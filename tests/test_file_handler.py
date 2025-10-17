"""
Tests for file handling functionality.
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch
import tkinter as tk

from utils.file_handler import FileHandler, find_las_file_with_dialog
from utils.exceptions import FileNotFoundError, InvalidFileFormatError


class TestFileHandler:
    """Test cases for FileHandler class."""
    
    def test_validate_las_file_valid(self):
        """Test validation of valid LAS file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as tmp:
            tmp.write(b'LASF\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            tmp_path = tmp.name
        
        try:
            handler = FileHandler()
            is_valid, error_msg = handler.validate_las_file(tmp_path)
            assert is_valid
            assert error_msg == ""
        finally:
            os.unlink(tmp_path)
    
    def test_validate_las_file_not_exist(self):
        """Test validation of non-existent file."""
        handler = FileHandler()
        is_valid, error_msg = handler.validate_las_file("nonexistent.las")
        assert not is_valid
        assert "does not exist" in error_msg
    
    def test_validate_las_file_wrong_extension(self):
        """Test validation of file with wrong extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b'some content')
            tmp_path = tmp.name
        
        try:
            handler = FileHandler()
            is_valid, error_msg = handler.validate_las_file(tmp_path)
            assert not is_valid
            assert "Invalid file extension" in error_msg
        finally:
            os.unlink(tmp_path)
    
    def test_validate_las_file_empty(self):
        """Test validation of empty file."""
        with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = FileHandler()
            is_valid, error_msg = handler.validate_las_file(tmp_path)
            assert not is_valid
            assert "File is empty" in error_msg
        finally:
            os.unlink(tmp_path)
    
    def test_get_file_info(self):
        """Test getting file information."""
        with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as tmp:
            tmp.write(b'LASF\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            tmp_path = tmp.name
        
        try:
            handler = FileHandler()
            file_info = handler.get_file_info(tmp_path)
            
            assert file_info['path'] == tmp_path
            assert file_info['name'] == os.path.basename(tmp_path)
            assert file_info['size'] > 0
            assert file_info['size_mb'] > 0
            assert 'error' not in file_info
        finally:
            os.unlink(tmp_path)
    
    def test_suggest_output_path(self):
        """Test output path suggestion."""
        handler = FileHandler()
        input_path = "/path/to/input/file.las"
        output_path = handler.suggest_output_path(input_path, "output.obj")
        
        expected = "/path/to/input/file_output.obj"
        assert output_path == expected
    
    @patch('tkinter.filedialog.askopenfilename')
    def test_find_las_file_with_dialog(self, mock_dialog):
        """Test finding LAS file with dialog."""
        # Mock the dialog to return a file path
        mock_dialog.return_value = "/path/to/test.las"
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as tmp:
            tmp.write(b'LASF\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            tmp_path = tmp.name
        
        try:
            # Mock os.path.exists to return True for our temp file
            with patch('os.path.exists', return_value=True):
                result = find_las_file_with_dialog("nonexistent.las")
                # Should return the mocked dialog result
                assert result == "/path/to/test.las"
        finally:
            os.unlink(tmp_path)
    
    def test_find_las_file_existing(self):
        """Test finding existing LAS file."""
        with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as tmp:
            tmp.write(b'LASF\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            tmp_path = tmp.name
        
        try:
            handler = FileHandler()
            result = handler.find_las_file(tmp_path)
            assert result == tmp_path
        finally:
            os.unlink(tmp_path)
    
    def test_find_las_file_nonexistent_no_dialog(self):
        """Test finding non-existent file without dialog (no parent window)."""
        handler = FileHandler()  # No parent window
        result = handler.find_las_file("nonexistent.las")
        assert result is None
