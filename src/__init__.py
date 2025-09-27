"""
Tekken 8 Replay Analysis Package

A comprehensive package for downloading, storing, and analyzing Tekken 8 replay data.
"""

__version__ = "2.0.0"
__author__ = "Tekken Replay Analysis Team"
__description__ = "Download and analyze Tekken 8 replay data with a modern GUI interface"

# Package imports
from .core.downloader import ReplayDownloader
from .core.analyzer import ReplayAnalyzer
from .core.database import DatabaseManager
from .gui.main_window import TekkenReplayGUI

__all__ = [
    "ReplayDownloader",
    "ReplayAnalyzer", 
    "DatabaseManager",
    "TekkenReplayGUI"
]
