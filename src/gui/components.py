"""
GUI components for the Tekken replay downloader.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import datetime
from typing import Callable, Optional

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import AppConfig


class DatePickerFrame(ttk.LabelFrame):
    """Frame containing date selection widgets."""
    
    def __init__(self, parent, config: AppConfig):
        """Initialize the date picker frame.
        
        Args:
            parent: Parent widget.
            config: Application configuration.
        """
        super().__init__(parent, text="Date Range", padding="15")
        
        self.config = config
        
        # Configure grid
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create date picker widgets."""
        # Start date
        self.start_date_label = ttk.Label(self, text="Start Date:")
        
        # End date
        self.end_date_label = ttk.Label(self, text="End Date:")
        
        # Date picker widgets
        if DateEntry is not None:
            # Use tkcalendar DateEntry widgets with calendar icon
            self.start_date_picker = DateEntry(
                self,
                date_pattern='yyyy-mm-dd',
                width=12,
                background='darkblue',
                foreground='white',
                borderwidth=2,
                year=self.config.start_date.year,
                month=self.config.start_date.month,
                day=self.config.start_date.day,
                showothermonthdays=False,
                firstweekday='sunday'
            )
            
            self.end_date_picker = DateEntry(
                self,
                date_pattern='yyyy-mm-dd',
                width=12,
                background='darkblue',
                foreground='white',
                borderwidth=2,
                year=self.config.end_date.year,
                month=self.config.end_date.month,
                day=self.config.end_date.day,
                showothermonthdays=False,
                firstweekday='sunday'
            )
            
            # Calendar icons don't work reliably, so we'll use the default appearance
            
            # Help text
            self.help_label = ttk.Label(
                self, 
                text="Click the date picker buttons to select dates", 
                font=("Arial", 9)
            )
        else:
            # Fallback to text entry
            self.start_date_var = tk.StringVar(value=self.config.start_date.strftime("%Y-%m-%d"))
            self.start_date_picker = ttk.Entry(self, textvariable=self.start_date_var, width=12)
            
            self.end_date_var = tk.StringVar(value=self.config.end_date.strftime("%Y-%m-%d"))
            self.end_date_picker = ttk.Entry(self, textvariable=self.end_date_var, width=12)
            
            # Help text
            self.help_label = ttk.Label(
                self, 
                text="Format: YYYY-MM-DD (e.g., 2025-09-01) - Install tkcalendar for calendar picker", 
                font=("Arial", 9)
            )
    
    def _setup_layout(self):
        """Arrange widgets in the frame."""
        self.start_date_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.start_date_picker.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 30))
        
        self.end_date_label.grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.end_date_picker.grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        self.help_label.grid(row=1, column=0, columnspan=4, pady=(10, 0))
    
    def get_dates(self) -> tuple[datetime.datetime, datetime.datetime]:
        """Get the selected dates.
        
        Returns:
            Tuple of (start_date, end_date) as datetime objects.
        """
        if DateEntry is not None:
            # Use DateEntry widgets
            start_date_obj = self.start_date_picker.get_date()  # type: ignore
            end_date_obj = self.end_date_picker.get_date()  # type: ignore
            
            # Convert datetime.date to datetime.datetime (at midnight)
            start_date = datetime.datetime.combine(start_date_obj, datetime.time.min)
            end_date = datetime.datetime.combine(end_date_obj, datetime.time.min)
        else:
            # Fallback to text entry parsing
            start_date = datetime.datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            end_date = datetime.datetime.strptime(self.end_date_var.get(), "%Y-%m-%d")
        
        return start_date, end_date


