#!/usr/bin/env python3
"""
Script to run the Point Cloud Analysis Tool
"""
import sys
import subprocess
import os

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'numpy', 'laspy', 'open3d', 'matplotlib', 
        'alphashape', 'sv_ttk', 'google-generativeai'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(packages):
    """Install missing dependencies."""
    if not packages:
        return True
    
    print(f"Installing missing packages: {', '.join(packages)}")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + packages)
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def check_api_key():
    """Check if Google API key is configured."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("\n" + "="*60)
        print("WARNING: Google API Key not configured")
        print("="*60)
        print("To enable AI Report feature:")
        print("1. Get API key from: https://aistudio.google.com/")
        print("2. Set environment variable:")
        print("   Windows: set GOOGLE_API_KEY=your_key_here")
        print("   Linux/Mac: export GOOGLE_API_KEY=your_key_here")
        print("="*60)
        return False
    else:
        print("Google API Key configured - AI Report feature enabled")
        return True

def main():
    """Main function to run the application."""
    print("Point Cloud Analysis Tool - Launcher")
    print("="*50)
    
    # Check dependencies
    print("Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        if not install_dependencies(missing):
            print("Failed to install dependencies. Please install manually:")
            print(f"pip install {' '.join(missing)}")
            return False
    else:
        print("All dependencies are installed!")
    
    # Check API key
    check_api_key()
    
    # Run the application
    print("\nStarting Point Cloud Analysis Tool...")
    print("="*50)
    
    try:
        from standalone_app import AnalysisApp
        import tkinter as tk
        
        root = tk.Tk()
        app = AnalysisApp(root)
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("\nPress Enter to exit...")
        sys.exit(1)

