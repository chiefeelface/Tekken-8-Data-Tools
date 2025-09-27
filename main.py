"""
Main entry point for the Tekken Replay Analyzer.
"""

import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.config.settings import load_config
    from src.utils.logging_config import setup_logging
    from src.gui.main_window import TekkenReplayGUI
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def main():
    """Main function to run the application."""
    try:
        # Set up logging
        setup_logging(level=20)  # INFO level
        
        # Load configuration
        config = load_config()
        
        # Create and run GUI
        root = tk.Tk()
        
        # Set a modern theme if available
        try:
            style = ttk.Style()
            available_themes = style.theme_names()
            if 'clam' in available_themes:
                style.theme_use('clam')
            elif 'alt' in available_themes:
                style.theme_use('alt')
        except:
            pass
        
        app = TekkenReplayGUI(root, config)
        app.run()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
