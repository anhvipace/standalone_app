"""
File handling utilities for LAS files with dialog support.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Tuple
from pathlib import Path

from utils.exceptions import FileNotFoundError, InvalidFileFormatError
from utils.logger import get_logger

logger = get_logger(__name__)


class FileHandler:
    """Handles file operations with dialog support."""
    
    def __init__(self, parent_window: Optional[tk.Tk] = None):
        """
        Initialize file handler.
        
        Args:
            parent_window: Parent window for dialogs (optional)
        """
        self.parent_window = parent_window
        self.last_directory = os.getcwd()
    
    def validate_las_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if a file is a valid LAS file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path:
            return False, "No file path provided"
        
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
        
        if not os.path.isfile(file_path):
            return False, f"Path is not a file: {file_path}"
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in ['.las', '.laz']:
            return False, f"Invalid file extension: {file_ext}. Expected .las or .laz"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "File is empty"
        
        if file_size < 100:  # LAS files should be at least 100 bytes
            return False, "File is too small to be a valid LAS file"
        
        return True, ""
    
    def find_las_file(self, file_path: str) -> Optional[str]:
        """
        Find a LAS file, showing dialog if not found.
        
        Args:
            file_path: Initial file path to check
            
        Returns:
            Valid file path or None if user cancels
        """
        # First, try to validate the provided path
        is_valid, error_msg = self.validate_las_file(file_path)
        if is_valid:
            logger.info(f"Using provided file: {file_path}")
            return file_path
        
        logger.warning(f"File validation failed: {error_msg}")
        
        # Show error message and ask user to select file
        if self.parent_window:
            messagebox.showwarning(
                "File Not Found",
                f"Cannot find or access the LAS file:\n\n{error_msg}\n\n"
                "Please select a valid LAS file."
            )
            
            # Show file dialog
            selected_file = self._show_file_dialog()
            if selected_file:
                # Validate the selected file
                is_valid, error_msg = self.validate_las_file(selected_file)
                if is_valid:
                    logger.info(f"User selected valid file: {selected_file}")
                    return selected_file
                else:
                    messagebox.showerror(
                        "Invalid File",
                        f"The selected file is not valid:\n\n{error_msg}"
                    )
                    return None
            else:
                logger.info("User cancelled file selection")
                return None
        else:
            # No parent window, just log the error
            logger.error(f"Cannot show dialog: {error_msg}")
            return None
    
    def _show_file_dialog(self) -> Optional[str]:
        """
        Show file selection dialog.
        
        Returns:
            Selected file path or None if cancelled
        """
        try:
            file_path = filedialog.askopenfilename(
                parent=self.parent_window,
                title="Select LAS File",
                initialdir=self.last_directory,
                filetypes=[
                    ("LAS files", "*.las"),
                    ("LAZ files", "*.laz"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                # Update last directory
                self.last_directory = os.path.dirname(file_path)
                logger.info(f"File dialog selected: {file_path}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"File dialog error: {e}")
            return None
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get basic information about a LAS file.
        
        Args:
            file_path: Path to the LAS file
            
        Returns:
            Dictionary with file information
        """
        try:
            stat = os.stat(file_path)
            return {
                "path": file_path,
                "name": os.path.basename(file_path),
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": stat.st_mtime
            }
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {
                "path": file_path,
                "name": os.path.basename(file_path),
                "size": 0,
                "size_mb": 0,
                "modified": 0,
                "error": str(e)
            }
    
    def suggest_output_path(self, input_path: str, output_name: str = "output.obj") -> str:
        """
        Suggest an output path based on input file location.
        
        Args:
            input_path: Path to input LAS file
            output_name: Desired output filename
            
        Returns:
            Suggested output path
        """
        input_dir = os.path.dirname(input_path)
        input_name = os.path.splitext(os.path.basename(input_path))[0]
        
        # Create output filename based on input
        output_filename = f"{input_name}_{output_name}"
        return os.path.join(input_dir, output_filename)


def find_las_file_with_dialog(file_path: str, parent_window: Optional[tk.Tk] = None) -> Optional[str]:
    """
    Convenience function to find LAS file with dialog support.
    
    Args:
        file_path: Initial file path
        parent_window: Parent window for dialogs
        
    Returns:
        Valid file path or None
    """
    handler = FileHandler(parent_window)
    return handler.find_las_file(file_path)
