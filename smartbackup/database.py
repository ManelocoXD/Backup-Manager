"""
SQLite database manager for SmartBackup.
Handles backup history, file hashes, and configuration persistence.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from .config import get_config


class Database:
    """SQLite database manager for backup operations."""
    
    def __init__(self):
        self._db_path = get_config().database_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database with required tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Backup sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_path TEXT NOT NULL,
                    dest_path TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    status TEXT DEFAULT 'running',
                    files_total INTEGER DEFAULT 0,
                    files_copied INTEGER DEFAULT 0,
                    files_skipped INTEGER DEFAULT 0,
                    bytes_copied INTEGER DEFAULT 0,
                    error_message TEXT,
                    backup_folder TEXT
                )
            """)
            
            # Check if backup_folder column exists (migration for existing DB)
            cursor.execute("PRAGMA table_info(backup_sessions)")
            columns = [info[1] for info in cursor.fetchall()]
            if "backup_folder" not in columns:
                cursor.execute("ALTER TABLE backup_sessions ADD COLUMN backup_folder TEXT")
            
            # File hashes table for deduplication
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_hashes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    relative_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    modified_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES backup_sessions(id)
                )
            """)
            
            # Create indexes for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_hashes_path 
                ON file_hashes(relative_path)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_hashes_session 
                ON file_hashes(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_source 
                ON backup_sessions(source_path)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_folder 
                ON backup_sessions(backup_folder)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # ==================== Backup Sessions ====================
    
    def create_session(self, source: str, dest: str, mode: str, backup_folder: str = None) -> int:
        """
        Create a new backup session.
        
        Returns:
            Session ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO backup_sessions 
                (source_path, dest_path, mode, started_at, status, backup_folder)
                VALUES (?, ?, ?, ?, 'running', ?)
            """, (source, dest, mode, datetime.now(), backup_folder))
            conn.commit()
            return cursor.lastrowid
    
    def update_session_progress(
        self, 
        session_id: int, 
        files_total: int = None,
        files_copied: int = None,
        files_skipped: int = None,
        bytes_copied: int = None
    ) -> None:
        """Update session progress counters."""
        updates = []
        values = []
        
        if files_total is not None:
            updates.append("files_total = ?")
            values.append(files_total)
        if files_copied is not None:
            updates.append("files_copied = ?")
            values.append(files_copied)
        if files_skipped is not None:
            updates.append("files_skipped = ?")
            values.append(files_skipped)
        if bytes_copied is not None:
            updates.append("bytes_copied = ?")
            values.append(bytes_copied)
        
        if not updates:
            return
        
        values.append(session_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE backup_sessions SET {', '.join(updates)} WHERE id = ?",
                values
            )
            conn.commit()
    
    def complete_session(
        self, 
        session_id: int, 
        status: str = "completed",
        error_message: str = None
    ) -> None:
        """Mark a session as completed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE backup_sessions 
                SET completed_at = ?, status = ?, error_message = ?
                WHERE id = ?
            """, (datetime.now(), status, error_message, session_id))
            conn.commit()
    
    def get_last_session(
        self, 
        source: str, 
        mode: str = None,
        status: str = "completed"
    ) -> Optional[Dict[str, Any]]:
        """
        Get the last backup session for a source path.
        
        Args:
            source: Source path to search for
            mode: Optional mode filter ('full', 'incremental', 'differential')
            status: Status filter (default: 'completed')
        
        Returns:
            Session dict or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if mode:
                cursor.execute("""
                    SELECT * FROM backup_sessions 
                    WHERE source_path = ? AND mode = ? AND status = ?
                    ORDER BY completed_at DESC LIMIT 1
                """, (source, mode, status))
            else:
                cursor.execute("""
                    SELECT * FROM backup_sessions 
                    WHERE source_path = ? AND status = ?
                    ORDER BY completed_at DESC LIMIT 1
                """, (source, status))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent backup sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM backup_sessions 
                ORDER BY started_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
            
    def get_session_by_folder(self, backup_folder: str) -> Optional[Dict[str, Any]]:
        """
        Find a session based on the backup folder name or path.
        """
        # Try finding by full path match first (if backup_folder column populated)
        folder_name = Path(backup_folder).name
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Exact match on backup_folder
            cursor.execute("SELECT * FROM backup_sessions WHERE backup_folder = ?", (folder_name,))
            row = cursor.fetchone()
            if row: return dict(row)
            
            # 2. Try match containing folder name (fallback)
            cursor.execute("SELECT * FROM backup_sessions WHERE backup_folder LIKE ?", (f"%{folder_name}%",))
            row = cursor.fetchone()
            if row: return dict(row)
            
            return None

    def get_sessions_history(self, source_path: str, before_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Get backup history for a source path, ordered by date descending.
        Useful for reconstructing restore chains.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM backup_sessions WHERE source_path = ? AND status = 'completed'"
            
            args = [source_path]
            if before_date:
                query += " AND started_at < ?"
                args.append(before_date)
            
            query += " ORDER BY started_at DESC"
            cursor.execute(query, tuple(args))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== File Hashes ====================
    
    def store_file_hash(
        self, 
        session_id: int, 
        relative_path: str, 
        file_hash: str,
        file_size: int,
        modified_at: datetime
    ) -> None:
        """Store a file hash for a backup session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO file_hashes 
                (session_id, relative_path, file_hash, file_size, modified_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, relative_path, file_hash, file_size, modified_at))
            conn.commit()
    
    def store_file_hashes_batch(
        self, 
        session_id: int, 
        files: List[Tuple[str, str, int, datetime]]
    ) -> None:
        """
        Store multiple file hashes efficiently.
        
        Args:
            session_id: The backup session ID
            files: List of (relative_path, file_hash, file_size, modified_at) tuples
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO file_hashes 
                (session_id, relative_path, file_hash, file_size, modified_at)
                VALUES (?, ?, ?, ?, ?)
            """, [(session_id, *f) for f in files])
            conn.commit()
    
    def get_file_hash(
        self, 
        session_id: int, 
        relative_path: str
    ) -> Optional[str]:
        """Get the stored hash for a file from a specific session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_hash FROM file_hashes 
                WHERE session_id = ? AND relative_path = ?
            """, (session_id, relative_path))
            row = cursor.fetchone()
            return row["file_hash"] if row else None
    
    def get_session_files(
        self, 
        session_id: int
    ) -> Dict[str, Tuple[str, int, datetime]]:
        """
        Get all file hashes from a session.
        
        Returns:
            Dict mapping relative_path to (hash, size, modified_at)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT relative_path, file_hash, file_size, modified_at 
                FROM file_hashes WHERE session_id = ?
            """, (session_id,))
            
            return {
                row["relative_path"]: (
                    row["file_hash"], 
                    row["file_size"], 
                    row["modified_at"]
                )
                for row in cursor.fetchall()
            }


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db
