"""
Backup scheduler for SmartBackup.
Manages scheduled/automated backup tasks with flexible scheduling options.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import json

from .config import get_config
from .backup_engine import get_backup_engine, BackupMode, BackupProgress, BackupResult


class ScheduleFrequency(Enum):
    """Backup schedule frequency options."""
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    CUSTOM = "custom"  # Custom days of week
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled backup."""
    id: str
    name: str
    source: str
    destination: str
    mode: str  # "full", "incremental", "differential"
    frequency: str  # ScheduleFrequency value
    enabled: bool = True
    
    # Time settings
    hour: int = 0  # 0-23
    minute: int = 0  # 0-59
    
    # Day settings
    days_of_week: List[int] = field(default_factory=lambda: [0])  # 0=Monday, 6=Sunday
    day_of_month: int = 1  # 1-31
    
    # Interval settings (for hourly)
    hour_interval: int = 1  # Every N hours
    
    # Compression and encryption settings
    compress: bool = False  # ZIP compression
    encrypt: bool = False  # AES encryption
    encryption_password: str = ""  # Password for encryption
    
    # Next run tracking
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    last_result: Optional[str] = None  # "success", "error", "cancelled"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "destination": self.destination,
            "mode": self.mode,
            "frequency": self.frequency,
            "enabled": self.enabled,
            "hour": self.hour,
            "minute": self.minute,
            "days_of_week": self.days_of_week,
            "day_of_month": self.day_of_month,
            "hour_interval": self.hour_interval,
            "compress": self.compress,
            "encrypt": self.encrypt,
            "encryption_password": self.encryption_password,
            "next_run": self.next_run,
            "last_run": self.last_run,
            "last_result": self.last_result,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduleConfig":
        # Handle legacy data with single day_of_week
        if "day_of_week" in data and "days_of_week" not in data:
            data["days_of_week"] = [data.pop("day_of_week")]
        # Set defaults for new fields
        if "hour_interval" not in data:
            data["hour_interval"] = 1
        if "days_of_week" not in data:
            data["days_of_week"] = [0]
        if "compress" not in data:
            data["compress"] = False
        if "encrypt" not in data:
            data["encrypt"] = False
        if "encryption_password" not in data:
            data["encryption_password"] = ""
        return cls(**data)


