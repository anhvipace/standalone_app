#!/usr/bin/env python3
"""
Test script to verify all fixes are working correctly
"""
import sys
import os

def test_imports():
    """Test all critical imports."""
    print("Testing imports...")
    
    try:
        import tkinter as tk
        print("✓ tkinter imported successfully")
    except ImportError as e:
        print(f"✗ tkinter import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ numpy imported successfully")
    except ImportError as e:
        print(f"✗ numpy import failed: {e}")
        return False
    
    try:
        import laspy
        print("✓ laspy imported successfully")
    except ImportError as e:
        print(f"✗ laspy import failed: {e}")
        return False
    
    try:
        import open3d as o3d
        print("✓ open3d imported successfully")
    except ImportError as e:
        print(f"✗ open3d import failed: {e}")
        return False
    
    try:
        import matplotlib.pyplot as plt
        print("✓ matplotlib imported successfully")
    except ImportError as e:
        print(f"✗ matplotlib import failed: {e}")
        return False
    
    try:
        import sv_ttk
        print("✓ sv_ttk imported successfully")
    except ImportError as e:
        print(f"✗ sv_ttk import failed: {e}")
        return False
    
    try:
        import alphashape
        print("✓ alphashape imported successfully")
    except ImportError as e:
        print(f"✗ alphashape import failed: {e}")
        return False
    
    return True

def test_analysis_tools():
    """Test analysis_tools.py imports."""
    print("\nTesting analysis_tools.py...")
    
    try:
        from analysis_tools import load_las_file, run_analysis, reconstruct_and_save_3d_mesh
        print("✓ analysis_tools functions imported successfully")
        return True
    except ImportError as e:
        print(f"✗ analysis_tools import failed: {e}")
        return False

def test_agent_core():
    """Test agent_core.py imports."""
    print("\nTesting agent_core.py...")
    
    try:
        from agent_core import create_agent_executor
        print("✓ agent_core imported successfully")
        
        # Test creating executor
        executor = create_agent_executor()
        print("✓ agent executor created successfully")
        return True
    except ImportError as e:
        print(f"✗ agent_core import failed: {e}")
        return False

def test_main_gui():
    """Test main_gui.py imports."""
    print("\nTesting main_gui.py...")
    
    try:
        # This will test the imports without creating the GUI
        import main_gui
        print("✓ main_gui imported successfully")
        return True
    except ImportError as e:
        print(f"✗ main_gui import failed: {e}")
        return False

def test_standalone_app():
    """Test standalone_app.py imports."""
    print("\nTesting standalone_app.py...")
    
    try:
        import standalone_app
        print("✓ standalone_app imported successfully")
        return True
    except ImportError as e:
        print(f"✗ standalone_app import failed: {e}")
        return False

def test_file_structure():
    """Test file structure."""
    print("\nTesting file structure...")
    
    required_files = [
        'main_gui.py',
        'standalone_app.py',
        'agent_core.py',
        'analysis_tools.py',
        'run_app.py',
        'requirements_standalone.txt',
        'README_standalone.md'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files present")
        return True

def test_las_file():
    """Test LAS file availability."""
    print("\nTesting LAS file...")
    
    las_files = [f for f in os.listdir('.') if f.endswith('.las')]
    if las_files:
        print(f"✓ Found LAS files: {las_files}")
        return True
    else:
        print("⚠ No LAS files found in current directory")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Point Cloud Analysis Tool - Fix Verification")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Core Imports", test_imports),
        ("Analysis Tools", test_analysis_tools),
        ("Agent Core", test_agent_core),
        ("Main GUI", test_main_gui),
        ("Standalone App", test_standalone_app),
        ("LAS File", test_las_file)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  {test_name} failed!")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
        print("\nTo run the application:")
        print("  python main_gui.py          # Enhanced GUI")
        print("  python standalone_app.py    # Standalone version")
        print("  python run_app.py           # Auto-installer")
    else:
        print("⚠ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)




