"""
Configuration management for the Personal Finance CLI application.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from utils.logger import get_logger


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    path: str = "finance_data.db"
    backup_interval_hours: int = 24
    max_backups: int = 30
    enable_wal_mode: bool = True


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    enable_encryption: bool = False
    password_hash: Optional[str] = None
    session_timeout_minutes: int = 60
    max_login_attempts: int = 3


@dataclass
class NotificationConfig:
    """Notification configuration settings."""
    enable_budget_alerts: bool = True
    enable_goal_reminders: bool = True
    budget_threshold_percentage: float = 80.0
    reminder_frequency_days: int = 7


@dataclass
class UIConfig:
    """User interface configuration settings."""
    theme: str = "default"
    currency_symbol: str = "$"
    date_format: str = "%Y-%m-%d"
    decimal_places: int = 2
    show_colors: bool = True


@dataclass
class PerformanceConfig:
    """Performance configuration settings."""
    enable_caching: bool = True
    cache_size_mb: int = 50
    enable_async_operations: bool = True
    max_concurrent_operations: int = 10


class Config:
    """Main configuration class for the application."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.logger = get_logger(__name__)
        
        # Initialize configuration sections
        self.database = DatabaseConfig()
        self.security = SecurityConfig()
        self.notifications = NotificationConfig()
        self.ui = UIConfig()
        self.performance = PerformanceConfig()
        
        # Application settings
        self.app_name = "Advanced Personal Finance CLI"
        self.version = "2.0.0"
        self.data_directory = Path("finance_data")
        self.log_directory = Path("logs")
        self.backup_directory = Path("backups")
        
        # Load configuration from file
        self.load_config()
        
        # Ensure directories exist
        self._create_directories()
    
    @property
    def database_path(self) -> str:
        """Get the full database path."""
        return str(self.data_directory / self.database.path)
    
    @property
    def auto_backup_enabled(self) -> bool:
        """Check if auto-backup is enabled."""
        return self.database.backup_interval_hours > 0
    
    def load_config(self):
        """Load configuration from JSON file."""
        if not self.config_file.exists():
            self.logger.info(f"Config file {self.config_file} not found, using defaults")
            self.save_config()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Update configuration sections
            if 'database' in config_data:
                self.database = DatabaseConfig(**config_data['database'])
            
            if 'security' in config_data:
                self.security = SecurityConfig(**config_data['security'])
            
            if 'notifications' in config_data:
                self.notifications = NotificationConfig(**config_data['notifications'])
            
            if 'ui' in config_data:
                self.ui = UIConfig(**config_data['ui'])
            
            if 'performance' in config_data:
                self.performance = PerformanceConfig(**config_data['performance'])
            
            # Update application settings
            for key in ['app_name', 'version', 'data_directory', 'log_directory', 'backup_directory']:
                if key in config_data:
                    if key.endswith('_directory'):
                        setattr(self, key, Path(config_data[key]))
                    else:
                        setattr(self, key, config_data[key])
            
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.logger.info("Using default configuration")
    
    def save_config(self):
        """Save current configuration to JSON file."""
        try:
            config_data = {
                'database': asdict(self.database),
                'security': asdict(self.security),
                'notifications': asdict(self.notifications),
                'ui': asdict(self.ui),
                'performance': asdict(self.performance),
                'app_name': self.app_name,
                'version': self.version,
                'data_directory': str(self.data_directory),
                'log_directory': str(self.log_directory),
                'backup_directory': str(self.backup_directory),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_directory,
            self.log_directory,
            self.backup_directory
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def update_setting(self, section: str, key: str, value: Any):
        """Update a specific configuration setting."""
        try:
            section_obj = getattr(self, section)
            if hasattr(section_obj, key):
                setattr(section_obj, key, value)
                self.save_config()
                self.logger.info(f"Updated {section}.{key} = {value}")
            else:
                raise ValueError(f"Invalid setting: {section}.{key}")
        except Exception as e:
            self.logger.error(f"Error updating setting: {e}")
            raise
    
    def get_setting(self, section: str, key: str) -> Any:
        """Get a specific configuration setting."""
        try:
            section_obj = getattr(self, section)
            return getattr(section_obj, key)
        except Exception as e:
            self.logger.error(f"Error getting setting: {e}")
            return None
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.database = DatabaseConfig()
        self.security = SecurityConfig()
        self.notifications = NotificationConfig()
        self.ui = UIConfig()
        self.performance = PerformanceConfig()
        
        self.save_config()
        self.logger.info("Configuration reset to defaults")