class BackupScheduler:
    """
    Manages scheduled backup tasks.
    Runs in background and executes backups at configured times.
    """
    
    SCHEDULES_KEY = "schedules"
    
    def __init__(self):
        self._config = get_config()
        self._engine = get_backup_engine()
        self._schedules: Dict[str, ScheduleConfig] = {}
        self._timer_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        self._on_backup_start: Optional[Callable[[ScheduleConfig], None]] = None
        self._on_backup_complete: Optional[Callable[[ScheduleConfig, BackupResult], None]] = None
        self._on_progress: Optional[Callable[[BackupProgress], None]] = None
        
        self._load_schedules()
    
    def _load_schedules(self) -> None:
        """Load schedules from configuration."""
        schedules_data = self._config.get(self.SCHEDULES_KEY, [])
        for item in schedules_data:
            try:
                schedule = ScheduleConfig.from_dict(item)
                self._schedules[schedule.id] = schedule
            except Exception:
                pass
    
    def _save_schedules(self) -> None:
        """Save schedules to configuration."""
        schedules_list = [s.to_dict() for s in self._schedules.values()]
        self._config.set(self.SCHEDULES_KEY, schedules_list)
    
    def set_callbacks(
        self,
        on_start: Optional[Callable[[ScheduleConfig], None]] = None,
        on_complete: Optional[Callable[[ScheduleConfig, BackupResult], None]] = None,
        on_progress: Optional[Callable[[BackupProgress], None]] = None
    ) -> None:
        """Set callback functions for backup events."""
        self._on_backup_start = on_start
        self._on_backup_complete = on_complete
        self._on_progress = on_progress
    
    def add_schedule(self, schedule: ScheduleConfig) -> None:
        """Add a new scheduled backup."""
        with self._lock:
            # Calculate next run time
            schedule.next_run = self._calculate_next_run(schedule)
            self._schedules[schedule.id] = schedule
            self._save_schedules()
    
    def update_schedule(self, schedule: ScheduleConfig) -> None:
        """Update an existing schedule."""
        with self._lock:
            schedule.next_run = self._calculate_next_run(schedule)
            self._schedules[schedule.id] = schedule
            self._save_schedules()
    
    def remove_schedule(self, schedule_id: str) -> None:
        """Remove a scheduled backup."""
        with self._lock:
            if schedule_id in self._schedules:
                del self._schedules[schedule_id]
                self._save_schedules()
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduleConfig]:
        """Get a schedule by ID."""
        return self._schedules.get(schedule_id)
    
    def get_all_schedules(self) -> List[ScheduleConfig]:
        """Get all scheduled backups."""
        return list(self._schedules.values())
    
    def toggle_schedule(self, schedule_id: str, enabled: bool) -> None:
        """Enable or disable a schedule."""
        with self._lock:
            if schedule_id in self._schedules:
                self._schedules[schedule_id].enabled = enabled
                if enabled:
                    self._schedules[schedule_id].next_run = self._calculate_next_run(
                        self._schedules[schedule_id]
                    )
                self._save_schedules()
    
    def _calculate_next_run(self, schedule: ScheduleConfig) -> str:
        """Calculate the next run time for a schedule."""
        now = datetime.now()
        
        if schedule.frequency == ScheduleFrequency.ONCE.value:
            # One-time backup - use configured time today or tomorrow
            target = now.replace(
                hour=schedule.hour, 
                minute=schedule.minute, 
                second=0, 
                microsecond=0
            )
            if target <= now:
                target += timedelta(days=1)
            return target.isoformat()
        
        elif schedule.frequency == ScheduleFrequency.HOURLY.value:
            # Next occurrence at configured minute, respecting interval
            target = now.replace(minute=schedule.minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(hours=1)
            # Adjust for interval
            if schedule.hour_interval > 1:
                hours_since_midnight = target.hour
                next_slot = ((hours_since_midnight // schedule.hour_interval) + 1) * schedule.hour_interval
                if next_slot >= 24:
                    target = target.replace(hour=0) + timedelta(days=1)
                else:
                    target = target.replace(hour=next_slot)
            return target.isoformat()
        
        elif schedule.frequency == ScheduleFrequency.DAILY.value:
            # Daily at configured time
            target = now.replace(
                hour=schedule.hour, 
                minute=schedule.minute, 
                second=0, 
                microsecond=0
            )
            if target <= now:
                target += timedelta(days=1)
            return target.isoformat()
        
        elif schedule.frequency == ScheduleFrequency.CUSTOM.value:
            # Custom days - find next matching day
            return self._find_next_custom_day(schedule, now)
        
        elif schedule.frequency == ScheduleFrequency.WEEKLY.value:
            # Weekly on first configured day
            if schedule.days_of_week:
                day = schedule.days_of_week[0]
            else:
                day = 0
            target = now.replace(
                hour=schedule.hour, 
                minute=schedule.minute, 
                second=0, 
                microsecond=0
            )
            days_ahead = day - now.weekday()
            if days_ahead < 0 or (days_ahead == 0 and target <= now):
                days_ahead += 7
            target += timedelta(days=days_ahead)
            return target.isoformat()
        
        elif schedule.frequency == ScheduleFrequency.MONTHLY.value:
            # Monthly on configured day and time
            target = now.replace(
                day=min(schedule.day_of_month, 28),  # Safe for all months
                hour=schedule.hour, 
                minute=schedule.minute, 
                second=0, 
                microsecond=0
            )
            if target <= now:
                # Move to next month
                if now.month == 12:
                    target = target.replace(year=now.year + 1, month=1)
                else:
                    target = target.replace(month=now.month + 1)
            return target.isoformat()
        
        return now.isoformat()
    
    def _find_next_custom_day(self, schedule: ScheduleConfig, now: datetime) -> str:
        """Find the next run time for custom day schedule."""
        if not schedule.days_of_week:
            return now.isoformat()
        
        target_time = now.replace(
            hour=schedule.hour,
            minute=schedule.minute,
            second=0,
            microsecond=0
        )
        
        # Check each day for the next 8 days
        for day_offset in range(8):
            check_date = now + timedelta(days=day_offset)
            check_day = check_date.weekday()
            
            if check_day in schedule.days_of_week:
                candidate = check_date.replace(
                    hour=schedule.hour,
                    minute=schedule.minute,
                    second=0,
                    microsecond=0
                )
                if candidate > now:
                    return candidate.isoformat()
        
        # Fallback: next week's first configured day
        first_day = min(schedule.days_of_week)
        days_ahead = first_day - now.weekday() + 7
        target = target_time + timedelta(days=days_ahead)
        return target.isoformat()
    
    def start(self) -> None:
        """Start the scheduler background thread."""
        if self._running:
            return
        
        self._running = True
        self._timer_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._timer_thread.start()
    
    def stop(self) -> None:
        """Stop the scheduler background thread."""
        self._running = False
        if self._timer_thread:
            self._timer_thread.join(timeout=2)
            self._timer_thread = None
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop - checks for due backups every minute."""
        while self._running:
            try:
                self._check_and_run_due_backups()
            except Exception as e:
                print(f"Scheduler error: {e}")
            
            # Sleep for 30 seconds before next check
            for _ in range(30):
                if not self._running:
                    break
                time.sleep(1)
    
    def _check_and_run_due_backups(self) -> None:
        """Check for and execute any due backups."""
        now = datetime.now()
        
        with self._lock:
            schedules_to_run = []
            for schedule in self._schedules.values():
                if not schedule.enabled or not schedule.next_run:
                    continue
                
                try:
                    next_run = datetime.fromisoformat(schedule.next_run)
                    if next_run <= now:
                        schedules_to_run.append(schedule)
                except Exception:
                    pass
        
        # Run due backups (outside lock to avoid blocking)
        for schedule in schedules_to_run:
            self._run_scheduled_backup(schedule)
    
    def _run_scheduled_backup(self, schedule: ScheduleConfig) -> None:
        """Execute a scheduled backup."""
        # Notify start
        if self._on_backup_start:
            self._on_backup_start(schedule)
        
        # Run backup
        mode = BackupMode(schedule.mode)
        result = self._engine.run_backup(
            schedule.source,
            schedule.destination,
            mode,
            self._on_progress
        )
        
        # Apply compression and/or encryption if backup was successful
        if result.success and result.backup_folder and (schedule.compress or schedule.encrypt):
            try:
                from .backup_utils import compress_folder, encrypt_file
                import shutil
                import os
                
                backup_path = result.backup_folder
                
                if schedule.compress or schedule.encrypt:
                    # Always create a zip for compression or encryption
                    zip_path = backup_path + ".zip"
                    compress_folder(backup_path, zip_path)
                    
                    if schedule.encrypt and schedule.encryption_password:
                        # Encrypt the zip file
                        enc_path = backup_path + ".zip.enc"
                        encrypt_file(zip_path, enc_path, schedule.encryption_password)
                        os.remove(zip_path)  # Remove unencrypted zip
                    
                    # Remove original backup folder since we have compressed/encrypted version
                    shutil.rmtree(backup_path)
            except Exception as e:
                print(f"Post-processing error: {e}")
        
        # Update schedule
        with self._lock:
            schedule.last_run = datetime.now().isoformat()
            schedule.last_result = "success" if result.success else "error"
            
            # Calculate next run (except for one-time backups)
            if schedule.frequency != ScheduleFrequency.ONCE.value:
                schedule.next_run = self._calculate_next_run(schedule)
            else:
                schedule.enabled = False  # Disable one-time after run
            
            self._save_schedules()
        
        # Notify complete
        if self._on_backup_complete:
            self._on_backup_complete(schedule, result)
    
    def run_now(self, schedule_id: str) -> bool:
        """Manually trigger a scheduled backup to run now."""
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return False
        
        # Run in background thread
        thread = threading.Thread(
            target=self._run_scheduled_backup,
            args=(schedule,),
            daemon=True
        )
        thread.start()
        return True
    
    def generate_schedule_id(self) -> str:
        """Generate a unique schedule ID."""
        import uuid
        return str(uuid.uuid4())[:8]


# Global scheduler instance
_scheduler: Optional[BackupScheduler] = None


def get_scheduler() -> BackupScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackupScheduler()
    return _scheduler
