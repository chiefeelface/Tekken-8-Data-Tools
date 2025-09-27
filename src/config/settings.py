"""
Application settings and configuration management.
"""

import json
import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # Date settings
    start_date: datetime.datetime = datetime.datetime(2025, 9, 1)
    end_date: datetime.datetime = datetime.datetime(2025, 9, 2)
    
    # Download settings
    max_replay_threshold: int = 1_000_000
    max_retries: int = 3
    request_delay: float = 1.005
    batch_size: int = 700
    
    # Storage settings
    use_sqlite: bool = True
    data_directory: str = "downloaded_replays"
    
    # API settings
    api_base_url: str = "https://wank.wavu.wiki/api/replays"
    api_timeout: int = 30
    
    # GUI settings
    window_width: int = 900
    window_height: int = 700
    
    # Analysis settings
    default_replay_file: str = "replay_data.csv"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration.
        """
        config_dict = asdict(self)
        
        # Convert datetime objects to ISO format strings
        config_dict['start_date'] = self.start_date.isoformat()
        config_dict['end_date'] = self.end_date.isoformat()
        
        return config_dict
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AppConfig':
        """Create configuration from dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values.
            
        Returns:
            AppConfig instance.
        """
        # Convert ISO format strings back to datetime objects
        if 'start_date' in config_dict and isinstance(config_dict['start_date'], str):
            config_dict['start_date'] = datetime.datetime.fromisoformat(config_dict['start_date'])
        
        if 'end_date' in config_dict and isinstance(config_dict['end_date'], str):
            config_dict['end_date'] = datetime.datetime.fromisoformat(config_dict['end_date'])
        
        return cls(**config_dict)


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from file.
    
    Args:
        config_path: Path to configuration file. Uses default if None.
        
    Returns:
        AppConfig instance.
    """
    if config_path is None:
        config_path = "config.json"
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        # Return default configuration
        return AppConfig()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        return AppConfig.from_dict(config_dict)
        
    except Exception as e:
        print(f"Failed to load configuration from {config_path}: {e}")
        return AppConfig()


def save_config(config: AppConfig, config_path: Optional[str] = None) -> None:
    """Save configuration to file.
    
    Args:
        config: Configuration to save.
        config_path: Path to configuration file. Uses default if None.
    """
    if config_path is None:
        config_path = "config.json"
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
        
        print(f"Configuration saved to {config_path}")
        
    except Exception as e:
        print(f"Failed to save configuration to {config_path}: {e}")
