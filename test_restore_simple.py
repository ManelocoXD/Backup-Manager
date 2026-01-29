#!/usr/bin/env python3
"""
Simple restore test to verify core functionality works.
Run this to see if restore logic is working at all.
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from smartbackup.backup_engine import BackupEngine, BackupMode
from smartbackup.backup_utils import decrypt_file, decompress_folder
import tempfile
import shutil

def test_restore():
    """Test restore from encrypted backup."""
    
    # Paths - CHANGE THESE to your actual backup file
    ENCRYPTED_FILE = input("Enter path to .zip.enc file: ").strip().strip('"')
    RESTORE_TO = input("Enter destination folder for restore: ").strip().strip('"')
    PASSWORD = input("Enter password: ").strip()
    
    if not os.path.exists(ENCRYPTED_FILE):
        print(f"❌ File not found: {ENCRYPTED_FILE}")
        return
    
    print(f"\n🔧 Starting restore test...")
    print(f"   Source: {ENCRYPTED_FILE}")
    print(f"   Destination: {RESTORE_TO}")
    print()
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Step 1: Decrypt
        print("1️⃣ Decrypting...")
        zip_path = os.path.join(temp_dir, "backup.zip")
        
        if not decrypt_file(ENCRYPTED_FILE, zip_path, PASSWORD):
            print("❌ DECRYPTION FAILED - Wrong password or corrupted file")
            return
        
        print(f"   ✅ Decrypted to {zip_path}")
        
        # Step 2: Decompress
        print("2️⃣ Decompressing...")
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir)
        
        if not decompress_folder(zip_path, extract_dir):
            print("❌ DECOMPRESSION FAILED")
            return
        
        print(f"   ✅ Decompressed to {extract_dir}")
        
        # Step 3: Restore
        print("3️⃣ Restoring files...")
        engine = BackupEngine()
        
        def progress_cb(p):
            print(f"   Progress: {p.progress_percent:.1f}% - {p.current_file}")
        
        result = engine.run_restore(extract_dir, RESTORE_TO, progress_cb)
        
        if result.success:
            print(f"\n✅ RESTORE SUCCESSFUL!")
            print(f"   Files restored: {result.files_restored}")
            print(f"   Bytes restored: {result.bytes_restored}")
        else:
            print(f"\n❌ RESTORE FAILED: {result.error_message}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

if __name__ == "__main__":
    test_restore()
    input("\nPress Enter to exit...")
