"""
Schedule dialog for SmartBackup.
Allows users to create and edit scheduled backups.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Optional, Callable
from datetime import datetime

if TYPE_CHECKING:
    from .main_window import MainWindow

from ..locales import Localizer
from ..scheduler import ScheduleConfig, ScheduleFrequency, get_scheduler
from .theme import get_colors


class ScheduleDialog(ctk.CTkToplevel):
    """Dialog for creating or editing a scheduled backup."""
    
    DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    def __init__(
        self, 
        parent: "MainWindow", 
        localizer: Localizer,
        schedule: Optional[ScheduleConfig] = None,
        on_save: Optional[Callable[[ScheduleConfig], None]] = None
    ):
        super().__init__(parent)
        
        self._ = localizer
        self._colors = get_colors()
        self._schedule = schedule
        self._on_save = on_save
        self._scheduler = get_scheduler()
        
        # Window configuration
        self.title(self._("edit_schedule") if schedule else self._("add_schedule"))
        self.geometry("550x650")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 550) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 650) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        self._load_schedule_data()
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda e: self._on_close())
    
    def _create_widgets(self):
        """Create dialog widgets with premium design."""
        # Main container with dark background padding
        container = ctk.CTkScrollableFrame(
            self, 
            fg_color="transparent"
        )
        container.pack(fill="both", expand=True, padx=25, pady=25)
        
        # === HEADER SECTION ===
        header_frame = ctk.CTkFrame(
            container,
            fg_color=self._colors["primary"],
            corner_radius=15
        )
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_text = "✏️ " + self._("edit_schedule") if self._schedule else "✨ " + self._("add_schedule")
        title = ctk.CTkLabel(
            header_frame,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.pack(pady=18)
        
        # === BASIC INFO CARD ===
        basic_card = self._create_card(container, "📝 " + self._("schedule_name"))
        
        self._name_entry = ctk.CTkEntry(
            basic_card,
            height=45,
            corner_radius=10,
            placeholder_text=self._("schedule_name") + "...",
            font=ctk.CTkFont(size=14)
        )
        self._name_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # === PATHS CARD ===
        paths_card = self._create_card(container, "📁 " + self._("source_folder") + " & " + self._("destination_folder"))
        
        # Source folder row
        source_label = ctk.CTkLabel(
            paths_card,
            text="📤 " + self._("source_folder"),
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        source_label.pack(fill="x", padx=15, pady=(0, 5))
        
        source_row = ctk.CTkFrame(paths_card, fg_color="transparent")
        source_row.pack(fill="x", padx=15, pady=(0, 12))
        
        self._source_entry = ctk.CTkEntry(
            source_row,
            height=42,
            corner_radius=10,
            state="readonly",
            font=ctk.CTkFont(size=13)
        )
        self._source_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        source_btn = ctk.CTkButton(
            source_row,
            text="📂",
            command=self._browse_source,
            width=50,
            height=42,
            corner_radius=10,
            fg_color=self._colors["secondary"],
            hover_color=self._colors["secondary_hover"]
        )
        source_btn.pack(side="right")
        
        # Destination folder row
        dest_label = ctk.CTkLabel(
            paths_card,
            text="📥 " + self._("destination_folder"),
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        dest_label.pack(fill="x", padx=15, pady=(5, 5))
        
        dest_row = ctk.CTkFrame(paths_card, fg_color="transparent")
        dest_row.pack(fill="x", padx=15, pady=(0, 15))
        
        self._dest_entry = ctk.CTkEntry(
            dest_row,
            height=42,
            corner_radius=10,
            state="readonly",
            font=ctk.CTkFont(size=13)
        )
        self._dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        dest_btn = ctk.CTkButton(
            dest_row,
            text="📂",
            command=self._browse_dest,
            width=50,
            height=42,
            corner_radius=10,
            fg_color=self._colors["secondary"],
            hover_color=self._colors["secondary_hover"]
        )
        dest_btn.pack(side="right")
        
        # === BACKUP MODE CARD ===
        mode_card = self._create_card(container, "⚙️ " + self._("backup_mode"))
        
        self._mode_var = ctk.StringVar(value="full")
        mode_buttons_frame = ctk.CTkFrame(mode_card, fg_color="transparent")
        mode_buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        modes = [
            ("full", "💾 " + self._("mode_full")),
            ("incremental", "📊 " + self._("mode_incremental")),
            ("differential", "📈 " + self._("mode_differential")),
        ]
        for value, text in modes:
            rb = ctk.CTkRadioButton(
                mode_buttons_frame,
                text=text,
                variable=self._mode_var,
                value=value,
                font=ctk.CTkFont(size=13),
                radiobutton_width=22,
                radiobutton_height=22
            )
            rb.pack(side="left", padx=(0, 20))
        
        # === SCHEDULE TIMING CARD ===
        timing_card = self._create_card(container, "🕐 " + self._("frequency") + " & " + self._("time"))
        
        # Frequency dropdown
        freq_label = ctk.CTkLabel(
            timing_card,
            text="🔄 " + self._("frequency"),
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        freq_label.pack(fill="x", padx=15, pady=(0, 5))
        
        self._freq_var = ctk.StringVar(value=self._("freq_daily"))
        freq_menu = ctk.CTkOptionMenu(
            timing_card,
            variable=self._freq_var,
            values=[
                self._("freq_once"),
                self._("freq_hourly"),
                self._("freq_daily"),
                self._("freq_weekly"),
                self._("freq_monthly"),
                self._("freq_custom"),
            ],
            command=self._on_frequency_change,
            height=42,
            corner_radius=10,
            fg_color=self._colors["surface"],
            button_color=self._colors["primary"],
            button_hover_color=self._colors["primary_hover"],
            font=ctk.CTkFont(size=13)
        )
        freq_menu.pack(fill="x", padx=15, pady=(0, 12))
        
        # Hourly interval frame (for hourly frequency)
        self._hourly_frame = ctk.CTkFrame(timing_card, fg_color="transparent")
        hourly_inner = ctk.CTkFrame(self._hourly_frame, fg_color="transparent")
        hourly_inner.pack(fill="x", padx=15, pady=(0, 12))
        
        ctk.CTkLabel(
            hourly_inner,
            text="⏱️ " + self._("hour_interval"),
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=(0, 10))
        
        self._interval_var = ctk.StringVar(value="1")
        interval_menu = ctk.CTkOptionMenu(
            hourly_inner,
            variable=self._interval_var,
            values=[str(i) for i in range(1, 13)],
            width=80,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=13)
        )
        interval_menu.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            hourly_inner,
            text=self._("hours"),
            font=ctk.CTkFont(size=13)
        ).pack(side="left")
        
        # Time selection
        time_label = ctk.CTkLabel(
            timing_card,
            text="⏰ " + self._("time"),
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        time_label.pack(fill="x", padx=15, pady=(5, 5))
        
        time_frame = ctk.CTkFrame(timing_card, fg_color="transparent")
        time_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        self._hour_var = ctk.StringVar(value="00")
        hour_menu = ctk.CTkOptionMenu(
            time_frame,
            variable=self._hour_var,
            values=[f"{i:02d}" for i in range(24)],
            width=80,
            height=42,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        hour_menu.pack(side="left", padx=(0, 5))
        
        ctk.CTkLabel(
            time_frame, 
            text=":", 
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")
        
        self._minute_var = ctk.StringVar(value="00")
        minute_menu = ctk.CTkOptionMenu(
            time_frame,
            variable=self._minute_var,
            values=[f"{i:02d}" for i in range(0, 60, 5)],
            width=80,
            height=42,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        minute_menu.pack(side="left", padx=(5, 0))
        
        # Days of week checkboxes (for weekly/custom)
        self._day_frame = ctk.CTkFrame(timing_card, fg_color="transparent")
        
        days_label = ctk.CTkLabel(
            self._day_frame,
            text="📅 " + self._("select_days"),
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        days_label.pack(fill="x", padx=15, pady=(5, 8))
        
        days_row = ctk.CTkFrame(self._day_frame, fg_color="transparent")
        days_row.pack(fill="x", padx=15, pady=(0, 12))
        
        # Create styled checkbox for each day
        self._day_checkboxes = {}
        for i, day_key in enumerate(self.DAYS_OF_WEEK):
            day_var = ctk.BooleanVar(value=(i == 0))
            cb = ctk.CTkCheckBox(
                days_row,
                text=self._(day_key)[:3].upper(),
                variable=day_var,
                width=50,
                checkbox_width=22,
                checkbox_height=22,
                corner_radius=5,
                font=ctk.CTkFont(size=11, weight="bold")
            )
            cb.pack(side="left", padx=(0, 6))
            self._day_checkboxes[i] = day_var
        
        # Day of month (for monthly)
        self._dom_frame = ctk.CTkFrame(timing_card, fg_color="transparent")
        
        dom_label = ctk.CTkLabel(
            self._dom_frame,
            text="📆 " + self._("day_of_month"),
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        dom_label.pack(fill="x", padx=15, pady=(5, 5))
        
        self._dom_var = ctk.StringVar(value="1")
        dom_menu = ctk.CTkOptionMenu(
            self._dom_frame,
            variable=self._dom_var,
            values=[str(i) for i in range(1, 29)],
            height=42,
            corner_radius=10,
            font=ctk.CTkFont(size=13)
        )
        dom_menu.pack(fill="x", padx=15, pady=(0, 12))
        
        # Spacing at end of timing card
        ctk.CTkLabel(timing_card, text="", height=5).pack()
        
        # === STATUS TOGGLE ===
        status_frame = ctk.CTkFrame(
            container,
            fg_color=self._colors["surface"],
            corner_radius=12
        )
        status_frame.pack(fill="x", pady=(8, 15))
        
        self._enabled_var = ctk.BooleanVar(value=True)
        enabled_switch = ctk.CTkSwitch(
            status_frame,
            text="🟢 " + self._("enabled"),
            variable=self._enabled_var,
            onvalue=True,
            offvalue=False,
            font=ctk.CTkFont(size=14, weight="bold"),
            switch_width=50,
            switch_height=26
        )
        enabled_switch.pack(padx=15, pady=15)
        
        # === ADVANCED OPTIONS (Compression/Encryption) ===
        advanced_card = ctk.CTkFrame(
            container,
            fg_color=self._colors["surface"],
            corner_radius=12
        )
        advanced_card.pack(fill="x", pady=(0, 15))
        
        advanced_header = ctk.CTkLabel(
            advanced_card,
            text="⚙️ " + self._("advanced_options"),
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        advanced_header.pack(fill="x", padx=15, pady=(12, 8))
        
        # Compression option
        self._compress_var = ctk.BooleanVar(value=False)
        compress_check = ctk.CTkCheckBox(
            advanced_card,
            text="📦 " + self._("enable_compression"),
            variable=self._compress_var,
            font=ctk.CTkFont(size=13),
            checkbox_width=24,
            checkbox_height=24
        )
        compress_check.pack(fill="x", padx=15, pady=(0, 10))
        
        # Encryption option
        self._encrypt_var = ctk.BooleanVar(value=False)
        encrypt_check = ctk.CTkCheckBox(
            advanced_card,
            text="🔐 " + self._("enable_encryption"),
            variable=self._encrypt_var,
            command=self._on_encrypt_toggle,
            font=ctk.CTkFont(size=13),
            checkbox_width=24,
            checkbox_height=24
        )
        encrypt_check.pack(fill="x", padx=15, pady=(0, 5))
        
        # Password frame (hidden by default)
        self._password_frame = ctk.CTkFrame(advanced_card, fg_color="transparent")
        
        pwd_label = ctk.CTkLabel(
            self._password_frame,
            text=self._("encryption_password") + ":",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        pwd_label.pack(fill="x", padx=0, pady=(5, 2))
        
        self._password_entry = ctk.CTkEntry(
            self._password_frame,
            height=38,
            corner_radius=8,
            show="•",
            placeholder_text=self._("enter_password")
        )
        self._password_entry.pack(fill="x", pady=(0, 5))
        
        self._confirm_entry = ctk.CTkEntry(
            self._password_frame,
            height=38,
            corner_radius=8,
            show="•",
            placeholder_text=self._("confirm_password")
        )
        self._confirm_entry.pack(fill="x")
        
        # Spacing at end
        ctk.CTkLabel(advanced_card, text="", height=5).pack()
        
        # === ACTION BUTTONS ===
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(5, 0))
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="❌ " + self._("cancel"),
            command=self._on_close,
            width=140,
            height=48,
            corner_radius=12,
            fg_color=self._colors["surface"],
            hover_color=self._colors["surface_light"],
            text_color=self._colors["text"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="✅ " + self._("save"),
            command=self._save_schedule,
            width=140,
            height=48,
            corner_radius=12,
            fg_color=self._colors["primary"],
            hover_color=self._colors["primary_hover"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        save_btn.pack(side="right")
        
        # Initially hide day-specific fields
        self._on_frequency_change(self._("freq_daily"))
    
    def _create_card(self, parent, title: str) -> ctk.CTkFrame:
        """Create a styled card section with title."""
        card = ctk.CTkFrame(
            parent,
            fg_color=self._colors["surface"],
            corner_radius=12
        )
        card.pack(fill="x", pady=(0, 12))
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        title_label.pack(fill="x", padx=15, pady=(12, 10))
        
        return card
    
    def _create_field(self, parent, label_key: str):
        """Create a field label."""
        label = ctk.CTkLabel(
            parent,
            text=self._(label_key),
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        label.pack(fill="x", pady=(5, 5))
    
    def _load_schedule_data(self):
        """Load existing schedule data into form."""
        if not self._schedule:
            return
        
        self._name_entry.insert(0, self._schedule.name)
        
        # Source
        self._source_entry.configure(state="normal")
        self._source_entry.insert(0, self._schedule.source)
        self._source_entry.configure(state="readonly")
        
        # Destination
        self._dest_entry.configure(state="normal")
        self._dest_entry.insert(0, self._schedule.destination)
        self._dest_entry.configure(state="readonly")
        
        # Mode
        self._mode_var.set(self._schedule.mode)
        
        # Frequency
        freq_map = {
            "once": "freq_once",
            "hourly": "freq_hourly",
            "daily": "freq_daily",
            "weekly": "freq_weekly",
            "monthly": "freq_monthly",
            "custom": "freq_custom",
        }
        self._freq_var.set(self._(freq_map.get(self._schedule.frequency, "freq_daily")))
        
        # Time
        self._hour_var.set(f"{self._schedule.hour:02d}")
        self._minute_var.set(f"{self._schedule.minute:02d}")
        
        # Hourly interval
        self._interval_var.set(str(self._schedule.hour_interval))
        
        # Days of week - set checkboxes
        for i, var in self._day_checkboxes.items():
            var.set(i in self._schedule.days_of_week)
        
        # Day of month
        self._dom_var.set(str(self._schedule.day_of_month))
        
        # Enabled
        self._enabled_var.set(self._schedule.enabled)
        
        # Compression and encryption
        self._compress_var.set(self._schedule.compress)
        self._encrypt_var.set(self._schedule.encrypt)
        if self._schedule.encrypt and self._schedule.encryption_password:
            self._password_entry.insert(0, self._schedule.encryption_password)
            self._confirm_entry.insert(0, self._schedule.encryption_password)
            self._on_encrypt_toggle()
        
        # Update visibility
        self._on_frequency_change(self._freq_var.get())
    
    def _on_frequency_change(self, value: str):
        """Handle frequency selection change."""
        # Hide all optional fields first
        self._day_frame.pack_forget()
        self._dom_frame.pack_forget()
        self._hourly_frame.pack_forget()
        
        # Show relevant fields based on frequency
        if value == self._("freq_hourly"):
            self._hourly_frame.pack(fill="x", pady=(0, 10))
        elif value == self._("freq_weekly") or value == self._("freq_custom"):
            self._day_frame.pack(fill="x", pady=(0, 10))
        elif value == self._("freq_monthly"):
            self._dom_frame.pack(fill="x", pady=(0, 10))
    
    def _browse_source(self):
        """Browse for source folder."""
        folder = filedialog.askdirectory(title=self._("select_source"))
        if folder:
            self._source_entry.configure(state="normal")
            self._source_entry.delete(0, "end")
            self._source_entry.insert(0, folder)
            self._source_entry.configure(state="readonly")
    
    def _browse_dest(self):
        """Browse for destination folder."""
        folder = filedialog.askdirectory(title=self._("select_destination"))
        if folder:
            self._dest_entry.configure(state="normal")
            self._dest_entry.delete(0, "end")
            self._dest_entry.insert(0, folder)
            self._dest_entry.configure(state="readonly")
    
    def _get_frequency_value(self) -> str:
        """Get the frequency enum value from selection."""
        freq_text = self._freq_var.get()
        freq_map = {
            self._("freq_once"): "once",
            self._("freq_hourly"): "hourly",
            self._("freq_daily"): "daily",
            self._("freq_weekly"): "weekly",
            self._("freq_monthly"): "monthly",
            self._("freq_custom"): "custom",
        }
        return freq_map.get(freq_text, "daily")
    
    def _get_days_of_week(self) -> list:
        """Get list of selected days (0=Monday, 6=Sunday)."""
        selected_days = []
        for i, var in self._day_checkboxes.items():
            if var.get():
                selected_days.append(i)
        # Default to Monday if none selected
        return selected_days if selected_days else [0]
    
    def _validate(self) -> bool:
        """Validate form inputs."""
        if not self._name_entry.get().strip():
            messagebox.showerror(self._("app_title"), self._("schedule_name") + " required")
            return False
        
        if not self._source_entry.get():
            messagebox.showerror(self._("app_title"), self._("error_no_source"))
            return False
        
        if not self._dest_entry.get():
            messagebox.showerror(self._("app_title"), self._("error_no_destination"))
            return False
        
        # Validate encryption password
        if self._encrypt_var.get():
            pwd = self._password_entry.get()
            confirm = self._confirm_entry.get()
            
            if not pwd:
                messagebox.showerror(self._("app_title"), self._("password_required"))
                return False
            
            if pwd != confirm:
                messagebox.showerror(self._("app_title"), self._("passwords_not_match"))
                return False
            
            if len(pwd) < 8:
                messagebox.showerror(self._("app_title"), self._("password_too_short"))
                return False
        
        return True
    
    def _on_encrypt_toggle(self):
        """Handle encryption checkbox toggle."""
        if self._encrypt_var.get():
            self._password_frame.pack(fill="x", padx=15, pady=(0, 10))
        else:
            self._password_frame.pack_forget()
    
    def _save_schedule(self):
        """Save the schedule."""
        if not self._validate():
            return
        
        # Create or update schedule config
        schedule_id = self._schedule.id if self._schedule else self._scheduler.generate_schedule_id()
        
        schedule = ScheduleConfig(
            id=schedule_id,
            name=self._name_entry.get().strip(),
            source=self._source_entry.get(),
            destination=self._dest_entry.get(),
            mode=self._mode_var.get(),
            frequency=self._get_frequency_value(),
            enabled=self._enabled_var.get(),
            hour=int(self._hour_var.get()),
            minute=int(self._minute_var.get()),
            days_of_week=self._get_days_of_week(),
            day_of_month=int(self._dom_var.get()),
            hour_interval=int(self._interval_var.get()),
            compress=self._compress_var.get(),
            encrypt=self._encrypt_var.get(),
            encryption_password=self._password_entry.get() if self._encrypt_var.get() else "",
        )
        
        # Save to scheduler
        if self._schedule:
            self._scheduler.update_schedule(schedule)
        else:
            self._scheduler.add_schedule(schedule)
        
        # Callback
        if self._on_save:
            self._on_save(schedule)
        
        # Show success message
        msg = self._("schedule_updated") if self._schedule else self._("schedule_created")
        messagebox.showinfo(self._("app_title"), msg)
        
        self._on_close()
    
    def _on_close(self):
        """Handle dialog close."""
        self.grab_release()
        self.destroy()


class ScheduleListDialog(ctk.CTkToplevel):
    """Dialog showing all scheduled backups."""
    
    def __init__(self, parent: "MainWindow", localizer: Localizer):
        super().__init__(parent)
        
        self._ = localizer
        self._colors = get_colors()
        self._parent = parent
        self._scheduler = get_scheduler()
        
        # Window configuration
        self.title(self._("scheduled_backups"))
        self.geometry("700x500")
        self.resizable(True, True)
        self.minsize(600, 400)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 700) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 500) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        self._refresh_list()
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda e: self._on_close())
    
    def _create_widgets(self):
        """Create dialog widgets with premium design."""
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=25)
        
        # === HEADER WITH GRADIENT ===
        header_frame = ctk.CTkFrame(
            container,
            fg_color=self._colors["primary"],
            corner_radius=15
        )
        header_frame.pack(fill="x", pady=(0, 20))
        
        header_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_inner.pack(fill="x", padx=20, pady=18)
        
        title = ctk.CTkLabel(
            header_inner,
            text="📅 " + self._("scheduled_backups"),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title.pack(side="left")
        
        add_btn = ctk.CTkButton(
            header_inner,
            text="✨ " + self._("add_schedule"),
            command=self._add_schedule,
            width=160,
            height=42,
            corner_radius=10,
            fg_color="#FFFFFF",
            hover_color="#F0F0F0",
            text_color=self._colors["primary"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        add_btn.pack(side="right")
        
        # Schedule list with better styling
        self._list_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="transparent",
            corner_radius=12
        )
        self._list_frame.pack(fill="both", expand=True)
        
        # Close button
        close_btn = ctk.CTkButton(
            container,
            text="❌ " + self._("close"),
            command=self._on_close,
            width=140,
            height=45,
            corner_radius=12,
            fg_color=self._colors["surface"],
            hover_color=self._colors["surface_light"],
            text_color=self._colors["text"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        close_btn.pack(pady=(15, 0))
    
    def _refresh_list(self):
        """Refresh the schedule list."""
        # Clear existing items
        for widget in self._list_frame.winfo_children():
            widget.destroy()
        
        schedules = self._scheduler.get_all_schedules()
        
        if not schedules:
            empty_label = ctk.CTkLabel(
                self._list_frame,
                text=self._("no_schedules"),
                font=ctk.CTkFont(size=14),
                text_color=self._colors["text_secondary"]
            )
            empty_label.pack(pady=50)
            return
        
        # Create schedule cards
        for schedule in schedules:
            self._create_schedule_card(schedule)
    
    def _create_schedule_card(self, schedule: ScheduleConfig):
        """Create a premium styled card for a schedule."""
        card = ctk.CTkFrame(
            self._list_frame,
            fg_color=self._colors["surface"],
            corner_radius=12
        )
        card.pack(fill="x", pady=6)
        
        # Left side - info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=18, pady=14)
        
        # Name and status row
        name_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_row.pack(fill="x")
        
        # Status indicator with glow effect
        status_color = self._colors["success"] if schedule.enabled else self._colors["text_secondary"]
        status_label = ctk.CTkLabel(
            name_row,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=status_color
        )
        status_label.pack(side="left", padx=(0, 10))
        
        name_label = ctk.CTkLabel(
            name_row,
            text=schedule.name,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        name_label.pack(side="left")
        
        # Mode badge
        mode_colors = {
            "full": self._colors["primary"],
            "incremental": self._colors["secondary"],
            "differential": self._colors["warning"]
        }
        mode_badge = ctk.CTkLabel(
            name_row,
            text=f"  {schedule.mode.upper()}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=mode_colors.get(schedule.mode, self._colors["primary"]),
            corner_radius=6,
            text_color="#FFFFFF"
        )
        mode_badge.pack(side="left", padx=(12, 0))
        
        # Details row
        freq_map = {
            "once": "🎯 " + self._("freq_once"),
            "hourly": "⏰ " + self._("freq_hourly"),
            "daily": "📆 " + self._("freq_daily"),
            "weekly": "📅 " + self._("freq_weekly"),
            "monthly": "🗓️ " + self._("freq_monthly"),
            "custom": "✨ " + self._("freq_custom"),
        }
        freq_text = freq_map.get(schedule.frequency, schedule.frequency)
        time_text = f"{schedule.hour:02d}:{schedule.minute:02d}"
        
        details = f"{freq_text} @ {time_text}"
        if schedule.next_run:
            try:
                next_dt = datetime.fromisoformat(schedule.next_run)
                details += f" • {self._('next_run')}: {next_dt.strftime('%d/%m %H:%M')}"
            except:
                pass
        
        details_label = ctk.CTkLabel(
            info_frame,
            text=details,
            font=ctk.CTkFont(size=12),
            text_color=self._colors["text_secondary"],
            anchor="w"
        )
        details_label.pack(fill="x")
        
        # Right side - actions
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.pack(side="right", padx=18, pady=14)
        
        # Run now button
        run_btn = ctk.CTkButton(
            actions_frame,
            text="▶️",
            command=lambda s=schedule: self._run_now(s),
            width=40,
            height=40,
            corner_radius=10,
            fg_color=self._colors["secondary"],
            hover_color=self._colors["secondary_hover"],
            font=ctk.CTkFont(size=14)
        )
        run_btn.pack(side="left", padx=3)
        
        # Edit button
        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏️",
            command=lambda s=schedule: self._edit_schedule(s),
            width=40,
            height=40,
            corner_radius=10,
            fg_color=self._colors["surface_light"],
            hover_color=self._colors["border"],
            text_color=self._colors["text"],
            font=ctk.CTkFont(size=14)
        )
        edit_btn.pack(side="left", padx=3)
        
        # Delete button
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            command=lambda s=schedule: self._delete_schedule(s),
            width=40,
            height=40,
            corner_radius=10,
            fg_color=self._colors["danger"],
            hover_color=self._colors["danger_hover"],
            font=ctk.CTkFont(size=14)
        )
        delete_btn.pack(side="left", padx=3)
    
    def _add_schedule(self):
        """Open dialog to add new schedule."""
        ScheduleDialog(self._parent, self._, on_save=lambda s: self._refresh_list())
    
    def _edit_schedule(self, schedule: ScheduleConfig):
        """Open dialog to edit schedule."""
        ScheduleDialog(self._parent, self._, schedule=schedule, on_save=lambda s: self._refresh_list())
    
    def _run_now(self, schedule: ScheduleConfig):
        """Run schedule immediately."""
        self._scheduler.run_now(schedule.id)
        messagebox.showinfo(
            self._("app_title"),
            self._("scheduled_backup_started", name=schedule.name)
        )
    
    def _delete_schedule(self, schedule: ScheduleConfig):
        """Delete a schedule."""
        if messagebox.askyesno(
            self._("app_title"),
            self._("confirm_delete_schedule")
        ):
            self._scheduler.remove_schedule(schedule.id)
            self._refresh_list()
            messagebox.showinfo(self._("app_title"), self._("schedule_deleted"))
    
    def _on_close(self):
        """Handle dialog close."""
        self.grab_release()
        self.destroy()
