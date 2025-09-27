"""
Configuration management for the Tekken replay analyzer.
"""

from .settings import AppConfig, load_config, save_config

__all__ = [
    "AppConfig",
    "load_config", 
    "save_config"
]
