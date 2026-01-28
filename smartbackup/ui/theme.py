"""
Theme management for SmartBackup UI.
Handles system theme detection and custom styling.
"""

import sys
import customtkinter as ctk
from typing import Tuple


# Color palettes
COLORS = {
    "dark": {
        "primary": "#3B82F6",       # Blue
        "primary_hover": "#2563EB",
        "secondary": "#10B981",      # Green
        "secondary_hover": "#059669",
        "danger": "#EF4444",
        "danger_hover": "#DC2626",
        "warning": "#F59E0B",
        "background": "#1E1E2E",
        "surface": "#2D2D3F",
        "surface_light": "#3D3D4F",
        "text": "#FFFFFF",
        "text_secondary": "#A1A1AA",
        "border": "#4B5563",
        "success": "#22C55E",
    },
    "light": {
        "primary": "#2563EB",
        "primary_hover": "#1D4ED8",
        "secondary": "#059669",
        "secondary_hover": "#047857",
        "danger": "#DC2626",
        "danger_hover": "#B91C1C",
        "warning": "#D97706",
        "background": "#F8FAFC",
        "surface": "#FFFFFF",
        "surface_light": "#F1F5F9",
        "text": "#1E293B",
        "text_secondary": "#64748B",
        "border": "#CBD5E1",
        "success": "#16A34A",
    }
}

# Gradient-like accent colors for visual interest
ACCENT_GRADIENT = {
    "start": "#3B82F6",  # Blue
    "end": "#8B5CF6",    # Purple
}


def detect_system_theme() -> str:
    """
    Detect the system theme preference.
    
    Returns:
        'dark' or 'light'
    """
    try:
        if sys.platform == "win32":
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if value == 1 else "dark"
    except Exception:
        pass
    
    # Default to dark theme
    return "dark"


def apply_theme(theme: str = "system") -> str:
    """
    Apply a theme to CustomTkinter.
    
    Args:
        theme: 'dark', 'light', or 'system'
    
    Returns:
        The actual theme applied ('dark' or 'light')
    """
    if theme == "system":
        theme = detect_system_theme()
    
    ctk.set_appearance_mode(theme)
    ctk.set_default_color_theme("blue")
    
    return theme


def get_colors(theme: str = None) -> dict:
    """
    Get the color palette for a theme.
    
    Args:
        theme: 'dark' or 'light', or None to auto-detect
    
    Returns:
        Color dictionary
    """
    if theme is None:
        theme = detect_system_theme()
    return COLORS.get(theme, COLORS["dark"])


def format_bytes(bytes_count: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration into human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"
