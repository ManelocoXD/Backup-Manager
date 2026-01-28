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
        # Full backup: always copy
        if mode == BackupMode.FULL:
            file_hash = compute_file_hash(source_file)
            return True, file_hash
        
        # For incremental/differential, we need a reference session
        if not reference_session or not reference_files:
            # No reference, treat as full backup
            file_hash = compute_file_hash(source_file)
            return True, file_hash
        
        # Compute current file hash
        current_hash = compute_file_hash(source_file)
        if current_hash is None:
            return False, None  # Can't read file, skip
        
        # Check if file exists in reference
        if relative_path not in reference_files:
            return True, current_hash  # New file
        
        # Compare hashes
        ref_hash, ref_size, ref_mtime = reference_files[relative_path]
        if current_hash != ref_hash:
            return True, current_hash  # File changed
        
        return False, current_hash  # File unchanged
    
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
        self._reset_cancel()
        start_time = datetime.now()
        
        source_path = Path(source)
        dest_path = Path(destination)
        
        # Initialize progress
        progress = BackupProgress()
        
        def update_progress():
            if progress_callback:
                progress_callback(progress)
        
        # Validate paths
        if not source_path.exists():
            return BackupResult(
                success=False,
                session_id=-1,
                files_total=0,
                files_copied=0,
                files_skipped=0,
                bytes_copied=0,
                duration_seconds=0,
                error_message="Source folder does not exist"
            )
        
        # Create backup folder with descriptive name
        backup_folder_name = self._generate_backup_folder_name(mode)
        backup_path = dest_path / backup_folder_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create backup session
        session_id = self._db.create_session(source, destination, mode.value)
        
        try:
            # Count files
            progress.files_total = self._count_files(source_path)
            self._db.update_session_progress(session_id, files_total=progress.files_total)
            update_progress()
            
            # Get reference session for incremental/differential
            reference_session = None
            reference_files = None
            
            if mode == BackupMode.INCREMENTAL:
                # Reference: last completed backup of any type
                reference_session = self._db.get_last_session(source)
            elif mode == BackupMode.DIFFERENTIAL:
                # Reference: last completed FULL backup
                reference_session = self._db.get_last_session(source, mode="full")
            
            if reference_session:
                reference_files = self._db.get_session_files(reference_session["id"])
            
            # Check if incremental/differential can proceed
            if mode in (BackupMode.INCREMENTAL, BackupMode.DIFFERENTIAL):
                required_mode = "full" if mode == BackupMode.DIFFERENTIAL else None
                if not reference_session:
                    # No reference backup exists, suggest full backup
                    error_msg = "no_full_backup" if mode == BackupMode.DIFFERENTIAL else "no_previous_backup"
                    # For now, we'll proceed as full backup
                    reference_files = {}
            
            # Copy empty directories for full backup
            if mode == BackupMode.FULL:
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
                    mode, 
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
        
        Args:
            backup_folder: Path to the backup folder to restore from
            destination: Destination directory path
            progress_callback: Optional callback for progress updates
        
        Returns:
            RestoreResult with operation details
        """
        self._reset_cancel()
        start_time = datetime.now()
        
        backup_path = Path(backup_folder)
        dest_path = Path(destination)
        
        # Initialize progress
        progress = BackupProgress()
        
        def update_progress():
            if progress_callback:
                progress_callback(progress)
        
        # Validate backup folder
        if not backup_path.exists():
            return RestoreResult(
                success=False,
                files_total=0,
                files_restored=0,
                files_skipped=0,
                bytes_restored=0,
                duration_seconds=0,
                error_message="Backup folder does not exist"
            )
        
        # Create destination if needed
        dest_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Count files in backup
            progress.files_total = self._count_files(backup_path)
            update_progress()
            
            # First, copy all directories (including empty ones)
            for source_dir in self._get_all_directories(backup_path):
                relative_dir = source_dir.relative_to(backup_path)
                dest_dir = dest_path / relative_dir
                dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all files
            files_restored = 0
            files_skipped = 0
            bytes_restored = 0
            
            for backup_file in self._get_all_files(backup_path):
                # Check for cancellation
                if self._is_cancelled():
                    duration = (datetime.now() - start_time).total_seconds()
                    return RestoreResult(
                        success=False,
                        files_total=progress.files_total,
                        files_restored=files_restored,
                        files_skipped=files_skipped,
                        bytes_restored=bytes_restored,
                        duration_seconds=duration,
                        error_message="Restore cancelled by user"
                    )
                
                relative_path = backup_file.relative_to(backup_path)
                dest_file = dest_path / relative_path
                
                progress.current_file = str(relative_path)
                update_progress()
                
                try:
                    # Create parent directories
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
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
                update_progress()
            
            duration = (datetime.now() - start_time).total_seconds()
            return RestoreResult(
                success=True,
                files_total=progress.files_total,
                files_restored=files_restored,
                files_skipped=files_skipped,
                bytes_restored=bytes_restored,
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return RestoreResult(
                success=False,
                files_total=progress.files_total,
                files_restored=0,
                files_skipped=0,
                bytes_restored=0,
                duration_seconds=duration,
                error_message=str(e)
            )


# Global engine instance
_engine: Optional[BackupEngine] = None


def get_backup_engine() -> BackupEngine:
    """Get the global backup engine instance."""
    global _engine
    if _engine is None:
        _engine = BackupEngine()
    return _engine
