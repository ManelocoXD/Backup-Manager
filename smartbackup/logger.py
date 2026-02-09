"""
Logging configuration for SmartBackup.
Writes logs to 'smartbackup.log' in the config directory.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import get_config

_logger: Optional[logging.Logger] = None

def get_logger() -> logging.Logger:
    """Get the global logger instance."""
    global _logger
    
    if _logger is not None:
        return _logger
        
    _logger = logging.getLogger("SmartBackup")
    _logger.setLevel(logging.INFO)
    
    # Avoid adding handlers multiple times
    if _logger.hasHandlers():
        return _logger

    try:
        config = get_config()
        log_file = config.config_dir / "smartbackup.log"
        
        # Rotating file handler (1MB max, 5 backups)
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=1024*1024, 
            backupCount=5, 
            encoding="utf-8"
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        _logger.addHandler(file_handler)
        
        # Console handler (optional, good for dev)
        # console_handler = logging.StreamHandler(sys.stdout)
        # console_handler.setFormatter(file_formatter)
        # _logger.addHandler(console_handler)
        
    except Exception as e:
        # Fallback if config/fs fails
        print(f"Failed to setup logging: {e}")
        
    return _logger
