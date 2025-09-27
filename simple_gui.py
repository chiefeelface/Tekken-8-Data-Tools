"""
Simple working GUI to test basic functionality.
"""

import tkinter as tk
from tkinter import ttk
import datetime

def create_simple_gui():
    """Create a simple working GUI."""
    root = tk.Tk()
    root.title("Tekken 8 Replay Downloader - Simple Test")
    root.geometry("600x400")
    
    # Main frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="Tekken 8 Replay Downloader", font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # Date frame
    date_frame = ttk.LabelFrame(main_frame, text="Date Range", padding="15")
    date_frame.pack(fill=tk.X, pady=(0, 15))
    
    # Date selection
    ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
    start_date_var = tk.StringVar(value="2025-09-01")
    start_date_entry = ttk.Entry(date_frame, textvariable=start_date_var, width=12)
    start_date_entry.grid(row=0, column=1, padx=(0, 20))
    
    ttk.Label(date_frame, text="End Date:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
    end_date_var = tk.StringVar(value="2025-09-02")
    end_date_entry = ttk.Entry(date_frame, textvariable=end_date_var, width=12)
    end_date_entry.grid(row=0, column=3)
    
    # Progress frame
    progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="15")
    progress_frame.pack(fill=tk.X, pady=(0, 15))
    
    # Progress bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100, length=400)
    progress_bar.pack(pady=(0, 10))
    
    # Status label
    status_label = ttk.Label(progress_frame, text="Ready to download")
    status_label.pack()
    
    # Log frame
    log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="15")
    log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
    
    # Log text
    log_text = tk.Text(log_frame, height=8, width=60)
    log_text.pack(fill=tk.BOTH, expand=True)
    log_text.insert(tk.END, "Application started successfully!\n")
    
    # Control buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack()
    
    def start_download():
        log_text.insert(tk.END, "Download started!\n")
        log_text.see(tk.END)
        status_label.config(text="Downloading...")
        progress_var.set(50)
    
    def clear_logs():
        log_text.delete(1.0, tk.END)
        log_text.insert(tk.END, "Logs cleared.\n")
    
    ttk.Button(button_frame, text="Start Download", command=start_download).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Button(button_frame, text="Clear Logs", command=clear_logs).pack(side=tk.LEFT)
    
    return root

if __name__ == "__main__":
    root = create_simple_gui()
    root.mainloop()
