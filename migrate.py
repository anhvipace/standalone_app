#!/usr/bin/env python3
"""
Migration script to help transition from old to new project structure.
"""
import os
import sys
import shutil
from pathlib import Path


def check_old_files():
    """Check if old files exist."""
    old_files = ['agent_core.py', 'analysis_tools.py', 'main_gui.py']
    existing_files = [f for f in old_files if os.path.exists(f)]
    
    if existing_files:
        print(f"Found old files: {', '.join(existing_files)}")
        return True
    else:
        print("No old files found")
        return False


def backup_old_files():
    """Create backup of old files."""
    backup_dir = Path("backup_old")
    backup_dir.mkdir(exist_ok=True)
    
    old_files = ['agent_core.py', 'analysis_tools.py', 'main_gui.py']
    
    for file in old_files:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir / file)
            print(f"Backed up {file} to {backup_dir / file}")


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import numpy
        import laspy
        import open3d
        import langchain
        import langchain_google_genai
        import sv_ttk
        print("All dependencies are installed")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False


def verify_new_structure():
    """Verify new project structure is in place."""
    required_dirs = ['agent', 'analysis', 'gui', 'utils', 'tests']
    required_files = ['main.py', 'config.py', 'requirements.txt', 'setup.py']
    
    missing_dirs = [d for d in required_dirs if not os.path.exists(d)]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_dirs:
        print(f"Missing directories: {', '.join(missing_dirs)}")
        return False
    
    if missing_files:
        print(f"Missing files: {', '.join(missing_files)}")
        return False
    
    print("New project structure is complete")
    return True


def main():
    """Main migration function."""
    print("=== Point Cloud Analysis Agent Migration ===")
    print()
    
    # Check old files
    print("1. Checking old files...")
    has_old_files = check_old_files()
    print()
    
    # Backup old files if they exist
    if has_old_files:
        print("2. Creating backup of old files...")
        backup_old_files()
        print()
    
    # Check dependencies
    print("3. Checking dependencies...")
    deps_ok = check_dependencies()
    print()
    
    # Verify new structure
    print("4. Verifying new structure...")
    structure_ok = verify_new_structure()
    print()
    
    # Summary
    print("=== Migration Summary ===")
    if deps_ok and structure_ok:
        print("✅ Migration successful!")
        print()
        print("Next steps:")
        print("1. Run: python main.py")
        print("2. Test the new GUI")
        print("3. Check the MIGRATION_GUIDE.md for more details")
    else:
        print("❌ Migration incomplete")
        if not deps_ok:
            print("- Install missing dependencies")
        if not structure_ok:
            print("- Verify project structure")
        print()
        print("Run this script again after fixing the issues")


if __name__ == "__main__":
    main()
