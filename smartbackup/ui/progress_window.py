"""
Progress notification window for scheduled backups.
Shows a small window with backup progress that auto-closes after completion.
"""

import customtkinter as ctk
from typing import Optional, Callable
import threading
from datetime import datetime

from ..backup_engine import BackupProgress, BackupResult
from ..locales import get_string


class ScheduledBackupWindow(ctk.CTkToplevel):
    """Small notification window for scheduled backup progress."""
    
    def __init__(
        self,
        schedule_name: str,
        lang: str = "es",
        on_close: Optional[Callable] = None
    ):
        super().__init__()
        
        self._lang = lang
        self._on_close = on_close
        self._schedule_name = schedule_name
        self._is_complete = False
        self._close_timer = None
        
        # Window setup
        self.title(f"SmartBackup - {schedule_name}")
        self.geometry("450x200")
        self.resizable(False, False)
        
        # Keep on top
        self.attributes("-topmost", True)
        
        # Position in bottom-right corner
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - 470
        y = screen_height - 280
        self.geometry(f"450x200+{x}+{y}")
        
        # Colors
        self._colors = {
            "primary": "#3B82F6",
            "success": "#22C55E",
            "warning": "#F59E0B",
            "danger": "#EF4444",
            "surface": "#1E293B",
            "text": "#F8FAFC",
            "text_dim": "#94A3B8"
        }
        
        self._create_widgets()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._handle_close)
    
    def _(self, key: str, **kwargs) -> str:
        """Get localized string."""
        return get_string(key, self._lang, **kwargs)
    
    def _create_widgets(self):
        """Create the window widgets."""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=self._colors["surface"])
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Header
        header = ctk.CTkFrame(main_frame, fg_color=self._colors["primary"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_label = ctk.CTkLabel(
            header,
            text=f"🔄 {self._schedule_name}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        )
        header_label.pack(side="left", padx=15, pady=10)
        
        self._time_label = ctk.CTkLabel(
            header,
            text=datetime.now().strftime("%H:%M"),
            font=ctk.CTkFont(size=14),
            text_color="#E0E0E0"
        )
        self._time_label.pack(side="right", padx=15, pady=10)
        
        # Content
        content = ctk.CTkFrame(main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Status label
        self._status_label = ctk.CTkLabel(
            content,
            text=self._("status_backing_up"),
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        self._status_label.pack(fill="x", pady=(0, 8))
        
        # Progress bar
        self._progress_bar = ctk.CTkProgressBar(
            content,
            height=12,
            corner_radius=6,
            progress_color=self._colors["primary"]
        )
        self._progress_bar.pack(fill="x", pady=(0, 8))
        self._progress_bar.set(0)
        
        # File label
        self._file_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=self._colors["text_dim"],
            anchor="w"
        )
        self._file_label.pack(fill="x")
        
        # Stats label
        self._stats_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self._stats_label.pack(fill="x", pady=(5, 0))
    
    def update_progress(self, progress: BackupProgress):
        """Update the progress display."""
        if self._is_complete:
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
        if len(file_text) > 50:
            file_text = "..." + file_text[-47:]
        self._file_label.configure(text=file_text)
    
    def show_complete(self, result: BackupResult, auto_close_seconds: int = 60):
        """Show completion status and schedule auto-close."""
        self._is_complete = True
        
        # Update UI
        self._progress_bar.set(1)
        
        if result.success:
            self._status_label.configure(
                text=self._("status_complete"),
                text_color=self._colors["success"]
            )
            self._progress_bar.configure(progress_color=self._colors["success"])
            
            # Show stats
            stats = f"✅ {self._('files_copied', count=result.files_copied)}"
            if result.files_skipped > 0:
                stats += f" | ⏭️ {result.files_skipped}"
            self._stats_label.configure(text=stats)
        else:
            self._status_label.configure(
                text=self._("status_error"),
                text_color=self._colors["danger"]
            )
            self._progress_bar.configure(progress_color=self._colors["danger"])
            self._stats_label.configure(text=result.error_message or "")
        
        self._file_label.configure(
            text=f"Cerrando en {auto_close_seconds} segundos..."
        )
        
        # Schedule auto-close
        self._schedule_auto_close(auto_close_seconds)
    
    def _schedule_auto_close(self, seconds: int):
        """Schedule the window to close after specified seconds."""
        if seconds <= 0:
            self._handle_close()
            return
        
        # Update countdown label
        self._file_label.configure(
            text=f"Cerrando en {seconds} segundos..."
        )
        
        # Schedule next countdown update
        self._close_timer = self.after(1000, lambda: self._schedule_auto_close(seconds - 1))
    
    def _handle_close(self):
        """Handle window close."""
        if self._close_timer:
            self.after_cancel(self._close_timer)
        
        if self._on_close:
            self._on_close()
        
        self.destroy()


def create_scheduled_backup_window(
    schedule_name: str,
    lang: str = "es"
) -> ScheduledBackupWindow:
    """Create a new scheduled backup progress window."""
    window = ScheduledBackupWindow(schedule_name, lang)
    return window
