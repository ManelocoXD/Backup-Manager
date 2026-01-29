"""
Configuration management for SmartBackup.
Handles cross-platform paths and application settings.
"""

import os
import sys
import json
import locale
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Manages application configuration with cross-platform support."""
    
    APP_NAME = "SmartBackup"
    CONFIG_FILE = "config.json"
    
    def __init__(self):
        self._config_dir = self._get_config_dir()
        self._config_file = self._config_dir / self.CONFIG_FILE
        self._settings: Dict[str, Any] = {}
        self._load()
    
    def _get_config_dir(self) -> Path:
        """Get the appropriate config directory for the current platform."""
        if sys.platform == "win32":
            # Windows: Use AppData/Local
            base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
            config_dir = Path(base) / self.APP_NAME
        else:
            # Linux/macOS: Use ~/.config
            base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            config_dir = Path(base) / self.APP_NAME.lower()
        
        # Ensure directory exists
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Return default application settings."""
        return {
            "language": self._detect_language(),
            "theme": "system",  # "system", "dark", "light"
            "last_source": "",
            "last_destination": "",
            "last_mode": "full",  # "full", "incremental", "differential"
            "show_notifications": True,
            "confirm_before_backup": True,
            "enable_compression": False,
            "enable_encryption": False,
            "encryption_password": "",
        }
    
    def _detect_language(self) -> str:
        """Detect system language and return 'es' or 'en'."""
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale and system_locale.startswith("es"):
                return "es"
        except Exception:
            pass
        return "en"
    
    def _load(self) -> None:
        """Load configuration from file or create defaults."""
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # Merge with defaults to handle new settings
                self._settings = {**self._get_default_settings(), **saved}
            except (json.JSONDecodeError, IOError):
                self._settings = self._get_default_settings()
        else:
            self._settings = self._get_default_settings()
            self._save()
    
    def _save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save config: {e}")
    
    def save(self) -> None:
        """Public method to save configuration."""
        self._save()
    
    @property
    def config_dir(self) -> Path:
        """Get the configuration directory path."""
        return self._config_dir
    
    @property
    def database_path(self) -> Path:
        """Get the database file path."""
        return self._config_dir / "smartbackup.db"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save."""
        self._settings[key] = value
        self._save()
    
    def update(self, settings: Dict[str, Any]) -> None:
        """Update multiple settings at once."""
        self._settings.update(settings)
        self._save()
    
    @property
    def language(self) -> str:
        return self.get("language", "en")
    
    @language.setter
    def language(self, value: str) -> None:
        self.set("language", value)
    
    @property
    def theme(self) -> str:
        return self.get("theme", "system")
    
    @theme.setter
    def theme(self, value: str) -> None:
        self.set("theme", value)
    
    @property
    def last_source(self) -> str:
        return self.get("last_source", "")
    
    @last_source.setter
    def last_source(self, value: str) -> None:
        self.set("last_source", value)
    
    @property
    def last_destination(self) -> str:
        return self.get("last_destination", "")
    
    @last_destination.setter
    def last_destination(self, value: str) -> None:
        self.set("last_destination", value)
    
    @property
    def last_mode(self) -> str:
        return self.get("last_mode", "full")
    
    @last_mode.setter
    def last_mode(self, value: str) -> None:
        self.set("last_mode", value)
    
    @property
    def enable_compression(self) -> bool:
        return self.get("enable_compression", False)
    
    @enable_compression.setter
    def enable_compression(self, value: bool) -> None:
        self._settings["enable_compression"] = value
    
    @property
    def enable_encryption(self) -> bool:
        return self.get("enable_encryption", False)
    
    @enable_encryption.setter
    def enable_encryption(self, value: bool) -> None:
        self._settings["enable_encryption"] = value
    
    @property
    def encryption_password(self) -> str:
        return self.get("encryption_password", "")
    
    @encryption_password.setter
    def encryption_password(self, value: str) -> None:
        self._settings["encryption_password"] = value


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

