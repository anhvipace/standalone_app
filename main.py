"""
Main application entry point for the Point Cloud Analysis Agent.
"""
import tkinter as tk
import sys
import os
from typing import Optional

from config import get_default_config, load_config_from_env
from gui.advanced_main_window import AdvancedMainWindow
from utils.logger import setup_logger, get_logger
from utils.exceptions import PointCloudAnalysisError


def setup_application() -> tuple[tk.Tk, AdvancedMainWindow]:
    """
    Setup the application with proper configuration and error handling.
    
    Returns:
        Tuple of (root_window, main_window)
        
    Raises:
        PointCloudAnalysisError: If application setup fails
    """
    try:
        # Setup logging
        logger = setup_logger("main", "INFO")
        logger.info("Starting Point Cloud Analysis Agent application")
        
        # Load configuration
        try:
            config = load_config_from_env()
        except Exception as e:
            logger.warning(f"Failed to load config from environment, using defaults: {e}")
            config = get_default_config()
        
        # Create root window
        root = tk.Tk()
        
        # Create main window
        main_window = AdvancedMainWindow(root, config.ui, config.model)
        
        logger.info("Application setup completed successfully")
        return root, main_window
        
    except Exception as e:
        logger.error(f"Application setup failed: {e}")
        raise PointCloudAnalysisError(f"Failed to setup application: {e}")


def main():
    """Main application entry point."""
    try:
        # Setup application
        root, main_window = setup_application()
        
        # Start GUI event loop
        root.mainloop()
        
    except PointCloudAnalysisError as e:
        print(f"Application error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
