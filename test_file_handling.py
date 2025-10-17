#!/usr/bin/env python3
"""
Demo script to test file handling functionality.
"""
import os
import sys
import tempfile
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.file_handler import FileHandler, find_las_file_with_dialog
from utils.logger import setup_logger

def create_test_las_file():
    """Create a minimal test LAS file."""
    # Create a temporary file with minimal LAS header
    with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as tmp:
        # Write minimal LAS header (simplified)
        las_header = bytearray(375)  # Standard LAS header size
        las_header[0:4] = b'LASF'    # File signature
        las_header[4:6] = b'\x01\x01'  # Version
        las_header[24:28] = b'\x00\x00\x00\x00'  # Point count (will be 0)
        tmp.write(las_header)
        return tmp.name

def test_file_validation():
    """Test file validation functionality."""
    print("=== Testing File Validation ===")
    
    handler = FileHandler()
    
    # Test 1: Valid LAS file
    print("\n1. Testing valid LAS file...")
    test_file = create_test_las_file()
    try:
        is_valid, error_msg = handler.validate_las_file(test_file)
        print(f"   Valid: {is_valid}")
        print(f"   Error: {error_msg}")
        assert is_valid, "Valid LAS file should pass validation"
    finally:
        os.unlink(test_file)
    
    # Test 2: Non-existent file
    print("\n2. Testing non-existent file...")
    is_valid, error_msg = handler.validate_las_file("nonexistent.las")
    print(f"   Valid: {is_valid}")
    print(f"   Error: {error_msg}")
    assert not is_valid, "Non-existent file should fail validation"
    
    # Test 3: Wrong extension
    print("\n3. Testing wrong file extension...")
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
        tmp.write(b'some content')
        txt_file = tmp.name
    
    try:
        is_valid, error_msg = handler.validate_las_file(txt_file)
        print(f"   Valid: {is_valid}")
        print(f"   Error: {error_msg}")
        assert not is_valid, "Wrong extension should fail validation"
    finally:
        os.unlink(txt_file)
    
    # Test 4: Empty file
    print("\n4. Testing empty file...")
    with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as tmp:
        empty_file = tmp.name
    
    try:
        is_valid, error_msg = handler.validate_las_file(empty_file)
        print(f"   Valid: {is_valid}")
        print(f"   Error: {error_msg}")
        assert not is_valid, "Empty file should fail validation"
    finally:
        os.unlink(empty_file)
    
    print("✅ All validation tests passed!")

def test_file_info():
    """Test file information functionality."""
    print("\n=== Testing File Information ===")
    
    handler = FileHandler()
    test_file = create_test_las_file()
    
    try:
        file_info = handler.get_file_info(test_file)
        print(f"File: {file_info['name']}")
        print(f"Size: {file_info['size']} bytes ({file_info['size_mb']} MB)")
        print(f"Path: {file_info['path']}")
        print("✅ File info test passed!")
    finally:
        os.unlink(test_file)

def test_output_path_suggestion():
    """Test output path suggestion."""
    print("\n=== Testing Output Path Suggestion ===")
    
    handler = FileHandler()
    
    # Test 1: Basic suggestion
    input_path = "/path/to/input/file.las"
    output_path = handler.suggest_output_path(input_path, "output.obj")
    expected = "/path/to/input/file_output.obj"
    print(f"Input: {input_path}")
    print(f"Suggested: {output_path}")
    print(f"Expected: {expected}")
    assert output_path == expected, "Output path suggestion incorrect"
    
    # Test 2: Custom output name
    output_path = handler.suggest_output_path(input_path, "mesh.ply")
    expected = "/path/to/input/file_mesh.ply"
    print(f"Custom output: {output_path}")
    assert output_path == expected, "Custom output path suggestion incorrect"
    
    print("✅ Output path suggestion tests passed!")

def test_find_file():
    """Test file finding functionality."""
    print("\n=== Testing File Finding ===")
    
    handler = FileHandler()
    
    # Test 1: Existing file
    test_file = create_test_las_file()
    try:
        result = handler.find_las_file(test_file)
        print(f"Existing file result: {result}")
        assert result == test_file, "Should return existing file path"
    finally:
        os.unlink(test_file)
    
    # Test 2: Non-existing file (no dialog)
    result = handler.find_las_file("nonexistent.las")
    print(f"Non-existing file result: {result}")
    assert result is None, "Should return None for non-existing file without dialog"
    
    print("✅ File finding tests passed!")

def main():
    """Run all tests."""
    print("🧪 Testing File Handling Functionality")
    print("=" * 50)
    
    # Setup logging
    logger = setup_logger("test_file_handling", "INFO")
    
    try:
        test_file_validation()
        test_file_info()
        test_output_path_suggestion()
        test_find_file()
        
        print("\n🎉 All tests completed successfully!")
        print("\nTo test with GUI dialog, run the main application:")
        print("python main.py")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
