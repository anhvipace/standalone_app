"""
Main GUI window for the Point Cloud Analysis Agent application.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import csv
import numpy as np
from typing import Optional, Dict, Any

import sv_ttk
import matplotlib.pyplot as plt

from agent.agent_core import PointCloudAnalysisAgent
from config import UIConfig, ModelConfig, AnalysisConfig
from utils.logger import get_logger
from utils.exceptions import AgentExecutionError
from utils.file_handler import FileHandler
from visualization.plot_utils import InteractivePlot, create_3d_visualization
from ai.report_generator import create_report_generator

logger = get_logger(__name__)


class MainWindow:
    """Main application window with advanced point cloud analysis features."""
    
    def __init__(self, root: tk.Tk, ui_config: UIConfig, model_config: ModelConfig):
        """
        Initialize the main window.
        
        Args:
            root: Tkinter root window
            ui_config: UI configuration
            model_config: Model configuration
        """
        self.root = root
        self.ui_config = ui_config
        self.model_config = model_config
        
        # Initialize components
        self.agent: Optional[PointCloudAnalysisAgent] = None
        self.file_handler = FileHandler(root)
        self.report_generator: Optional[Any] = None
        
        # Analysis data
        self.analysis_results: Optional[Dict] = None
        self.file_path: Optional[str] = None
        self.design_profile: Optional[np.ndarray] = None
        self.last_slice_data: Optional[Dict] = None
        self.las_header_info: Dict = {}
        self.current_analysis_params: Dict = {}
        
        # UI state
        self.status_text = tk.StringVar(value="Please select a .LAS file to begin.")
        self.show_profile_var = tk.BooleanVar(value=False)
        
        # Initialize components
        self._initialize_agent()
        self._initialize_report_generator()
        
        # Setup UI
        self._setup_window()
        self._create_menu()
        self._create_widgets()
        
        logger.info("Main window initialized successfully")
    
    def _initialize_agent(self):
        """Initialize the AI agent."""
        try:
            self.agent = PointCloudAnalysisAgent(self.model_config, self.root)
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            messagebox.showerror("Initialization Error", 
                               f"Failed to initialize AI agent: {e}")
    
    def _setup_window(self):
        """Setup the main window properties."""
        self.root.title(self.ui_config.window_title)
        self.root.geometry(self.ui_config.window_size)
        
        # Set theme
        try:
            sv_ttk.set_theme(self.ui_config.theme)
        except Exception as e:
            logger.warning(f"Failed to set theme: {e}")
    
    def _create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input section
        self._create_input_section(main_frame)
        
        # Output section
        self._create_output_section(main_frame)
        
        # Status bar
        self._create_status_bar(main_frame)
    
    def _create_input_section(self, parent: ttk.Frame):
        """Create the input section."""
        input_frame = ttk.LabelFrame(parent, text="Objective for AI Agent", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File selection
        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_frame, text="LAS File:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, 
                                   font=(self.ui_config.font_family, self.ui_config.font_size))
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(file_frame, text="Browse", 
                  command=self._browse_file).pack(side=tk.LEFT)
        
        # Objective input
        ttk.Label(input_frame, text="Objective:").pack(anchor=tk.W)
        self.objective_entry = ttk.Entry(input_frame, 
                                        font=(self.ui_config.font_family, self.ui_config.font_size))
        self.objective_entry.pack(fill=tk.X, pady=(5, 10))
        self.objective_entry.insert(0, "Analyze the selected LAS file and create a 3D mesh model")
        
        # Control buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X)
        
        self.run_button = ttk.Button(button_frame, text="Start Analysis", 
                                   command=self._start_analysis)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="Clear Output", 
                                     command=self._clear_output)
        self.clear_button.pack(side=tk.LEFT)
    
    def _create_output_section(self, parent: ttk.Frame):
        """Create the output section."""
        output_frame = ttk.LabelFrame(parent, text="AI Agent Process", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            wrap=tk.WORD, 
            relief="flat", 
            font=(self.ui_config.monospace_font, 9),
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_status_bar(self, parent: ttk.Frame):
        """Create the status bar."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def _browse_file(self):
        """Open file dialog to select LAS file."""
        file_path = filedialog.askopenfilename(
            title="Select LAS File",
            filetypes=[
                ("LAS files", "*.las"),
                ("LAZ files", "*.laz"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)
            # Update objective with file name
            file_name = os.path.basename(file_path)
            self.objective_entry.delete(0, tk.END)
            self.objective_entry.insert(0, f"Analyze '{file_name}' and create a 3D mesh model")
            
            # Show file info
            self._show_file_info(file_path)
    
    def _show_file_info(self, file_path: str):
        """Show file information in the output area."""
        try:
            from utils.file_handler import FileHandler
            handler = FileHandler(self.root)
            file_info = handler.get_file_info(file_path)
            
            info_text = (f"Selected file: {file_info['name']}\n"
                        f"Size: {file_info['size_mb']} MB\n"
                        f"Path: {file_info['path']}\n")
            
            self._append_output(info_text)
            
        except Exception as e:
            logger.warning(f"Failed to get file info: {e}")
    
    def _start_analysis(self):
        """Start the analysis in a separate thread."""
        if not self.agent:
            messagebox.showerror("Error", "AI agent not initialized")
            return
        
        objective = self.objective_entry.get().strip()
        if not objective:
            messagebox.showwarning("Warning", "Please enter an objective")
            return
        
        # Get file path from GUI
        file_path = self.file_path_var.get().strip()
        if not file_path:
            messagebox.showwarning("Warning", "Please select a LAS file")
            return
        
        # Disable controls
        self.run_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        self.status_var.set("Running analysis...")
        
        # Clear and prepare output
        self._clear_output()
        self._append_output(f"Starting analysis: {objective}\n")
        self._append_output(f"File: {os.path.basename(file_path)}\n\n")
        
        # Start analysis thread
        threading.Thread(
            target=self._run_analysis_thread, 
            args=(objective, file_path), 
            daemon=True
        ).start()
    
    def _run_analysis_thread(self, objective: str, file_path: str):
        """Run the analysis in a separate thread."""
        try:
            # Update objective to include file path
            enhanced_objective = f"{objective}\n\nFile path: {file_path}"
            result = self.agent.execute(enhanced_objective)
            self.root.after(0, self._analysis_completed, result, None)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.root.after(0, self._analysis_completed, None, str(e))
    
    def _analysis_completed(self, result: Optional[str], error: Optional[str]):
        """Handle analysis completion."""
        if error:
            self._append_output(f"\n--- ERROR ---\n{error}\n")
            self.status_var.set("Analysis failed")
        else:
            self._append_output(f"\n--- FINAL RESULT ---\n{result}\n")
            self.status_var.set("Analysis completed")
        
        # Re-enable controls
        self.run_button.config(state=tk.NORMAL)
        self.clear_button.config(state=tk.NORMAL)
    
    def _clear_output(self):
        """Clear the output text area."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.status_var.set("Ready")
    
    def _append_output(self, text: str):
        """Append text to the output area."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.config(state=tk.DISABLED)
        self.output_text.see(tk.END)  # Scroll to bottom
