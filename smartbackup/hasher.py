"""
SHA-256 file hashing utilities for SmartBackup.
Used for detecting file changes and deduplication.
"""

import hashlib
from pathlib import Path
from typing import Optional, Callable


# Buffer size for reading large files (64KB)
BUFFER_SIZE = 65536


def compute_file_hash(file_path: Path, progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[str]:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        progress_callback: Optional callback(bytes_read, total_bytes) for progress reporting
    
    Returns:
        Hexadecimal hash string, or None if file cannot be read
    """
    try:
        file_size = file_path.stat().st_size
        bytes_read = 0
        
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break
                sha256_hash.update(data)
                bytes_read += len(data)
                
                if progress_callback:
                    progress_callback(bytes_read, file_size)
        
        return sha256_hash.hexdigest()
    
    except (IOError, OSError, PermissionError):
        return None


def compute_quick_hash(file_path: Path) -> Optional[str]:
    """
    Compute a quick hash using file metadata for fast comparison.
    Combines file size and modification time.
    
    This is NOT cryptographically secure but is fast for change detection.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Quick hash string, or None if file cannot be accessed
    """
    try:
        stat = file_path.stat()
        # Combine size and mtime for quick comparison
        quick_data = f"{stat.st_size}:{stat.st_mtime_ns}".encode()
        return hashlib.md5(quick_data).hexdigest()
    except (IOError, OSError, PermissionError):
        return None


def files_are_identical(file1: Path, file2: Path) -> bool:
    """
    Check if two files are identical by comparing their SHA-256 hashes.
    
    Args:
        file1: First file path
        file2: Second file path
    
    Returns:
        True if files have identical content, False otherwise
    """
    hash1 = compute_file_hash(file1)
    hash2 = compute_file_hash(file2)
    
    if hash1 is None or hash2 is None:
        return False
    
    return hash1 == hash2


def file_needs_update(source: Path, dest: Path) -> bool:
    """
    Check if a destination file needs to be updated based on the source.
    Uses quick hash for fast comparison.
    
    Args:
        source: Source file path
        dest: Destination file path
    
    Returns:
        True if dest doesn't exist or differs from source
    """
    if not dest.exists():
        return True
    
    source_quick = compute_quick_hash(source)
    dest_quick = compute_quick_hash(dest)
    
    if source_quick is None:
        return False  # Can't read source, skip
    
    if dest_quick is None:
        return True  # Can't read dest, assume needs update
    
    # Quick hashes differ, files are different
    return source_quick != dest_quick