class SettingsFrame(ttk.LabelFrame):
    """Frame containing application settings."""
    
    def __init__(self, parent, config: AppConfig):
        """Initialize the settings frame.
        
        Args:
            parent: Parent widget.
            config: Application configuration.
        """
        super().__init__(parent, text="Settings", padding="15")
        
        self.config = config
        
        # Configure grid
        self.columnconfigure(1, weight=1)
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create settings widgets."""
        # Storage type
        self.storage_label = ttk.Label(self, text="Storage Type:")
        self.storage_var = tk.StringVar(value="SQLite Database" if self.config.use_sqlite else "CSV File")
        self.storage_combo = ttk.Combobox(
            self,
            textvariable=self.storage_var,
            values=["SQLite Database", "CSV File"],
            state="readonly",
            width=15
        )
        
        # Bind change event
        self.storage_combo.bind('<<ComboboxSelected>>', self._on_storage_change)
    
    def _setup_layout(self):
        """Arrange widgets in the frame."""
        self.storage_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.storage_combo.grid(row=0, column=1, sticky=tk.W)
    
    def _on_storage_change(self, event):
        """Handle storage type change."""
        selection = self.storage_var.get()
        self.config.use_sqlite = (selection == "SQLite Database")
    
    def get_storage_type(self) -> str:
        """Get the selected storage type."""
        return self.storage_var.get()


class ProgressFrame(ttk.LabelFrame):
    """Frame containing progress bar and status information."""
    
    def __init__(self, parent):
        """Initialize the progress frame.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent, text="Download Progress", padding="15")
        
        self.columnconfigure(0, weight=1)
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create progress widgets."""
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self,
            variable=self.progress_var,
            maximum=100,
            length=500,
            mode='determinate'
        )
        
        # Status label
        self.status_label = ttk.Label(self, text="Ready to download")
        
        # ETA label
        self.eta_label = ttk.Label(self, text="", font=("Arial", 10))
    
    def _setup_layout(self):
        """Arrange widgets in the frame."""
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.eta_label.grid(row=2, column=0, sticky=tk.W)
    
    def set_progress(self, value: float):
        """Set the progress bar value.
        
        Args:
            value: Progress value (0-100).
        """
        self.progress_var.set(value)
    
    def set_status(self, text: str):
        """Set the status label text.
        
        Args:
            text: Status text.
        """
        self.status_label.config(text=text)
    
    def set_eta(self, text: str):
        """Set the ETA label text.
        
        Args:
            text: ETA text.
        """
        self.eta_label.config(text=text)
    
    def reset(self):
        """Reset the progress frame."""
        self.progress_var.set(0)
        self.status_label.config(text="Starting download...")
        self.eta_label.config(text="")


class LogFrame(ttk.LabelFrame):
    """Frame containing log display."""
    
    def __init__(self, parent):
        """Initialize the log frame.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent, text="Status & Logs", padding="15")
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create log widgets."""
        # Create a frame to hold text and scrollbar
        self.text_frame = tk.Frame(self)
        
        # Log text area
        self.log_text = tk.Text(
            self.text_frame,
            height=15,
            width=80,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 9),
            bg='white',
            fg='black',
            selectbackground='lightblue',
            selectforeground='black',
            insertbackground='black',
            relief=tk.SUNKEN,
            borderwidth=1
        )
        
        # Custom scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.text_frame,
            orient=tk.VERTICAL,
            command=self.log_text.yview
        )
        
        # Configure text widget to use scrollbar
        self.log_text.configure(yscrollcommand=self.scrollbar.set)
    
    def _setup_layout(self):
        """Arrange widgets in the frame."""
        # Pack the text frame
        self.text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid for text and scrollbar
        self.text_frame.grid_rowconfigure(0, weight=1)
        self.text_frame.grid_columnconfigure(0, weight=1)
        
        # Place text and scrollbar side by side
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
    def add_message(self, message: str):
        """Add a message to the log.
        
        Args:
            message: Message to add.
        """
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear(self):
        """Clear the log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)


class ControlFrame(ttk.Frame):
    """Frame containing control buttons."""
    
    def __init__(
        self, 
        parent, 
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
        on_clear: Callable[[], None]
    ):
        """Initialize the control frame.
        
        Args:
            parent: Parent widget.
            on_start: Callback for start button.
            on_stop: Callback for stop button.
            on_clear: Callback for clear button.
        """
        super().__init__(parent)
        
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_clear = on_clear
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create control widgets."""
        # Download button
        self.download_button = ttk.Button(
            self,
            text="Start Download",
            command=self.on_start,
            style="Accent.TButton"
        )
        
        # Stop button
        self.stop_button = ttk.Button(
            self,
            text="Stop Download",
            command=self.on_stop,
            state=tk.DISABLED
        )
        
        # Clear logs button
        self.clear_button = ttk.Button(
            self,
            text="Clear Logs",
            command=self.on_clear
        )
    
    def _setup_layout(self):
        """Arrange widgets in the frame."""
        self.download_button.grid(row=0, column=0, padx=(0, 15))
        self.stop_button.grid(row=0, column=1, padx=(0, 15))
        self.clear_button.grid(row=0, column=2)
    
    def set_downloading(self, is_downloading: bool):
        """Set the downloading state.
        
        Args:
            is_downloading: Whether a download is in progress.
        """
        if is_downloading:
            self.download_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.download_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
