"""
Debug version of main.py to see what's happening.
"""

import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

print("Starting debug main.py...")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
print(f"Added to path: {str(Path(__file__).parent / 'src')}")

try:
    print("Importing config...")
    from config.settings import load_config
    print("✓ Config imported")
    
    print("Importing logging...")
    from utils.logging_config import setup_logging
    print("✓ Logging imported")
    
    print("Importing GUI...")
    from gui.main_window import TekkenReplayGUI
    print("✓ GUI imported")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

def main():
    """Main function to run the application."""
    try:
        print("Setting up logging...")
        setup_logging(level=20)  # INFO level
        print("✓ Logging setup complete")
        
        print("Loading configuration...")
        config = load_config()
        print("✓ Configuration loaded")
        
        print("Creating tkinter root...")
        root = tk.Tk()
        print("✓ Root created")
        
        print("Setting theme...")
        try:
            style = ttk.Style()
            available_themes = style.theme_names()
            print(f"Available themes: {available_themes}")
            if 'clam' in available_themes:
                style.theme_use('clam')
                print("Using clam theme")
            elif 'alt' in available_themes:
                style.theme_use('alt')
                print("Using alt theme")
        except Exception as e:
            print(f"Theme setup failed: {e}")
        
        print("Creating GUI application...")
        app = TekkenReplayGUI(root, config)
        print("✓ GUI application created")
        
        print("Starting GUI...")
        app.run()
        print("GUI finished")
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
