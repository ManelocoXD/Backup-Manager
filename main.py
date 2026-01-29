#!/usr/bin/env python3
"""
SmartBackup Local - Edición Universal
Entry point for the application.
"""

import sys
import os

# Ensure the package is importable when running as script
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = os.path.dirname(sys.executable)
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

# Add to path if needed
if application_path not in sys.path:
    sys.path.insert(0, application_path)


def main():
    """Main entry point."""
    # Check for background mode
    background_mode = "--background" in sys.argv or "-b" in sys.argv
    
    # Import here to ensure path is set up
    from smartbackup.ui.main_window import MainWindow
    
    # Create and run application
    app = MainWindow(start_minimized=background_mode)
    app.mainloop()


if __name__ == "__main__":
    main()
