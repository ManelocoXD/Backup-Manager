"""
System tray functionality for SmartBackup.
Allows the application to run in background and execute scheduled backups.
"""

import threading
from typing import Optional, Callable, TYPE_CHECKING
from PIL import Image, ImageDraw

if TYPE_CHECKING:
    from .main_window import MainWindow

try:
    import pystray
    from pystray import MenuItem, Menu
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False


class SystemTray:
    """System tray icon for background operation."""
    
    def __init__(
        self,
        on_show_window: Callable,
        on_exit: Callable,
        lang: str = "es"
    ):
        self._on_show_window = on_show_window
        self._on_exit = on_exit
        self._lang = lang
        self._icon = None
        self._running = False
        
    def _create_icon_image(self) -> Image.Image:
        """Create a simple shield icon for the tray."""
        # Create a 64x64 image with a shield shape
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a blue shield shape
        shield_color = (59, 130, 246)  # Blue
        
        # Shield outline points
        points = [
            (size // 2, 4),  # Top center
            (size - 4, 12),  # Top right
            (size - 4, size // 2),  # Middle right
            (size // 2, size - 4),  # Bottom center
            (4, size // 2),  # Middle left
            (4, 12),  # Top left
        ]
        
        draw.polygon(points, fill=shield_color)
        
        # Draw checkmark
        check_color = (255, 255, 255)
        check_points = [
            (size // 4, size // 2),
            (size // 2 - 4, size // 2 + 12),
            (size - size // 4, size // 3),
        ]
        draw.line(check_points, fill=check_color, width=4)
        
        return image
    
    def _get_menu(self) -> 'Menu':
        """Create the tray context menu."""
        if self._lang == "es":
            show_text = "Abrir SmartBackup"
            exit_text = "Salir"
        else:
            show_text = "Open SmartBackup"
            exit_text = "Exit"
        
        return Menu(
            MenuItem(show_text, self._on_show_click, default=True),
            MenuItem(exit_text, self._on_exit_click)
        )
    
    def _on_show_click(self, icon, item):
        """Handle show window click."""
        self._on_show_window()
    
    def _on_exit_click(self, icon, item):
        """Handle exit click."""
        self.stop()
        self._on_exit()
    
    def start(self):
        """Start the system tray icon."""
        if not PYSTRAY_AVAILABLE:
            return
        
        if self._running:
            return
        
        self._running = True
        
        # Create icon
        self._icon = pystray.Icon(
            "SmartBackup",
            self._create_icon_image(),
            "SmartBackup - Running",
            self._get_menu()
        )
        
        # Run in background thread
        self._tray_thread = threading.Thread(target=self._icon.run, daemon=True)
        self._tray_thread.start()
    
    def stop(self):
        """Stop the system tray icon."""
        self._running = False
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
    
    def update_tooltip(self, text: str):
        """Update the tray icon tooltip."""
        if self._icon:
            self._icon.title = text


def is_tray_available() -> bool:
    """Check if system tray functionality is available."""
    return PYSTRAY_AVAILABLE
