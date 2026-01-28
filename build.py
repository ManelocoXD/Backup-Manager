#!/usr/bin/env python3
"""
Build script for SmartBackup Local.
Automates creation of distributable executables.
"""

import subprocess
import sys
import os
from pathlib import Path


def build_windows():
    """Build Windows executable using PyInstaller."""
    print("🔨 Building SmartBackup for Windows...")
    print()
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Run PyInstaller with spec file
    result = subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "smartbackup.spec"
    ])
    
    if result.returncode == 0:
        print()
        print("✅ Build successful!")
        print(f"📦 Executable: {project_root / 'dist' / 'SmartBackup.exe'}")
    else:
        print()
        print("❌ Build failed!")
        sys.exit(1)


def build_linux_appimage():
    """Instructions for building Linux AppImage."""
    print("🐧 Building Linux AppImage...")
    print()
    print("To create an AppImage on Linux:")
    print()
    print("1. Install dependencies:")
    print("   sudo apt install python3-pip python3-venv")
    print()
    print("2. Create virtual environment:")
    print("   python3 -m venv venv")
    print("   source venv/bin/activate")
    print("   pip install -r requirements.txt pyinstaller")
    print()
    print("3. Build with PyInstaller:")
    print("   pyinstaller --clean --noconfirm smartbackup.spec")
    print()
    print("4. Create AppImage using linuxdeploy or appimagetool:")
    print("   wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage")
    print("   chmod +x linuxdeploy-x86_64.AppImage")
    print("   ./linuxdeploy-x86_64.AppImage --appdir AppDir --executable dist/SmartBackup --output appimage")
    print()


def main():
    """Main build script entry point."""
    print("=" * 50)
    print("  SmartBackup Local - Build Script")
    print("=" * 50)
    print()
    
    if sys.platform == "win32":
        build_windows()
    elif sys.platform == "linux":
        build_linux_appimage()
    else:
        print(f"⚠️ Platform '{sys.platform}' not fully supported.")
        print("   Attempting Windows-style build...")
        build_windows()


if __name__ == "__main__":
    main()
