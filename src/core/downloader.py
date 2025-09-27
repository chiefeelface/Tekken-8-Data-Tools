"""
Core downloader for Tekken replay data.
"""

import math
import time
import datetime
import logging
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass

from .api_client import APIClient, APIConfig
from .database import DatabaseManager
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.replay_data import ReplayData

logger = logging.getLogger(__name__)


@dataclass
class DownloadConfig:
    """Configuration for replay downloads."""
    max_replay_threshold: int = 1_000_000
    use_sqlite: bool = True
    progress_callback: Optional[Callable[[int, int, str], None]] = None
    log_callback: Optional[Callable[[str], None]] = None
    stop_callback: Optional[Callable[[], bool]] = None


class ReplayDownloader:
    """Downloads Tekken replay data from the API and stores it."""
    
    def __init__(
        self, 
        api_config: Optional[APIConfig] = None,
        download_config: Optional[DownloadConfig] = None
    ):
        """Initialize the replay downloader.
        
        Args:
            api_config: API client configuration.
            download_config: Download configuration.
        """
        self.api_client = APIClient(api_config)
        self.db_manager = DatabaseManager()
        self.config = download_config or DownloadConfig()
    
    def calculate_loops_required(
        self, 
        start_date: datetime.datetime, 
        end_date: datetime.datetime
    ) -> int:
        """Calculate the number of API calls needed.
        
        Args:
            start_date: Start date for downloads.
            end_date: End date for downloads.
            
        Returns:
            Number of API calls required.
        """
        start_ts = math.trunc(start_date.timestamp())
        end_ts = math.trunc((end_date + datetime.timedelta(days=1)).timestamp())
        return math.ceil((end_ts - start_ts) / self.api_client.config.batch_size)
    
    def download_replay_data(
        self, 
        start_date: datetime.datetime, 
        end_date: datetime.datetime
    ) -> int:
        """Download all replay data for the specified date range.
        
        Args:
            start_date: Start date for downloads.
            end_date: End date for downloads.
            
        Returns:
            Total number of replays downloaded.
        """
        total_replays = 0
        replays: List[ReplayData] = []
        
        # Calculate timing parameters
        start_ts = math.trunc(start_date.timestamp())
        end_ts = math.trunc((end_date + datetime.timedelta(days=1)).timestamp())
        loops_required = self.calculate_loops_required(start_date, end_date)
        before_ts = math.trunc(end_ts)
        
        # Initialize database if using SQLite
        if self.config.use_sqlite:
            self.db_manager.create_tables(start_date, end_date)
            self.db_manager.populate_lookup_tables(start_date, end_date)
        
        self._log_message(f'Starting download of {loops_required:,} sets of replays')
        
        for i in range(loops_required + 1):
            # Check for stop signal
            if self.config.stop_callback and self.config.stop_callback():
                self._log_message("Stop signal received, saving current data...")
                break
            
            start_time = time.perf_counter()
            
            # Update progress
            progress_message = f"Downloading set {i + 1} of {loops_required:,}"
            self._update_progress(i, loops_required, progress_message)
            
            # Download replays with retry logic
            downloaded = self.api_client.download_replays_with_retry(
                before_ts, i + 1, loops_required
            )
            
            if downloaded:
                replays.extend(downloaded)
                total_replays += len(downloaded)
                # Log each set download
                self._log_message(f"Set {i + 1}/{loops_required}: Downloaded {len(downloaded)} replays (Total: {total_replays:,})")
            else:
                self._log_message(f"Set {i + 1}/{loops_required}: Failed to download (skipped)")
            
            before_ts -= self.api_client.config.batch_size
            
            # Save data if threshold is reached
            if len(replays) > self.config.max_replay_threshold:
                self._log_message(f"Saving {len(replays):,} replays to {'database' if self.config.use_sqlite else 'CSV'}...")
                self.db_manager.save_replay_data(replays, start_date, end_date, self.config.use_sqlite)
                del replays[:]
                self._log_message("Data saved successfully")
            
            # Rate limiting
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time - 0.005 < self.api_client.config.request_delay:
                time.sleep(self.api_client.config.request_delay - elapsed_time + 0.005)
        
        # Save any remaining data
        if replays:
            self._log_message(f"Saving final {len(replays):,} replays to {'database' if self.config.use_sqlite else 'CSV'}...")
            self.db_manager.save_replay_data(replays, start_date, end_date, self.config.use_sqlite)
            self._log_message("Final data saved successfully")
        
        self._log_message(f'Download completed: {total_replays:,} replays downloaded')
        return total_replays
    
    def _update_progress(self, current: int, total: int, message: str = "") -> None:
        """Update progress if callback is provided."""
        if self.config.progress_callback:
            self.config.progress_callback(current, total, message)
    
    def _log_message(self, message: str) -> None:
        """Log message if callback is provided."""
        if self.config.log_callback:
            self.config.log_callback(message)
        logger.info(message)
    
    def close(self):
        """Close the API client."""
        self.api_client.close()
