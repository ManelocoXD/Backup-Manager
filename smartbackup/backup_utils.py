"""
Backup utilities for compression and encryption.
"""

import os
import zipfile
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
import hashlib
import base64

# Encryption imports
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


def is_crypto_available() -> bool:
    """Check if encryption is available."""
    return CRYPTO_AVAILABLE


def derive_key_from_password(password: str, salt: bytes = None) -> tuple:
    """
    Derive a Fernet key from a password using PBKDF2.
    
    Args:
        password: User-provided password
        salt: Optional salt (generated if not provided)
    
    Returns:
        (key, salt) tuple
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def compress_folder(
    source_folder: str,
    output_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    """
    Compress a folder to a ZIP file.
    
    Args:
        source_folder: Path to folder to compress
        output_path: Output ZIP file path
        progress_callback: Optional callback(current, total)
    
    Returns:
        True if successful
    """
    try:
        source = Path(source_folder)
        
        # Count files for progress
        all_files = list(source.rglob("*"))
        total = len(all_files)
        current = 0
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for item in all_files:
                if item.is_file():
                    arcname = item.relative_to(source)
                    zf.write(item, arcname)
                elif item.is_dir():
                    # Add empty directories
                    arcname = str(item.relative_to(source)) + "/"
                    zf.writestr(arcname, "")
                
                current += 1
                if progress_callback:
                    progress_callback(current, total)
        
        return True
    except Exception as e:
        print(f"Compression error: {e}")
        return False


def decompress_folder(
    zip_path: str,
    output_folder: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    """
    Decompress a ZIP file to a folder.
    
    Args:
        zip_path: Path to ZIP file
        output_folder: Output folder path
        progress_callback: Optional callback(current, total)
    
    Returns:
        True if successful
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            members = zf.namelist()
            total = len(members)
            
            for i, member in enumerate(members):
                zf.extract(member, output_folder)
                if progress_callback:
                    progress_callback(i + 1, total)
        
        return True
    except Exception as e:
        print(f"Decompression error: {e}")
        return False


def encrypt_file(
    input_path: str,
    output_path: str,
    password: str
) -> bool:
    """
    Encrypt a file using AES (Fernet).
    
    Args:
        input_path: Input file path
        output_path: Output encrypted file path
        password: Encryption password
    
    Returns:
        True if successful
    """
    if not CRYPTO_AVAILABLE:
        return False
    
    try:
        key, salt = derive_key_from_password(password)
        fernet = Fernet(key)
        
        with open(input_path, 'rb') as f:
            data = f.read()
        
        encrypted = fernet.encrypt(data)
        
        # Write salt + encrypted data
        with open(output_path, 'wb') as f:
            f.write(salt)  # 16 bytes
            f.write(encrypted)
        
        return True
    except Exception as e:
        print(f"Encryption error: {e}")
        return False


def decrypt_file(
    input_path: str,
    output_path: str,
    password: str
) -> bool:
    """
    Decrypt a file using AES (Fernet).
    
    Args:
        input_path: Input encrypted file path
        output_path: Output decrypted file path
        password: Decryption password
    
    Returns:
        True if successful
    """
    if not CRYPTO_AVAILABLE:
        return False
    
    try:
        with open(input_path, 'rb') as f:
            salt = f.read(16)
            encrypted = f.read()
        
        key, _ = derive_key_from_password(password, salt)
        fernet = Fernet(key)
        
        decrypted = fernet.decrypt(encrypted)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted)
        
        return True
    except Exception as e:
        print(f"Decryption error: {e}")
        return False


def compress_and_encrypt_backup(
    source_folder: str,
    output_path: str,
    password: Optional[str] = None,
    compress: bool = True,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> bool:
    """
    Compress and optionally encrypt a backup folder.
    
    Args:
        source_folder: Source backup folder
        output_path: Final output path (without extension, will add .zip or .enc)
        password: If provided, encrypts the backup
        compress: If True, compresses to ZIP
        progress_callback: callback(stage, current, total)
    
    Returns:
        True if successful
    """
    try:
        if compress:
            zip_path = output_path + ".zip"
            
            def zip_progress(cur, tot):
                if progress_callback:
                    progress_callback("compressing", cur, tot)
            
            if not compress_folder(source_folder, zip_path, zip_progress):
                return False
            
            if password:
                enc_path = output_path + ".zip.enc"
                
                if progress_callback:
                    progress_callback("encrypting", 0, 1)
                
                if not encrypt_file(zip_path, enc_path, password):
                    return False
                
                # Remove unencrypted zip
                os.remove(zip_path)
                
                if progress_callback:
                    progress_callback("encrypting", 1, 1)
            
            return True
        
        elif password:
            # Encrypt without compression - create temp zip first
            temp_zip = output_path + "_temp.zip"
            
            def zip_progress(cur, tot):
                if progress_callback:
                    progress_callback("compressing", cur, tot)
            
            if not compress_folder(source_folder, temp_zip, zip_progress):
                return False
            
            enc_path = output_path + ".enc"
            
            if progress_callback:
                progress_callback("encrypting", 0, 1)
            
            if not encrypt_file(temp_zip, enc_path, password):
                os.remove(temp_zip)
                return False
            
            os.remove(temp_zip)
            
            if progress_callback:
                progress_callback("encrypting", 1, 1)
            
            return True
        
        return True
        
    except Exception as e:
        print(f"Compress/encrypt error: {e}")
        return False
