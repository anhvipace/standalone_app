#!/usr/bin/env python3
"""
Test script for the enhanced main_gui.py
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all imports work correctly."""
    print("=== Testing Imports ===")
    
    try:
        from main_gui import AgentApp
        print("OK - AgentApp import successful")
    except ImportError as e:
        print(f"ERROR - AgentApp import failed: {e}")
        return False
    
    try:
        import tkinter as tk
        from tkinter import ttk, scrolledtext, messagebox, filedialog
        print("OK - Tkinter imports successful")
    except ImportError as e:
        print(f"ERROR - Tkinter imports failed: {e}")
        return False
    
    try:
        from agent.agent_core import PointCloudAnalysisAgent
        from config import UIConfig, ModelConfig
        from utils.logger import get_logger
        from utils.exceptions import AgentExecutionError
        from utils.file_handler import FileHandler
        print("OK - New structure imports successful")
    except ImportError as e:
        print(f"ERROR - New structure imports failed: {e}")
        return False
    
    return True

def test_gui_creation():
    """Test if GUI can be created without errors."""
    print("\n=== Testing GUI Creation ===")
    
    try:
        import tkinter as tk
        from main_gui import AgentApp
        
        # Create a test window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        app = AgentApp(root)
        print("OK - GUI creation successful")
        
        # Test some methods
        app._update_output("Test message")
        print("OK - _update_output method works")
        
        app._enable_buttons()
        print("OK - _enable_buttons method works")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"ERROR - GUI creation failed: {e}")
        return False

def test_file_handling():
    """Test file handling functionality."""
    print("\n=== Testing File Handling ===")
    
    try:
        from utils.file_handler import FileHandler
        
        handler = FileHandler()
        print("OK - FileHandler creation successful")
        
        # Test file validation
        is_valid, error_msg = handler.validate_las_file("nonexistent.las")
        print(f"OK - File validation works: {is_valid}, {error_msg}")
        
        return True
        
    except Exception as e:
        print(f"ERROR - File handling test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Enhanced main_gui.py")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_gui_creation,
        test_file_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS - All tests passed! The enhanced GUI is ready to use.")
        print("\nTo run the enhanced GUI:")
        print("python main_gui.py")
    else:
        print("ERROR - Some tests failed. Please check the errors above.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
