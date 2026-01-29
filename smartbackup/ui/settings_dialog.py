"""
Settings dialog for SmartBackup.
Allows users to configure startup, compression, and encryption options.
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .main_window import MainWindow

from ..locales import Localizer
from ..config import get_config
from ..startup import is_startup_available, is_startup_enabled, toggle_startup
from ..backup_utils import is_crypto_available
from .theme import get_colors


class SettingsDialog(ctk.CTkToplevel):
    """Dialog for application settings."""
    
    def __init__(self, parent: "MainWindow", localizer: Localizer):
        super().__init__(parent)
        
        self._ = localizer
        self._colors = get_colors()
        self._config = get_config()
        self._parent = parent
        
        # Window configuration
        self.title(self._("settings"))
        self.geometry("500x550")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 550) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda e: self._on_close())
    
    def _create_card(self, parent, title: str) -> ctk.CTkFrame:
        """Create a styled card container."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=self._colors["surface"]
        )
        card.pack(fill="x", pady=(0, 15))
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        title_label.pack(fill="x", padx=15, pady=(12, 8))
        
        return card
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Main container
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # === HEADER ===
        header = ctk.CTkFrame(container, fg_color=self._colors["primary"], corner_radius=12)
        header.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(
            header,
            text="⚙️ " + self._("settings"),
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FFFFFF"
        )
        title.pack(pady=15)
        
        # === STARTUP SECTION ===
        startup_card = self._create_card(container, "🚀 " + self._("startup_settings"))
        
        self._startup_var = ctk.BooleanVar(value=is_startup_enabled())
        startup_check = ctk.CTkCheckBox(
            startup_card,
            text=self._("start_with_windows"),
            variable=self._startup_var,
            font=ctk.CTkFont(size=13),
            checkbox_width=24,
            checkbox_height=24,
            state="normal" if is_startup_available() else "disabled"
        )
        startup_check.pack(fill="x", padx=15, pady=(0, 5))
        
        startup_desc = ctk.CTkLabel(
            startup_card,
            text=self._("startup_desc"),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        startup_desc.pack(fill="x", padx=15, pady=(0, 12))
        
        # === COMPRESSION SECTION ===
        compress_card = self._create_card(container, "📦 " + self._("compression_settings"))
        
        self._compress_var = ctk.BooleanVar(value=self._config.enable_compression)
        compress_check = ctk.CTkCheckBox(
            compress_card,
            text=self._("enable_compression"),
            variable=self._compress_var,
            font=ctk.CTkFont(size=13),
            checkbox_width=24,
            checkbox_height=24
        )
        compress_check.pack(fill="x", padx=15, pady=(0, 5))
        
        compress_desc = ctk.CTkLabel(
            compress_card,
            text=self._("compression_desc"),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        compress_desc.pack(fill="x", padx=15, pady=(0, 12))
        
        # === ENCRYPTION SECTION ===
        encrypt_card = self._create_card(container, "🔐 " + self._("encryption_settings"))
        
        self._encrypt_var = ctk.BooleanVar(value=self._config.enable_encryption)
        encrypt_check = ctk.CTkCheckBox(
            encrypt_card,
            text=self._("enable_encryption"),
            variable=self._encrypt_var,
            font=ctk.CTkFont(size=13),
            checkbox_width=24,
            checkbox_height=24,
            command=self._on_encryption_toggle,
            state="normal" if is_crypto_available() else "disabled"
        )
        encrypt_check.pack(fill="x", padx=15, pady=(0, 5))
        
        encrypt_desc = ctk.CTkLabel(
            encrypt_card,
            text=self._("encryption_desc"),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        encrypt_desc.pack(fill="x", padx=15, pady=(0, 10))
        
        # Password fields
        self._password_frame = ctk.CTkFrame(encrypt_card, fg_color="transparent")
        self._password_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        pwd_label = ctk.CTkLabel(
            self._password_frame,
            text=self._("encryption_password") + ":",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        pwd_label.pack(fill="x", pady=(0, 5))
        
        self._password_entry = ctk.CTkEntry(
            self._password_frame,
            height=40,
            corner_radius=8,
            show="•",
            placeholder_text=self._("enter_password")
        )
        self._password_entry.pack(fill="x", pady=(0, 8))
        
        # Load saved password hint (not actual password)
        if self._config.encryption_password:
            self._password_entry.insert(0, self._config.encryption_password)
        
        confirm_label = ctk.CTkLabel(
            self._password_frame,
            text=self._("confirm_password") + ":",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        confirm_label.pack(fill="x", pady=(0, 5))
        
        self._confirm_entry = ctk.CTkEntry(
            self._password_frame,
            height=40,
            corner_radius=8,
            show="•",
            placeholder_text=self._("confirm_password")
        )
        self._confirm_entry.pack(fill="x")
        
        if self._config.encryption_password:
            self._confirm_entry.insert(0, self._config.encryption_password)
        
        # Show/hide password frame based on encryption toggle
        self._update_password_visibility()
        
        # === BUTTONS ===
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 " + self._("save"),
            command=self._save_settings,
            height=45,
            corner_radius=10,
            fg_color=self._colors["primary"],
            hover_color=self._colors["primary_hover"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        save_btn.pack(side="right", padx=(10, 0))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text=self._("cancel"),
            command=self._on_close,
            height=45,
            corner_radius=10,
            fg_color=self._colors["surface"],
            hover_color=self._colors["secondary_hover"],
            font=ctk.CTkFont(size=14)
        )
        cancel_btn.pack(side="right")
    
    def _on_encryption_toggle(self):
        """Handle encryption checkbox toggle."""
        self._update_password_visibility()
    
    def _update_password_visibility(self):
        """Show/hide password fields based on encryption setting."""
        if self._encrypt_var.get():
            self._password_frame.pack(fill="x", padx=15, pady=(0, 12))
        else:
            self._password_frame.pack_forget()
    
    def _save_settings(self):
        """Save settings."""
        # Validate encryption password
        if self._encrypt_var.get():
            pwd = self._password_entry.get()
            confirm = self._confirm_entry.get()
            
            if not pwd:
                messagebox.showerror(
                    self._("app_title"),
                    self._("password_required")
                )
                return
            
            if pwd != confirm:
                messagebox.showerror(
                    self._("app_title"),
                    self._("passwords_not_match")
                )
                return
            
            if len(pwd) < 8:
                messagebox.showerror(
                    self._("app_title"),
                    self._("password_too_short")
                )
                return
        
        # Save startup setting
        if is_startup_available():
            toggle_startup(self._startup_var.get())
        
        # Save config
        self._config.enable_compression = self._compress_var.get()
        self._config.enable_encryption = self._encrypt_var.get()
        
        if self._encrypt_var.get():
            self._config.encryption_password = self._password_entry.get()
        else:
            self._config.encryption_password = ""
        
        self._config.save()
        
        messagebox.showinfo(
            self._("app_title"),
            self._("settings_saved")
        )
        
        self._on_close()
    
    def _on_close(self):
        """Handle dialog close."""
        self.grab_release()
        self.destroy()
