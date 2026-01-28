"""
Help dialog for SmartBackup.
Provides tutorial and explanation of backup modes.
"""

import customtkinter as ctk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main_window import MainWindow

from ..locales import Localizer


class HelpDialog(ctk.CTkToplevel):
    """Modal dialog with help and tutorial content."""
    
    def __init__(self, parent: "MainWindow", localizer: Localizer):
        super().__init__(parent)
        
        self._ = localizer
        
        # Window configuration
        self.title(self._("help_title"))
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 500) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda e: self._on_close())
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Main container with padding
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        title = ctk.CTkLabel(
            container,
            text="🛡️ " + self._("help_title"),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(0, 10))
        
        # Intro text
        intro = ctk.CTkLabel(
            container,
            text=self._("help_intro"),
            font=ctk.CTkFont(size=14),
            wraplength=520
        )
        intro.pack(pady=(0, 20))
        
        # Scrollable content
        content_frame = ctk.CTkScrollableFrame(container, height=280)
        content_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Section title
        section_title = ctk.CTkLabel(
            content_frame,
            text=self._("help_modes_title"),
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w"
        )
        section_title.pack(fill="x", pady=(0, 15))
        
        # Backup mode cards
        self._create_mode_card(
            content_frame,
            icon="📦",
            title=self._("mode_full"),
            description=self._("mode_full_desc"),
            color="#3B82F6"
        )
        
        self._create_mode_card(
            content_frame,
            icon="⚡",
            title=self._("mode_incremental"),
            description=self._("mode_incremental_desc"),
            color="#10B981"
        )
        
        self._create_mode_card(
            content_frame,
            icon="🔄",
            title=self._("mode_differential"),
            description=self._("mode_differential_desc"),
            color="#8B5CF6"
        )
        
        # Tip box
        tip_frame = ctk.CTkFrame(content_frame, fg_color=("#FEF3C7", "#422006"))
        tip_frame.pack(fill="x", pady=(15, 0))
        
        tip_label = ctk.CTkLabel(
            tip_frame,
            text=self._("help_tip"),
            font=ctk.CTkFont(size=13),
            wraplength=480,
            text_color=("#92400E", "#FCD34D")
        )
        tip_label.pack(padx=15, pady=12)
        
        # Close button
        close_btn = ctk.CTkButton(
            container,
            text=self._("close"),
            command=self._on_close,
            width=120,
            height=40
        )
        close_btn.pack()
    
    def _create_mode_card(
        self, 
        parent, 
        icon: str, 
        title: str, 
        description: str,
        color: str
    ):
        """Create a backup mode explanation card."""
        card = ctk.CTkFrame(parent)
        card.pack(fill="x", pady=5)
        
        # Header with icon and title
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(12, 5))
        
        icon_label = ctk.CTkLabel(
            header,
            text=icon,
            font=ctk.CTkFont(size=20)
        )
        icon_label.pack(side="left")
        
        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=color
        )
        title_label.pack(side="left", padx=(10, 0))
        
        # Description
        desc_label = ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(size=13),
            wraplength=480,
            anchor="w",
            justify="left"
        )
        desc_label.pack(fill="x", padx=15, pady=(0, 12))
    
    def _on_close(self):
        """Handle dialog close."""
        self.grab_release()
        self.destroy()
