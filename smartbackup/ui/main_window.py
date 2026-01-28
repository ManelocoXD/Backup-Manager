"""
Main window for SmartBackup application.
Modern UI with CustomTkinter.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
from typing import Optional

from ..config import get_config
from ..locales import Localizer
from ..backup_engine import get_backup_engine, BackupMode, BackupProgress, BackupResult
from ..scheduler import get_scheduler
from .theme import apply_theme, get_colors, format_bytes, format_duration
from .help_dialog import HelpDialog
from .schedule_dialog import ScheduleListDialog


class MainWindow(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Configuration
        self._config = get_config()
        self._engine = get_backup_engine()
        self._scheduler = get_scheduler()
        
        # Localization
        self._ = Localizer(self._config.language)
        
        # Apply theme
        self._theme = apply_theme(self._config.theme)
        self._colors = get_colors(self._theme)
        
        # Window setup
        self.title(self._("app_title"))
        self.geometry("700x600")
        self.minsize(600, 500)
        
        # Center window
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - 700) // 2
        y = (screen_h - 600) // 2
        self.geometry(f"+{x}+{y}")
        
        # State
        self._source_path: Optional[str] = self._config.last_source
        self._dest_path: Optional[str] = self._config.last_destination
        self._backup_thread: Optional[threading.Thread] = None
        self._is_running = False
        
        # Create UI
        self._create_widgets()
        
        # Restore last values
        self._restore_state()
        
        # Start scheduler
        self._scheduler.start()
    
    def _create_widgets(self):
        """Create all UI widgets with premium design."""
        # Main container with subtle background
        self._main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._main_frame.pack(fill="both", expand=True)
        
        # === HERO HEADER SECTION ===
        self._create_header()
        
        # === CONTENT AREA ===
        content_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=(0, 25))
        
        # Folder selection card
        self._create_folder_selection(content_frame)
        
        # Mode selection card
        self._create_mode_selection(content_frame)
        
        # Action buttons
        self._create_action_buttons(content_frame)
        
        # Progress section
        self._create_progress_section(content_frame)
        
        # Footer
        self._create_footer(content_frame)
    
    def _create_header(self):
        """Create premium hero header with gradient-like effect."""
        # Hero container with primary color background
        hero = ctk.CTkFrame(
            self._main_frame,
            fg_color=self._colors["primary"],
            corner_radius=0
        )
        hero.pack(fill="x")
        
        # Inner container for content
        hero_content = ctk.CTkFrame(hero, fg_color="transparent")
        hero_content.pack(fill="x", padx=30, pady=25)
        
        # Left side - Branding
        brand_frame = ctk.CTkFrame(hero_content, fg_color="transparent")
        brand_frame.pack(side="left", fill="y")
        
        # App icon and title
        title = ctk.CTkLabel(
            brand_frame,
            text="🛡️ SmartBackup",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color="#FFFFFF"
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            brand_frame,
            text=self._("app_subtitle"),
            font=ctk.CTkFont(size=14),
            text_color="#E0E0E0"
        )
        subtitle.pack(anchor="w", pady=(2, 0))
        
        # Right side - Action buttons
        actions_frame = ctk.CTkFrame(hero_content, fg_color="transparent")
        actions_frame.pack(side="right")
        
        # Schedule button - prominent
        schedule_btn = ctk.CTkButton(
            actions_frame,
            text="📅 " + self._("schedule"),
            command=self._show_schedules,
            width=130,
            height=42,
            corner_radius=10,
            fg_color="#FFFFFF",
            hover_color="#F0F0F0",
            text_color=self._colors["primary"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        schedule_btn.pack(side="left", padx=(0, 10))
        
        # Restore button - prominent
        restore_btn = ctk.CTkButton(
            actions_frame,
            text="🔄 " + self._("restore"),
            command=self._show_restore_dialog,
            width=130,
            height=42,
            corner_radius=10,
            fg_color="#FFFFFF",
            hover_color="#F0F0F0",
            text_color=self._colors["secondary"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        restore_btn.pack(side="left", padx=(0, 10))
        
        # Help button - subtle
        help_btn = ctk.CTkButton(
            actions_frame,
            text="❓",
            command=self._show_help,
            width=42,
            height=42,
            corner_radius=10,
            fg_color="#5A9BF8",
            hover_color="#7AABF8",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=18)
        )
        help_btn.pack(side="left")
    
    def _create_folder_selection(self, parent):
        """Create premium source and destination folder selectors."""
        # Main card container
        folders_card = ctk.CTkFrame(
            parent,
            fg_color=self._colors["surface"],
            corner_radius=16
        )
        folders_card.pack(fill="x", pady=(20, 12))
        
        # Card header
        header = ctk.CTkLabel(
            folders_card,
            text="📁 " + self._("source_folder") + " & " + self._("destination_folder"),
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=20, pady=(18, 12))
        
        # Source folder row
        source_frame = ctk.CTkFrame(folders_card, fg_color="transparent")
        source_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        source_icon = ctk.CTkLabel(
            source_frame,
            text="📤",
            font=ctk.CTkFont(size=18),
            width=30
        )
        source_icon.pack(side="left")
        
        self._source_entry = ctk.CTkEntry(
            source_frame,
            placeholder_text=self._("select_source") + "...",
            height=45,
            corner_radius=10,
            state="readonly",
            font=ctk.CTkFont(size=13)
        )
        self._source_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))
        
        source_btn = ctk.CTkButton(
            source_frame,
            text="📂 " + self._("browse"),
            command=self._browse_source,
            width=110,
            height=45,
            corner_radius=10,
            fg_color=self._colors["secondary"],
            hover_color=self._colors["secondary_hover"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        source_btn.pack(side="right")
        
        # Destination folder row
        dest_frame = ctk.CTkFrame(folders_card, fg_color="transparent")
        dest_frame.pack(fill="x", padx=20, pady=(0, 18))
        
        dest_icon = ctk.CTkLabel(
            dest_frame,
            text="📥",
            font=ctk.CTkFont(size=18),
            width=30
        )
        dest_icon.pack(side="left")
        
        self._dest_entry = ctk.CTkEntry(
            dest_frame,
            placeholder_text=self._("select_destination") + "...",
            height=45,
            corner_radius=10,
            state="readonly",
            font=ctk.CTkFont(size=13)
        )
        self._dest_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))
        
        dest_btn = ctk.CTkButton(
            dest_frame,
            text="📂 " + self._("browse"),
            command=self._browse_destination,
            width=110,
            height=45,
            corner_radius=10,
            fg_color=self._colors["secondary"],
            hover_color=self._colors["secondary_hover"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        dest_btn.pack(side="right")
    
    def _create_mode_selection(self, parent):
        """Create premium backup mode selector with card buttons."""
        mode_card = ctk.CTkFrame(
            parent,
            fg_color=self._colors["surface"],
            corner_radius=16
        )
        mode_card.pack(fill="x", pady=(0, 12))
        
        mode_label = ctk.CTkLabel(
            mode_card,
            text="⚙️ " + self._("backup_mode"),
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        mode_label.pack(fill="x", padx=20, pady=(18, 12))
        
        # Mode selection with styled buttons
        modes_row = ctk.CTkFrame(mode_card, fg_color="transparent")
        modes_row.pack(fill="x", padx=20, pady=(0, 18))
        
        self._mode_var = ctk.StringVar(value=self._config.last_mode)
        
        modes = [
            ("full", "💾", self._("mode_full"), self._colors["primary"]),
            ("incremental", "📊", self._("mode_incremental"), self._colors["secondary"]),
            ("differential", "📈", self._("mode_differential"), "#8B5CF6"),
        ]
        
        for i, (value, icon, text, color) in enumerate(modes):
            btn = ctk.CTkRadioButton(
                modes_row,
                text=f"{icon} {text}",
                variable=self._mode_var,
                value=value,
                font=ctk.CTkFont(size=14),
                radiobutton_width=22,
                radiobutton_height=22
            )
            btn.pack(side="left", padx=(0 if i == 0 else 30, 0))
    
    def _create_action_buttons(self, parent):
        """Create premium main action button."""
        actions_frame = ctk.CTkFrame(parent, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(8, 12))
        
        # Main backup button - Large and prominent
        self._backup_btn = ctk.CTkButton(
            actions_frame,
            text="🚀 " + self._("backup_now"),
            command=self._start_backup,
            height=58,
            corner_radius=14,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=self._colors["primary"],
            hover_color=self._colors["primary_hover"]
        )
        self._backup_btn.pack(fill="x")
        
        # Cancel button (hidden initially)
        self._cancel_btn = ctk.CTkButton(
            actions_frame,
            text="⏹️ " + self._("cancel"),
            command=self._cancel_backup,
            height=58,
            corner_radius=14,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=self._colors["danger"],
            hover_color=self._colors["danger_hover"]
        )
        # Don't pack initially
    
    def _create_progress_section(self, parent):
        """Create premium progress indicators."""
        self._progress_frame = ctk.CTkFrame(
            parent,
            fg_color=self._colors["surface"],
            corner_radius=16
        )
        # Don't pack initially - shown during backup
        
        # Progress header
        progress_header = ctk.CTkLabel(
            self._progress_frame,
            text="⏳ " + self._("status_backing_up"),
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        progress_header.pack(fill="x", padx=20, pady=(18, 12))
        
        # Progress bar with rounded style
        self._progress_bar = ctk.CTkProgressBar(
            self._progress_frame,
            height=12,
            corner_radius=6,
            progress_color=self._colors["primary"]
        )
        self._progress_bar.pack(fill="x", padx=20, pady=(0, 10))
        self._progress_bar.set(0)
        
        # Status label
        self._status_label = ctk.CTkLabel(
            self._progress_frame,
            text=self._("status_ready"),
            font=ctk.CTkFont(size=13),
            text_color=self._colors["text_secondary"]
        )
        self._status_label.pack(fill="x", padx=20, pady=(0, 5))
        
        # Current file label
        self._file_label = ctk.CTkLabel(
            self._progress_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self._colors["text_secondary"],
            anchor="w"
        )
        self._file_label.pack(fill="x", padx=20, pady=(0, 18))
    
    def _create_footer(self, parent):
        """Create footer with stats."""
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=(10, 0))
        
        self._stats_label = ctk.CTkLabel(
            footer,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self._colors["text_secondary"]
        )
        self._stats_label.pack(side="left")
    
    def _restore_state(self):
        """Restore previous session state."""
        if self._source_path and Path(self._source_path).exists():
            self._source_entry.configure(state="normal")
            self._source_entry.delete(0, "end")
            self._source_entry.insert(0, self._source_path)
            self._source_entry.configure(state="readonly")
        
        if self._dest_path and Path(self._dest_path).exists():
            self._dest_entry.configure(state="normal")
            self._dest_entry.delete(0, "end")
            self._dest_entry.insert(0, self._dest_path)
            self._dest_entry.configure(state="readonly")
    
    def _browse_source(self):
        """Open folder browser for source."""
        folder = filedialog.askdirectory(
            title=self._("select_source"),
            initialdir=self._source_path or None
        )
        if folder:
            self._source_path = folder
            self._config.last_source = folder
            self._source_entry.configure(state="normal")
            self._source_entry.delete(0, "end")
            self._source_entry.insert(0, folder)
            self._source_entry.configure(state="readonly")
    
    def _browse_destination(self):
        """Open folder browser for destination."""
        folder = filedialog.askdirectory(
            title=self._("select_destination"),
            initialdir=self._dest_path or None
        )
        if folder:
            self._dest_path = folder
            self._config.last_destination = folder
            self._dest_entry.configure(state="normal")
            self._dest_entry.delete(0, "end")
            self._dest_entry.insert(0, folder)
            self._dest_entry.configure(state="readonly")
    
    def _show_help(self):
        """Show help dialog."""
        HelpDialog(self, self._)
    
    def _show_schedules(self):
        """Show scheduled backups dialog."""
        ScheduleListDialog(self, self._)
    
    def _validate_inputs(self) -> bool:
        """Validate source and destination paths."""
        if not self._source_path:
            messagebox.showerror(
                self._("app_title"),
                self._("error_no_source")
            )
            return False
        
        if not self._dest_path:
            messagebox.showerror(
                self._("app_title"),
                self._("error_no_destination")
            )
            return False
        
        if not Path(self._source_path).exists():
            messagebox.showerror(
                self._("app_title"),
                self._("error_source_not_exists")
            )
            return False
        
        if self._source_path == self._dest_path:
            messagebox.showerror(
                self._("app_title"),
                self._("error_same_folder")
            )
            return False
        
        # Check for full backup requirement
        mode = BackupMode(self._mode_var.get())
        if mode == BackupMode.DIFFERENTIAL:
            if not self._engine.has_full_backup(self._source_path):
                messagebox.showerror(
                    self._("app_title"),
                    self._("error_no_full_backup")
                )
                return False
        
        return True
    
    def _start_backup(self):
        """Start the backup operation."""
        if not self._validate_inputs():
            return
        
        # Save mode preference
        self._config.last_mode = self._mode_var.get()
        
        # Switch UI to running state
        self._is_running = True
        self._backup_btn.pack_forget()
        self._cancel_btn.pack(fill="x")
        self._progress_frame.pack(fill="x", pady=(0, 20))
        self._progress_bar.set(0)
        self._status_label.configure(text=self._("status_backing_up"))
        self._file_label.configure(text="")
        
        # Start backup in thread
        mode = BackupMode(self._mode_var.get())
        self._backup_thread = threading.Thread(
            target=self._run_backup_thread,
            args=(self._source_path, self._dest_path, mode),
            daemon=True
        )
        self._backup_thread.start()
    
    def _run_backup_thread(self, source: str, dest: str, mode: BackupMode):
        """Run backup in background thread."""
        def on_progress(progress: BackupProgress):
            # Schedule UI update on main thread
            self.after(0, lambda: self._update_progress(progress))
        
        result = self._engine.run_backup(source, dest, mode, on_progress)
        
        # Schedule result handling on main thread
        self.after(0, lambda: self._handle_backup_result(result))
    
    def _update_progress(self, progress: BackupProgress):
        """Update UI with progress."""
        if not self._is_running:
            return
        
        # Update progress bar
        percent = progress.progress_percent / 100
        self._progress_bar.set(percent)
        
        # Update status
        status_text = f"{progress.files_processed}/{progress.files_total} - "
        status_text += self._("files_copied", count=progress.files_copied)
        self._status_label.configure(text=status_text)
        
        # Update current file (truncate if too long)
        file_text = progress.current_file
        if len(file_text) > 60:
            file_text = "..." + file_text[-57:]
        self._file_label.configure(text=file_text)
    
    def _handle_backup_result(self, result: BackupResult):
        """Handle backup completion."""
        self._is_running = False
        
        # Reset UI
        self._cancel_btn.pack_forget()
        self._backup_btn.pack(fill="x")
        self._progress_bar.set(1 if result.success else 0)
        
        if result.success:
            self._status_label.configure(
                text=self._("status_complete"),
                text_color=self._colors["success"]
            )
            
            # Show stats
            stats = f"✅ {self._('files_copied', count=result.files_copied)}"
            if result.files_skipped > 0:
                stats += f" | {self._('files_skipped', count=result.files_skipped)}"
            stats += f" | {format_bytes(result.bytes_copied)} | {format_duration(result.duration_seconds)}"
            self._stats_label.configure(text=stats)
            
            messagebox.showinfo(
                self._("app_title"),
                self._("status_complete") + f"\n\n{stats}"
            )
        elif result.error_message and "cancelled" in result.error_message.lower():
            self._status_label.configure(
                text=self._("status_cancelled"),
                text_color=self._colors["warning"]
            )
        else:
            self._status_label.configure(
                text=self._("status_error"),
                text_color=self._colors["danger"]
            )
            messagebox.showerror(
                self._("app_title"),
                f"{self._('status_error')}\n\n{result.error_message}"
            )
    
    def _cancel_backup(self):
        """Cancel the running backup."""
        self._engine.cancel()
        self._status_label.configure(text=self._("status_cancelled"))
    
    def _show_restore_dialog(self):
        """Show dialog to select backup folder and restore destination."""
        from tkinter import filedialog, messagebox
        
        # Select backup folder to restore from
        backup_folder = filedialog.askdirectory(
            title=self._("select_backup_folder")
        )
        if not backup_folder:
            return
        
        # Select destination for restore
        restore_dest = filedialog.askdirectory(
            title=self._("select_restore_destination")
        )
        if not restore_dest:
            return
        
        # Confirm restore
        confirm = messagebox.askyesno(
            self._("restore"),
            f"{self._('select_backup_folder')}:\n{backup_folder}\n\n"
            f"{self._('select_restore_destination')}:\n{restore_dest}\n\n"
            f"¿Continuar con la restauración?"
        )
        
        if confirm:
            self._start_restore(backup_folder, restore_dest)
    
    def _start_restore(self, backup_folder: str, restore_dest: str):
        """Start the restore operation."""
        from .backup_engine import RestoreResult
        
        # Switch UI to running state
        self._is_running = True
        self._backup_btn.pack_forget()
        self._cancel_btn.pack(fill="x")
        self._progress_frame.pack(fill="x", pady=(0, 20))
        self._progress_bar.set(0)
        self._status_label.configure(text=self._("restoring"))
        self._file_label.configure(text="")
        
        # Start restore in thread
        self._backup_thread = threading.Thread(
            target=self._run_restore_thread,
            args=(backup_folder, restore_dest),
            daemon=True
        )
        self._backup_thread.start()
    
    def _run_restore_thread(self, backup_folder: str, restore_dest: str):
        """Run restore in background thread."""
        from .backup_engine import BackupProgress
        
        def on_progress(progress: BackupProgress):
            self.after(0, lambda: self._update_progress(progress))
        
        result = self._engine.run_restore(backup_folder, restore_dest, on_progress)
        self.after(0, lambda: self._handle_restore_result(result))
    
    def _handle_restore_result(self, result):
        """Handle restore completion."""
        from .backup_engine import RestoreResult
        
        self._is_running = False
        
        # Reset UI
        self._cancel_btn.pack_forget()
        self._backup_btn.pack(fill="x")
        self._progress_bar.set(1 if result.success else 0)
        
        if result.success:
            self._status_label.configure(
                text=self._("restore_complete"),
                text_color=self._colors["success"]
            )
            
            stats = f"✅ {self._('files_restored', count=result.files_restored)}"
            if result.files_skipped > 0:
                stats += f" | {self._('files_skipped', count=result.files_skipped)}"
            stats += f" | {format_bytes(result.bytes_restored)} | {format_duration(result.duration_seconds)}"
            self._stats_label.configure(text=stats)
            
            messagebox.showinfo(
                self._("restore"),
                self._("restore_complete") + f"\n\n{stats}"
            )
        elif result.error_message and "cancelled" in result.error_message.lower():
            self._status_label.configure(
                text=self._("restore_cancelled"),
                text_color=self._colors["warning"]
            )
        else:
            self._status_label.configure(
                text=self._("status_error"),
                text_color=self._colors["danger"]
            )
            messagebox.showerror(
                self._("restore"),
                f"{self._('status_error')}\n\n{result.error_message}"
            )
