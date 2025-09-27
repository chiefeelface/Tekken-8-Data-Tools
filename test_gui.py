"""
Simple test script to verify the GUI works.
"""

import sys
import tkinter as tk
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_gui():
    """Test basic GUI creation."""
    try:
        print("Testing basic tkinter...")
        root = tk.Tk()
        root.title("Test Window")
        root.geometry("300x200")
        
        label = tk.Label(root, text="If you see this, tkinter is working!")
        label.pack(pady=50)
        
        print("Basic tkinter test passed!")
        root.mainloop()
        
    except Exception as e:
        print(f"Basic tkinter test failed: {e}")
        return False
    
    return True

def test_imports():
    """Test importing our modules."""
    try:
        print("Testing imports...")
        
        from config.settings import AppConfig
        print("✓ AppConfig imported")
        
        from utils.logging_config import setup_logging
        print("✓ setup_logging imported")
        
        from gui.components import DatePickerFrame
        print("✓ DatePickerFrame imported")
        
        from gui.main_window import TekkenReplayGUI
        print("✓ TekkenReplayGUI imported")
        
        print("All imports successful!")
        return True
        
    except Exception as e:
        print(f"Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_creation():
    """Test creating the actual GUI."""
    try:
        print("Testing GUI creation...")
        
        from config.settings import AppConfig
        from gui.main_window import TekkenReplayGUI
        
        root = tk.Tk()
        config = AppConfig()
        
        app = TekkenReplayGUI(root, config)
        print("✓ GUI created successfully!")
        
        # Don't run mainloop in test
        root.destroy()
        return True
        
    except Exception as e:
        print(f"GUI creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running GUI tests...")
    print("=" * 40)
    
    # Test 1: Basic tkinter
    if not test_basic_gui():
        print("Basic tkinter test failed. Exiting.")
        sys.exit(1)
    
    # Test 2: Imports
    if not test_imports():
        print("Import test failed. Exiting.")
        sys.exit(1)
    
    # Test 3: GUI creation
    if not test_gui_creation():
        print("GUI creation test failed. Exiting.")
        sys.exit(1)
    
    print("=" * 40)
    print("All tests passed! The GUI should work now.")
    print("Try running: python main.py")
