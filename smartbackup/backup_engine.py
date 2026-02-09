"""
Backup engine for SmartBackup.
Implements Full, Incremental, and Differential backup modes.
"""

import os
import shutil
import locale
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, List, Generator, Tuple
from dataclasses import dataclass
from enum import Enum
import threading

from .hasher import compute_file_hash, compute_quick_hash
from .database import get_database

# Day names in Spanish
DAYS_ES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
MONTHS_ES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


class BackupMode(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


@dataclass
class BackupProgress:
    """Progress information for backup operations."""
    current_file: str = ""
    files_total: int = 0
    files_processed: int = 0
    files_copied: int = 0
    files_skipped: int = 0
    bytes_copied: int = 0
    is_complete: bool = False
    is_cancelled: bool = False
    error: Optional[str] = None
    
    @property
    def progress_percent(self) -> float:
        if self.files_total == 0:
            return 0.0
        return (self.files_processed / self.files_total) * 100


@dataclass
class BackupResult:
    """Result of a backup operation."""
    success: bool
    session_id: int
    files_total: int
    files_copied: int
    files_skipped: int
    bytes_copied: int
    duration_seconds: float
    backup_folder: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class RestoreResult:
    """Result of a restore operation."""
    success: bool
    files_total: int
    files_restored: int
    files_skipped: int
    bytes_restored: int
    duration_seconds: float
    error_message: Optional[str] = None


# Type alias for progress callback
ProgressCallback = Callable[[BackupProgress], None]


class BackupEngine:
    """
    Backup engine supporting multiple backup modes.
    
    - Full: Copies all files
    - Incremental: Only files changed since last backup (any type)
    - Differential: All files changed since last full backup
    """
    
    def __init__(self):
        self._db = get_database()
        self._cancel_requested = False
        self._lock = threading.Lock()
    
    def cancel(self) -> None:
        """Request cancellation of the current backup."""
        with self._lock:
            self._cancel_requested = True
    
    def _is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        with self._lock:
            return self._cancel_requested
    
    def _reset_cancel(self) -> None:
        """Reset the cancellation flag."""
        with self._lock:
            self._cancel_requested = False
    
    def _get_all_files(self, source: Path) -> Generator[Path, None, None]:
        """Recursively get all files in source directory."""
        for item in source.rglob("*"):
            if item.is_file():
                yield item
    
    def _get_all_directories(self, source: Path) -> Generator[Path, None, None]:
        """Recursively get all directories in source directory."""
        for item in source.rglob("*"):
            if item.is_dir():
                yield item
    
    def _count_files(self, source: Path) -> int:
        """Count total files in source directory."""
        return sum(1 for _ in self._get_all_files(source))
    
    def _generate_backup_folder_name(self, mode: BackupMode) -> str:
        """Generate backup folder name with format: Type_DayOfWeek_Day_Month."""
        now = datetime.now()
        
        # Mode name
        mode_names = {
            BackupMode.FULL: "Completo",
            BackupMode.INCREMENTAL: "Incremental",
            BackupMode.DIFFERENTIAL: "Diferencial"
        }
        mode_name = mode_names.get(mode, mode.value)
        
        # Day of week (0=Monday)
        day_of_week = DAYS_ES[now.weekday()]
        
        # Day number
        day_num = now.day
        
        # Month name
        month_name = MONTHS_ES[now.month]
        
        # Time for uniqueness
        time_str = now.strftime("%H%M")
        
        return f"{mode_name}_{day_of_week}_{day_num}_{month_name}_{time_str}"
    
    def _should_copy_file(
        self, 
        source_file: Path, 
        relative_path: str,
        mode: BackupMode,
        reference_session: Optional[dict],
        reference_files: Optional[dict]
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if a file should be copied based on backup mode.
        
        Returns:
            (should_copy, current_hash) tuple
        """
        # Full backup: always copy, but still need hash
        if mode == BackupMode.FULL:
            file_hash = compute_file_hash(source_file)
            return True, file_hash
        
        # For incremental/differential, we need a reference session
        if not reference_session or not reference_files:
            # No reference, treat as full backup
            file_hash = compute_file_hash(source_file)
            return True, file_hash
        
        # Check if file exists in reference
        if relative_path not in reference_files:
            # New file -> Copy
            file_hash = compute_file_hash(source_file)
            return True, file_hash
        
        # --- QUICK CHECK (Performance Optimization) ---
        # Before reading the whole file for SHA-256, check metadata.
        # If size and mtime differ, we know it changed.
        # If they match, we assume it's unchanged (standard backup practice).
        
        ref_hash, ref_size, ref_mtime = reference_files[relative_path]
        
        try:
            stat = source_file.stat()
            current_size = stat.st_size
            current_mtime = datetime.fromtimestamp(stat.st_mtime)
            
            # Check size first (fastest)
            if current_size != ref_size:
                # Size changed -> Content changed -> Copy
                current_hash = compute_file_hash(source_file)
                return True, current_hash
            
            # Check mtime (with 1s tolerance for FS differences)
            # Note: ref_mtime comes from DB as datetime or string depending on sqlite adapter
            if isinstance(ref_mtime, str):
                try:
                    ref_mtime = datetime.fromisoformat(ref_mtime)
                except ValueError:
                    pass # Ignore parsing error, fall back to hash check
            
            if isinstance(ref_mtime, datetime):
                time_diff = abs((current_mtime - ref_mtime).total_seconds())
                if time_diff < 1.0:
                    # Size matches, mtime matches -> Assume unchanged
                    # Return False (don't copy) and REUSE reference hash (avoid I/O)
                    return False, ref_hash
        except Exception:
            # If metadata check fails, fall back to safe hash comparison
            pass
            
        # --- FALLBACK / CONFIRMATION ---
        # If we reach here, metadata didn't definitively say "unchanged" 
        # (or we distrust it), OR it said "changed" but we want to be sure? 
        # Actually, if size changed, we returned True.
        # If mtime changed (or parsed wrong), we come here.
        # So we perform the expensive hash check now.
        
        current_hash = compute_file_hash(source_file)
        if current_hash is None:
            return False, None  # Can't read file, skip
        
        if current_hash != ref_hash:
            return True, current_hash  # Content changed
        
        return False, current_hash  # Content identical (even if mtime changed)
    
    
    def run_backup(
        self,
        source: str,
        destination: str,
        mode: BackupMode,
        progress_callback: Optional[ProgressCallback] = None
    ) -> BackupResult:
        """
        Execute a backup operation.
        
        Args:
            source: Source directory path
            destination: Destination directory path
            mode: Backup mode (full, incremental, differential)
            progress_callback: Optional callback for progress updates
        
        Returns:
            BackupResult with operation details
        """
        from .logger import get_logger
        logger = get_logger()
        
        self._reset_cancel()
        start_time = datetime.now()
        
        source_path = Path(source)
        dest_path = Path(destination)
        
        logger.info(f"Starting backup: mode={mode.value}, source={source}, dest={destination}")
        
        # Initialize progress
        progress = BackupProgress()
        
        def update_progress():
            if progress_callback:
                progress_callback(progress)
        
        # Validate paths
        if not source_path.exists():
            msg = "Source folder does not exist"
            logger.error(msg)
            return BackupResult(
                success=False,
                session_id=-1,
                files_total=0,
                files_copied=0,
                files_skipped=0,
                bytes_copied=0,
                duration_seconds=0,
                error_message=msg
            )
        
        # --- ROBUSTNESS: Determine Effective Mode ---
        # If Incremental/Differential requested, check if we have a valid reference.
        # If not, FORCE FULL backup to ensure chain integrity.
        
        effective_mode = mode
        reference_session = None
        reference_files = None
        forced_full_reason = None
        
        if mode in (BackupMode.INCREMENTAL, BackupMode.DIFFERENTIAL):
            # Check DB for reference
            if mode == BackupMode.INCREMENTAL:
                reference_session = self._db.get_last_session(source)
            else: # Differential
                reference_session = self._db.get_last_session(source, mode="full")
            
            # Validation Logic
            is_valid_reference = False
            
            if reference_session:
                # DB record exists. Now check physical existence.
                ref_folder_name = reference_session.get('backup_folder')
                
                # We expect the backup to be in the same destination root
                # Note: This assumes user hasn't moved backups to a new drive entirely.
                # If 'dest_path' in DB matches current 'destination', we look there.
                # If they differ, we might look in the old path? 
                # For robustness, we check the CURRENT destination for the folder.
                
                # Heuristic: We look for the reference folder in the *current* destination parent.
                # If not found there, we assume it's missing (even if it exists on another drive).
                # Why? Because we need it here for the chain logic to hold easily? 
                # Actually, for Differential/Incremental *creation*, we mainly need DB hashes.
                # BUT for *Restore*, we need the files.
                # If we make an incremental based on a missing folder, restoration will FAIL.
                # So we MUST ensure the physical files are reachable.
                
                if ref_folder_name:
                    ref_path = dest_path / ref_folder_name
                    if ref_path.exists():
                        is_valid_reference = True
                    else:
                        forced_full_reason = f"Reference backup folder missing: {ref_folder_name}"
                else:
                    # Legacy session without folder name
                    # We can't verify execution, safer to force full
                    forced_full_reason = "Legacy reference session incompatible"
            else:
                forced_full_reason = "No previous backup found"
            
            if not is_valid_reference:
                logger.warning(f"{forced_full_reason}. Forcing FULL backup.")
                effective_mode = BackupMode.FULL
                reference_session = None # Clear it so we don't try to use it
        
        # Create backup folder with descriptive name
        # Use effective_mode for naming to avoid confusion (e.g. don't name it "Incremental" if it's actually Full)
        backup_folder_name = self._generate_backup_folder_name(effective_mode)
        backup_path = dest_path / backup_folder_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create backup session
        # IMPORTANT: Store as effective_mode (FULL) so it acts as an anchor for future backups
        session_id = self._db.create_session(source, destination, effective_mode.value, backup_folder_name)
        
        logger.info(f"Session {session_id} created. Mode: {effective_mode.value}. Folder: {backup_folder_name}")
        
        try:
            # Count files
            progress.files_total = self._count_files(source_path)
            self._db.update_session_progress(session_id, files_total=progress.files_total)
            update_progress()
            
            # Re-fetch reference files ONLY if we are still Incremental/Differential
            if effective_mode in (BackupMode.INCREMENTAL, BackupMode.DIFFERENTIAL) and reference_session:
                logger.info(f"Using reference session {reference_session['id']} for {effective_mode.value} backup")
                reference_files = self._db.get_session_files(reference_session["id"])
            else:
                reference_files = {} # Full backup or forced full
            
            # Copy empty directories for full backup
            if effective_mode == BackupMode.FULL:
                for source_dir in self._get_all_directories(source_path):
                    relative_dir = source_dir.relative_to(source_path)
                    dest_dir = backup_path / relative_dir
                    dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Process files
            file_hashes_batch: List[Tuple[str, str, int, datetime]] = []
            
            for source_file in self._get_all_files(source_path):
                # Check for cancellation
                if self._is_cancelled():
                    progress.is_cancelled = True
                    self._db.complete_session(session_id, status="cancelled")
                    update_progress()
                    logger.info("Backup cancelled by user")
                    
                    duration = (datetime.now() - start_time).total_seconds()
                    return BackupResult(
                        success=False,
                        session_id=session_id,
                        files_total=progress.files_total,
                        files_copied=progress.files_copied,
                        files_skipped=progress.files_skipped,
                        bytes_copied=progress.bytes_copied,
                        duration_seconds=duration,
                        error_message="Backup cancelled by user"
                    )
                
                # Calculate relative path
                relative_path = str(source_file.relative_to(source_path))
                progress.current_file = relative_path
                update_progress()
                
                # Determine if file should be copied
                should_copy, file_hash = self._should_copy_file(
                    source_file, 
                    relative_path, 
                    effective_mode, 
                    reference_session, 
                    reference_files
                )
                
                if should_copy and file_hash:
                    # Copy file
                    dest_file = backup_path / relative_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        shutil.copy2(source_file, dest_file)
                        file_size = source_file.stat().st_size
                        progress.files_copied += 1
                        progress.bytes_copied += file_size
                        
                        # Store hash for future reference
                        file_hashes_batch.append((
                            relative_path,
                            file_hash,
                            file_size,
                            datetime.fromtimestamp(source_file.stat().st_mtime)
                        ))
                        
                    except (IOError, OSError, PermissionError) as e:
                        # Log error but continue
                        pass
                else:
                    progress.files_skipped += 1
                    
                    # Still store hash for skipped files (they're unchanged)
                    if file_hash:
                        file_size = source_file.stat().st_size
                        file_hashes_batch.append((
                            relative_path,
                            file_hash,
                            file_size,
                            datetime.fromtimestamp(source_file.stat().st_mtime)
                        ))
                
                progress.files_processed += 1
                
                # Update database periodically
                if progress.files_processed % 100 == 0:
                    self._db.update_session_progress(
                        session_id,
                        files_copied=progress.files_copied,
                        files_skipped=progress.files_skipped,
                        bytes_copied=progress.bytes_copied
                    )
                    
                    # Batch insert hashes
                    if file_hashes_batch:
                        self._db.store_file_hashes_batch(session_id, file_hashes_batch)
                        file_hashes_batch.clear()
                
                update_progress()
            
            # Final batch insert
            if file_hashes_batch:
                self._db.store_file_hashes_batch(session_id, file_hashes_batch)
            
            # Mark session complete
            self._db.update_session_progress(
                session_id,
                files_copied=progress.files_copied,
                files_skipped=progress.files_skipped,
                bytes_copied=progress.bytes_copied
            )
            self._db.complete_session(session_id, status="completed")
            
            progress.is_complete = True
            update_progress()
            
            duration = (datetime.now() - start_time).total_seconds()
            return BackupResult(
                success=True,
                session_id=session_id,
                files_total=progress.files_total,
                files_copied=progress.files_copied,
                files_skipped=progress.files_skipped,
                bytes_copied=progress.bytes_copied,
                duration_seconds=duration,
                backup_folder=str(backup_path)
            )
            
        except Exception as e:
            # Handle unexpected errors
            error_msg = str(e)
            self._db.complete_session(session_id, status="error", error_message=error_msg)
            
            progress.error = error_msg
            update_progress()
            
            duration = (datetime.now() - start_time).total_seconds()
            return BackupResult(
                success=False,
                session_id=session_id,
                files_total=progress.files_total,
                files_copied=progress.files_copied,
                files_skipped=progress.files_skipped,
                bytes_copied=progress.bytes_copied,
                duration_seconds=duration,
                error_message=error_msg
            )
    
    def has_full_backup(self, source: str) -> bool:
        """Check if a full backup exists for the given source."""
        session = self._db.get_last_session(source, mode="full")
        return session is not None
    
    def has_any_backup(self, source: str) -> bool:
        """Check if any backup exists for the given source."""
        session = self._db.get_last_session(source)
        return session is not None
    
    def run_restore(
        self,
        backup_folder: str,
        destination: str,
        progress_callback: Optional[ProgressCallback] = None
    ) -> RestoreResult:
        """
        Restore files from a backup folder to a destination.
        
        Uses 'Smart Restore' to reconstruct files from the backup chain if possible.
        Falls back to 'Legacy Restore' (simple copy) if session info is missing.
        """
        from .logger import get_logger
        logger = get_logger()
        
        self._reset_cancel()
        start_time = datetime.now()
        
        backup_path = Path(backup_folder)
        dest_path = Path(destination)
        
        logger.info(f"Starting restore: source={backup_folder}, dest={destination}")
        
        # Initialize progress
        progress = BackupProgress()
        
        def update_progress():
            if progress_callback:
                progress_callback(progress)
        
        # Validate backup folder
        if not backup_path.exists():
            msg = "Backup folder does not exist"
            logger.error(msg)
            return RestoreResult(False, 0, 0, 0, 0, 0, msg)
        
        # Create destination if needed
        dest_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # --- SMART RESTORE LOGIC ---
            # 1. Identify Session
            session = self._db.get_session_by_folder(backup_folder)
            
            if session:
                logger.info(f"Smart Restore identified session {session.get('id')}")
                # 2. Get File Manifest
                files_to_restore = self._db.get_session_files(session['id'])
                progress.files_total = len(files_to_restore)
                update_progress()
                
                # 3. Build Backup Chain (for finding file content)
                source_path = session['source_path']
                started_at = session['started_at']
                if isinstance(started_at, str):
                    try:
                        started_at = datetime.fromisoformat(started_at)
                    except ValueError:
                        pass # Keep as string or handle error
                
                # Get history: current session + previous sessions
                history = self._db.get_sessions_history(source_path, before_date=started_at)
                
                # Chain: [Current, Prev1, Prev2, ... Full]
                # Note: 'session' dict includes backup_folder name/path info
                chain = [session] + history
                logger.info(f"Backup chain length: {len(chain)}")
                
                # Pre-calculate backup roots for the chain
                # Need to handle case where dest_path in DB might differ from current location if user moved backups.
                # Heuristic: Require backup folders to be siblings of the selected 'backup_folder'.
                # i.e., root_backup_dir = backup_path.parent
                root_backup_dir = backup_path.parent
                
                files_restored = 0
                files_skipped = 0
                bytes_restored = 0
                
                for rel_path, (f_hash, f_size, f_mtime) in files_to_restore.items():
                    if self._is_cancelled():
                        break
                        
                    progress.current_file = rel_path
                    update_progress()
                    
                    found = False
                    dest_file = dest_path / rel_path
                    
                    # Search logic:
                    # 1. Check current session folder (most likely)
                    # 2. Check previous sessions in order
                    
                    for sess in chain:
                        sess_folder_name = sess.get('backup_folder')
                        if not sess_folder_name:
                             # Fallback: try to guess or skip
                             # If we can't find the folder name, we can't find the file.
                             continue
                             
                        candidate_source = root_backup_dir / sess_folder_name / rel_path
                        
                        if candidate_source.exists():
                            # Found it!
                            try:
                                dest_file.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(candidate_source, dest_file)
                                files_restored += 1
                                bytes_restored += candidate_source.stat().st_size
                                found = True
                            except (IOError, OSError, PermissionError) as e:
                                logger.warning(f"Failed to copy {candidate_source}: {e}")
                                files_skipped += 1
                                found = True # Found but failed to copy
                            break
                    
                    if not found:
                        # File is in manifest but content missing from all chain folders.
                        # This implies corruption or missing backup folder.
                        msg = f"Error: Content for {rel_path} not found in backup chain."
                        print(msg)
                        logger.error(msg)
                        files_skipped += 1
                    
                    progress.files_processed += 1
                    progress.files_copied = files_restored
                    progress.files_skipped = files_skipped
                    progress.bytes_copied = bytes_restored
                    update_progress()
                    
                duration = (datetime.now() - start_time).total_seconds()
                
                if self._is_cancelled():
                     logger.info("Restore cancelled by user")
                     return RestoreResult(False, progress.files_total, files_restored, files_skipped, bytes_restored, duration, "Restore cancelled by user")

                logger.info(f"Restore completed successfully. Restored: {files_restored}, Skipped: {files_skipped}")
                return RestoreResult(True, progress.files_total, files_restored, files_skipped, bytes_restored, duration)

            else:
                # --- LEGACY RESTORE (Fallback) ---
                # No DB session found (old backup). Copy exactly what's in the folder.
                logger.info("No session found in DB. Falling back to Legacy Restore.")
                return self._legacy_restore(backup_path, dest_path, progress, update_progress, start_time)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.exception("Restore failed with exception")
            duration = (datetime.now() - start_time).total_seconds()
            return RestoreResult(False, progress.files_total, 0, 0, 0, duration, str(e))

    def _legacy_restore(self, backup_path, dest_path, progress, update_callback, start_time):
        """Legacy restore logic: simple copy of folder contents."""
        try:
            progress.files_total = self._count_files(backup_path)
            update_callback()
            
            files_restored = 0
            files_skipped = 0
            bytes_restored = 0
            
            # Copy all directories
            for source_dir in self._get_all_directories(backup_path):
                relative_dir = source_dir.relative_to(backup_path)
                dest_dir = dest_path / relative_dir
                dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all files
            for backup_file in self._get_all_files(backup_path):
                if self._is_cancelled():
                     duration = (datetime.now() - start_time).total_seconds()
                     return RestoreResult(False, progress.files_total, files_restored, files_skipped, bytes_restored, duration, "Restore cancelled by user")
                
                relative_path = backup_file.relative_to(backup_path)
                dest_file = dest_path / relative_path
                
                progress.current_file = str(relative_path)
                update_callback()
                
                try:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, dest_file)
                    file_size = backup_file.stat().st_size
                    files_restored += 1
                    bytes_restored += file_size
                except (IOError, OSError, PermissionError):
                    files_skipped += 1
                
                progress.files_processed += 1
                progress.files_copied = files_restored
                progress.files_skipped = files_skipped
                progress.bytes_copied = bytes_restored
                update_callback()
            
            duration = (datetime.now() - start_time).total_seconds()
            return RestoreResult(True, progress.files_total, files_restored, files_skipped, bytes_restored, duration)
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return RestoreResult(False, progress.files_total, 0, 0, 0, duration, str(e))


# Global engine instance
_engine: Optional[BackupEngine] = None


def get_backup_engine() -> BackupEngine:
    """Get the global backup engine instance."""
    global _engine
    if _engine is None:
        _engine = BackupEngine()
    return _engine
