"""
Main GUI window for the Tekken replay downloader.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import datetime
import time
import logging
from typing import Optional
import queue

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.downloader import ReplayDownloader, DownloadConfig
from core.api_client import APIConfig
from config.settings import AppConfig
from gui.components import DatePickerFrame, SettingsFrame, ProgressFrame, LogFrame, ControlFrame

logger = logging.getLogger(__name__)


class TekkenReplayGUI:
    """Main GUI application for Tekken replay downloading."""
    
    def __init__(self, root: tk.Tk, config: Optional[AppConfig] = None):
        """Initialize the GUI application.
        
        Args:
            root: Tkinter root window.
            config: Application configuration.
        """
        self.root = root
        self.config = config or AppConfig()
        
        # Window setup
        self.root.title("Tekken 8 Replay Downloader")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Enable HiDPI scaling
        try:
            import platform
            if platform.system() == "Windows":
                # Windows HiDPI scaling - set DPI awareness before creating widgets
                try:
                    import ctypes
                    # Set DPI awareness to system DPI aware
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)
                except:
                    pass
        except:
            pass  # Fallback if scaling not supported
        
        # Download state
        self.download_thread: Optional[threading.Thread] = None
        self.is_downloading = False
        self.stop_download = False
        
        # Time tracking for ETA
        self.download_start_time: Optional[float] = None
        self.last_progress_time: Optional[float] = None
        self.last_progress_value: int = 0
        
        # Queue for thread-safe GUI updates
        self.log_queue = queue.Queue()
        
        # Create GUI components
        self._create_widgets()
        self._setup_layout()
        
        # Start checking the log queue
        self._check_log_queue()
    
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="15")
        
        # Title
        self.title_label = ttk.Label(
            self.main_frame, 
            text="Tekken 8 Replay Downloader", 
            font=("Arial", 18, "bold")
        )
        
        # Create component frames
        self.date_frame = DatePickerFrame(self.main_frame, self.config)
        self.settings_frame = SettingsFrame(self.main_frame, self.config)
        self.progress_frame = ProgressFrame(self.main_frame)
        self.log_frame = LogFrame(self.main_frame)
        self.control_frame = ControlFrame(
            self.main_frame,
            on_start=self._start_download,
            on_stop=self._stop_download,
            on_clear=self._clear_logs
        )
    
    def _setup_layout(self):
        """Arrange widgets in the window."""
        # Pack the main frame to the root window
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(4, weight=1)
        
        # Title
        self.title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Component frames
        self.date_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.settings_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        self.control_frame.grid(row=5, column=0, pady=(10, 0))
    
    def _check_log_queue(self):
        """Check for new log messages and update the GUI."""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_frame.add_message(message)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._check_log_queue)
    
    def _log_message(self, message: str):
        """Add a message to the log display (thread-safe)."""
        # Standardize log message format
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_queue.put(formatted_message)
    
    def _clear_logs(self):
        """Clear the log display."""
        self.log_frame.clear()
    
    def _validate_dates(self) -> tuple[datetime.datetime, datetime.datetime]:
        """Validate and parse the date inputs."""
        try:
            start_date, end_date = self.date_frame.get_dates()
            
            if start_date >= end_date:
                raise ValueError("Start date must be before end date")
            
            return start_date, end_date
            
        except ValueError as e:
            messagebox.showerror("Invalid Date", f"Please select valid dates.\nError: {e}")
            raise
    
    def _update_progress(self, current: int, total: int, message: str = ""):
        """Update the progress bar, label, and ETA."""
        current_time = time.time()
        
        if total > 0:
            progress = (current / total) * 100
            self.progress_frame.set_progress(progress)
            
            # Calculate ETA
            eta_text = self._calculate_eta(current, total, current_time)
            self.progress_frame.set_eta(eta_text)
        
        if message:
            self.progress_frame.set_status(message)
        else:
            self.progress_frame.set_status(f"Progress: {current}/{total} ({progress:.1f}%)")
    
    def _calculate_eta(self, current: int, total: int, current_time: float) -> str:
        """Calculate and format estimated time remaining."""
        if current <= 0 or total <= 0:
            return ""
        
        # Initialize timing on first progress update
        if self.download_start_time is None:
            self.download_start_time = current_time
            self.last_progress_time = current_time
            self.last_progress_value = current
            return "Calculating ETA..."
        
        # Calculate ETA based on recent progress
        if (current > self.last_progress_value and 
            self.last_progress_time is not None and 
            current_time > self.last_progress_time):
            # Time elapsed since last update
            time_elapsed = current_time - self.last_progress_time
            # Progress made since last update
            progress_made = current - self.last_progress_value
            
            if progress_made > 0 and time_elapsed > 0:
                # Rate of progress (sets per second)
                progress_rate = progress_made / time_elapsed
                # Remaining work
                remaining_work = total - current
                # Estimated time remaining
                eta_seconds = remaining_work / progress_rate
                
                # Update tracking variables
                self.last_progress_time = current_time
                self.last_progress_value = current
                
                return self._format_time(eta_seconds)
        
        # Fallback: calculate based on overall progress
        if self.download_start_time is not None:
            total_elapsed = current_time - self.download_start_time
            if current > 0 and total_elapsed > 0:
                # Overall rate
                overall_rate = current / total_elapsed
                remaining_work = total - current
                eta_seconds = remaining_work / overall_rate
                return self._format_time(eta_seconds)
        
        return "Calculating ETA..."
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into a human-readable time string."""
        if seconds < 60:
            return f"ETA: {int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"ETA: {minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"ETA: {hours}h {minutes}m"
    
    def _start_download(self):
        """Start the download process in a separate thread."""
        try:
            start_date, end_date = self._validate_dates()
            
            # Update GUI state
            self.is_downloading = True
            self.stop_download = False
            self.control_frame.set_downloading(True)
            self.progress_frame.reset()
            
            # Reset timing variables
            self.download_start_time = None
            self.last_progress_time = None
            self.last_progress_value = 0
            
            # Create downloader with callbacks
            api_config = APIConfig(
                max_retries=self.config.max_retries,
                request_delay=self.config.request_delay
            )
            
            download_config = DownloadConfig(
                max_replay_threshold=self.config.max_replay_threshold,
                use_sqlite=self.config.use_sqlite,
                progress_callback=self._update_progress,
                log_callback=self._log_message,
                stop_callback=lambda: self.stop_download
            )
            
            # Start download thread
            self.download_thread = threading.Thread(
                target=self._download_worker,
                args=(start_date, end_date, api_config, download_config),
                daemon=True
            )
            self.download_thread.start()
            
        except ValueError:
            # Date validation failed
            pass
    
    def _stop_download(self):
        """Stop the current download process."""
        self.stop_download = True
        self._log_message("Stopping download process...")
    
    def _download_worker(
        self, 
        start_date: datetime.datetime, 
        end_date: datetime.datetime,
        api_config: APIConfig,
        download_config: DownloadConfig
    ):
        """Worker thread for downloading replays."""
        try:
            self._log_message(f"Starting download from {start_date.date()} to {end_date.date()}")
            
            # Create downloader
            downloader = ReplayDownloader(api_config, download_config)
            
            # Download data
            downloaded_replays = downloader.download_replay_data(start_date, end_date)
            
            if not self.stop_download:
                self._log_message(f"Download completed successfully: {downloaded_replays:,} replays")
                self._update_progress(100, 100, "Download completed!")
            else:
                self._log_message(f"Download stopped by user: {downloaded_replays:,} replays saved")
                self._update_progress(100, 100, "Download stopped and saved!")
            
            # Clean up
            downloader.close()
            
        except Exception as e:
            self._log_message(f"Download error: {str(e)}")
            messagebox.showerror("Download Error", f"An error occurred during download:\n{str(e)}")
        
        finally:
            # Reset GUI state
            self.is_downloading = False
            self.download_start_time = None
            self.last_progress_time = None
            self.last_progress_value = 0
            self.root.after(0, self._reset_download_ui)
    
    def _reset_download_ui(self):
        """Reset the download UI state."""
        self.control_frame.set_downloading(False)
        if not self.is_downloading:
            self.progress_frame.set_status("Ready to download")
            self.progress_frame.set_eta("")
    
    def run(self):
        """Start the GUI application."""
        # Handle window closing
        def on_closing():
            if self.is_downloading:
                if messagebox.askokcancel("Quit", "Download in progress. Do you want to quit?"):
                    self.stop_download = True
                    self.root.destroy()
            else:
                self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the GUI
        self.root.mainloop()
