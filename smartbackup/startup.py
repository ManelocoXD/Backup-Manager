"""
Windows startup registration for SmartBackup.
Allows the application to start automatically with Windows.
"""

import sys
import os
from pathlib import Path

# Windows registry for startup
try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False


APP_NAME = "SmartBackup"
STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def is_startup_available() -> bool:
    """Check if startup registration is available."""
    return WINREG_AVAILABLE and sys.platform == "win32"


def get_app_path() -> str:
    """Get the path to the application executable or script."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return sys.executable
    else:
        # Running as script - use pythonw to avoid console window
        python_exe = sys.executable
        main_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py")
        return f'"{python_exe}" "{main_script}" --background'


def is_startup_enabled() -> bool:
    """Check if the application is set to start with Windows."""
    if not is_startup_available():
        return False
    
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            STARTUP_KEY,
            0,
            winreg.KEY_READ
        )
        try:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except WindowsError:
            winreg.CloseKey(key)
            return False
    except WindowsError:
        return False


def enable_startup() -> bool:
    """Enable starting the application with Windows."""
    if not is_startup_available():
        return False
    
    try:
        app_path = get_app_path()
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            STARTUP_KEY,
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(key)
        return True
    except WindowsError as e:
        print(f"Failed to enable startup: {e}")
        return False


def disable_startup() -> bool:
    """Disable starting the application with Windows."""
    if not is_startup_available():
        return False
    
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            STARTUP_KEY,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
        except WindowsError:
            pass  # Value doesn't exist
        winreg.CloseKey(key)
        return True
    except WindowsError as e:
        print(f"Failed to disable startup: {e}")
        return False


def toggle_startup(enabled: bool) -> bool:
    """Toggle startup registration."""
    if enabled:
        return enable_startup()
    else:
        return disable_startup()
