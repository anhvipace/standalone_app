"""
Advanced main GUI window for the Point Cloud Analysis Agent application.
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


class AdvancedMainWindow:
    """Advanced main application window with comprehensive point cloud analysis features."""
    
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
        
        logger.info("Advanced main window initialized successfully")
    
    def _initialize_agent(self):
        """Initialize the AI agent."""
        try:
            self.agent = PointCloudAnalysisAgent(self.model_config, self.root)
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            messagebox.showerror("Initialization Error", 
                               f"Failed to initialize AI agent: {e}")
    
    def _initialize_report_generator(self):
        """Initialize the AI report generator."""
        try:
            self.report_generator = create_report_generator()
            logger.info("Report generator initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize report generator: {e}")
            # Don't show error dialog for optional feature
    
    def _setup_window(self):
        """Setup the main window properties."""
        self.root.title("Point Cloud Analysis Tool - Advanced Edition")
        
        # Center window on screen
        window_width, window_height = 1000, 800
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Set theme
        try:
            sv_ttk.set_theme(self.ui_config.theme)
        except Exception as e:
            logger.warning(f"Failed to set theme: {e}")
    
    def _create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Import .LAS File", command=self.browse_las_file)
        file_menu.add_command(label="Import Profile", command=self.import_profile)
        file_menu.add_separator()
        file_menu.add_command(label="Export Cross-section", command=self.export_cross_section)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        analysis_menu.add_command(label="Start Analysis", command=self.start_analysis_thread)
        analysis_menu.add_command(label="Show 3D Points", command=self.show_3d_result)
        analysis_menu.add_command(label="Reconstruct 3D Mesh", command=self.reconstruct_3d_mesh)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        
        # AI menu
        ai_menu = tk.Menu(menubar, tearoff=0)
        ai_menu.add_command(label="Generate AI Report", command=self.start_generate_report_thread)
        menubar.add_cascade(label="AI", menu=ai_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="User Guide", command=self.show_help_dialog)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about_dialog)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def _create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        self._create_control_section(main_frame)
        
        # Parameters section
        self._create_parameters_section(main_frame)
        
        # Results section
        self._create_results_section(main_frame)
        
        # Cross-section section
        self._create_cross_section_section(main_frame)
        
        # Information display
        self._create_info_section(main_frame)
        
        # Status and progress
        self._create_status_section(main_frame)
    
    def _create_control_section(self, parent):
        """Create control buttons section."""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=5)
        
        self.browse_button = ttk.Button(control_frame, text="📁 Import .LAS", 
                                       command=self.browse_las_file)
        self.browse_button.pack(side=tk.LEFT, padx=5, ipady=5)
        
        self.profile_button = ttk.Button(control_frame, text="📐 Import Profile", 
                                        command=self.import_profile)
        self.profile_button.pack(side=tk.LEFT, padx=5, ipady=5)
        
        self.analyze_button = ttk.Button(control_frame, text="▶ Start Analysis", 
                                        command=self.start_analysis_thread, 
                                        state=tk.DISABLED)
        self.analyze_button.pack(side=tk.LEFT, padx=5, ipady=5)
    
    def _create_parameters_section(self, parent):
        """Create analysis parameters section."""
        param_frame = ttk.LabelFrame(parent, text="Analysis Parameters", padding=10)
        param_frame.pack(fill=tk.X, pady=10)
        
        # Create parameter entries
        self.params = {}
        param_list = {
            "min_wall_height": ("Min Wall Height (m):", "5.0"),
            "ransac_distance": ("RANSAC Distance (m):", "0.1"),
            "ground_angle": ("Ground Angle (°):", "15.0"),
            "wall_angle": ("Wall Angle (°):", "75.0")
        }
        
        for i, (key, (text, default_val)) in enumerate(param_list.items()):
            label = ttk.Label(param_frame, text=text, font=("Segoe UI", 10, "bold"))
            label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            entry = ttk.Entry(param_frame, width=10)
            entry.grid(row=i, column=1, sticky=tk.W, padx=5, pady=5)
            entry.insert(0, default_val)
            self.params[key] = entry
    
    def _create_results_section(self, parent):
        """Create results section."""
        result_frame = ttk.LabelFrame(parent, text="Analysis Results", padding=10)
        result_frame.pack(fill=tk.X, pady=10)
        
        # Top row buttons
        top_row = ttk.Frame(result_frame)
        top_row.pack(fill=tk.X, pady=(0, 5))
        
        self.show_3d_button = ttk.Button(top_row, text="Show 3D Points", 
                                        command=self.show_3d_result, 
                                        state=tk.DISABLED)
        self.show_3d_button.pack(side=tk.LEFT, padx=5, ipady=5)
        
        self.reconstruct_3d_button = ttk.Button(top_row, text="Reconstruct 3D Mesh", 
                                               command=self.reconstruct_3d_mesh, 
                                               state=tk.DISABLED)
        self.reconstruct_3d_button.pack(side=tk.LEFT, padx=5, ipady=5)
        
        self.report_button = ttk.Button(top_row, text="🤖 Generate AI Report", 
                                       command=self.start_generate_report_thread, 
                                       state=tk.DISABLED)
        self.report_button.pack(side=tk.LEFT, padx=5, ipady=5)
        
        self.export_profile_btn = ttk.Button(top_row, text="Export Cross-section...", 
                                            command=self.export_cross_section, 
                                            state=tk.DISABLED)
        self.export_profile_btn.pack(side=tk.RIGHT, padx=5, ipady=5)
    
    def _create_cross_section_section(self, parent):
        """Create cross-section analysis section."""
        cross_frame = ttk.LabelFrame(parent, text="Cross-Section Analysis", padding=10)
        cross_frame.pack(fill=tk.X, pady=10)
        
        # Y position input
        pos_frame = ttk.Frame(cross_frame)
        pos_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(pos_frame, text="Y Position:").pack(side=tk.LEFT, padx=(0, 5))
        self.slice_pos_entry = ttk.Entry(pos_frame, width=10)
        self.slice_pos_entry.pack(side=tk.LEFT)
        
        # Cross-section buttons
        button_frame = ttk.Frame(cross_frame)
        button_frame.pack(fill=tk.X)
        
        self.view_slice_btn = ttk.Button(button_frame, text="View 2D Cross-section", 
                                        command=self.view_cross_section_normal, 
                                        state=tk.DISABLED)
        self.view_slice_btn.pack(side=tk.LEFT, padx=5)
        
        self.compare_btn = ttk.Button(button_frame, text="Compare Profile", 
                                     command=self.view_cross_section_with_profile, 
                                     state=tk.DISABLED)
        self.compare_btn.pack(side=tk.LEFT, padx=5)
        
        self.profile_checkbox = ttk.Checkbutton(button_frame, text="Show Profile", 
                                               variable=self.show_profile_var)
        self.profile_checkbox.pack(side=tk.LEFT, padx=(10, 5))
    
    def _create_info_section(self, parent):
        """Create information display section."""
        info_frame = ttk.LabelFrame(parent, text="Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, height=8, 
                                                  state=tk.DISABLED)
        self.info_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_status_section(self, parent):
        """Create status and progress section."""
        # Status label
        status_label = ttk.Label(parent, textvariable=self.status_text, 
                                font=("Segoe UI", 9, "italic"))
        status_label.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(5, 0))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(parent, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 10))
    
    # File handling methods
    def browse_las_file(self):
        """Browse and select LAS file."""
        file_path = filedialog.askopenfilename(
            title="Select LAS File",
            filetypes=[
                ("LAS files", "*.las"),
                ("LAZ files", "*.laz"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.file_path = file_path
            self.status_text.set(f"Selected: {os.path.basename(file_path)}. Ready to analyze.")
            self.analyze_button.config(state=tk.NORMAL)
            self._disable_result_buttons()
            self._load_file_info(file_path)
    
    def _load_file_info(self, file_path: str):
        """Load and display file information."""
        try:
            file_info = self.file_handler.get_file_info(file_path)
            
            # Try to read LAS header
            import laspy
            with laspy.open(file_path) as f:
                header = f.header
                self.las_header_info = {
                    "point_count": header.point_count,
                    "y_min": header.y_min,
                    "y_max": header.y_max,
                    "x_min": header.x_min,
                    "x_max": header.x_max,
                    "z_min": header.z_min,
                    "z_max": header.z_max
                }
                
                # Set default Y position to middle
                middle_y = (header.y_min + header.y_max) / 2.0
                self.slice_pos_entry.delete(0, tk.END)
                self.slice_pos_entry.insert(0, f"{middle_y:.2f}")
            
            info_str = (f"File: {file_info['name']}\n"
                       f"Size: {file_info['size_mb']} MB\n"
                       f"Points: {self.las_header_info['point_count']:,}\n"
                       f"X Range: [{self.las_header_info['x_min']:.2f}, {self.las_header_info['x_max']:.2f}] m\n"
                       f"Y Range: [{self.las_header_info['y_min']:.2f}, {self.las_header_info['y_max']:.2f}] m\n"
                       f"Z Range: [{self.las_header_info['z_min']:.2f}, {self.las_header_info['z_max']:.2f}] m")
            
            self._update_info_text(info_str)
            
        except Exception as e:
            self._update_info_text(f"Error reading file:\n{e}")
            logger.error(f"Failed to load file info: {e}")
    
    def import_profile(self):
        """Import design profile from CSV file."""
        file_path = filedialog.askopenfilename(
            title="Select Profile CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                profile_data = []
                with open(file_path, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            profile_data.append([float(row[0]), float(row[1])])
                
                self.design_profile = np.array(profile_data)
                self.compare_btn.config(state=tk.NORMAL)
                self._update_info_text(f"Profile loaded: {len(profile_data)} points")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load profile: {e}")
                logger.error(f"Failed to load profile: {e}")
    
    # Analysis methods
    def start_analysis_thread(self):
        """Start analysis in a separate thread."""
        if not self.file_path:
            messagebox.showwarning("Warning", "Please select a LAS file first")
            return
        
        try:
            self.current_analysis_params = {
                key: float(entry.get()) for key, entry in self.params.items()
            }
        except ValueError:
            messagebox.showerror("Error", "Invalid parameter values")
            return
        
        self.browse_button.config(state=tk.DISABLED)
        self.analyze_button.config(state=tk.DISABLED)
        self._disable_result_buttons()
        self._update_progress(0)
        
        threading.Thread(target=self._run_analysis, daemon=True).start()
    
    def _run_analysis(self):
        """Run the point cloud analysis."""
        try:
            from analysis.point_cloud_processor import PointCloudProcessor
            
            config = AnalysisConfig(
                min_wall_height=self.current_analysis_params['min_wall_height'],
                ransac_distance=self.current_analysis_params['ransac_distance'],
                ground_angle=self.current_analysis_params['ground_angle'],
                wall_angle=self.current_analysis_params['wall_angle']
            )
            
            processor = PointCloudProcessor(config, self.root)
            
            # Load file
            self._update_status("Loading LAS file...")
            self._update_progress(10)
            processor.load_las_file(self.file_path)
            
            # Run analysis
            self._update_status("Running analysis...")
            self._update_progress(50)
            result = processor.analyze_point_cloud()
            
            # Store results
            self.analysis_results = processor.analysis_results
            self._update_status("Analysis completed successfully!")
            self._update_progress(100)
            
            # Enable result buttons
            self.root.after(0, self._enable_result_buttons)
            
        except Exception as e:
            self._update_status(f"Analysis failed: {e}")
            self._update_progress(0)
            logger.error(f"Analysis failed: {e}")
        
        finally:
            self.root.after(0, self._enable_control_buttons)
    
    # Visualization methods
    def show_3d_result(self):
        """Show 3D visualization of analysis results."""
        if not self.analysis_results:
            messagebox.showwarning("No Data", "Please run analysis first")
            return
        
        try:
            import open3d as o3d
            
            # Create geometries
            geometries = []
            
            # Ground points
            if len(self.analysis_results["ground"].points) > 0:
                ground_pcd = self.analysis_results["ground"]
                ground_pcd.paint_uniform_color([0.5, 0.5, 0.5])  # Gray
                geometries.append(ground_pcd)
            
            # Wall 1
            if len(self.analysis_results["wall1"].points) > 0:
                wall1_pcd = self.analysis_results["wall1"]
                wall1_pcd.paint_uniform_color([1, 0, 0])  # Red
                geometries.append(wall1_pcd)
            
            # Wall 2
            if len(self.analysis_results["wall2"].points) > 0:
                wall2_pcd = self.analysis_results["wall2"]
                wall2_pcd.paint_uniform_color([0, 0, 1])  # Blue
                geometries.append(wall2_pcd)
            
            create_3d_visualization(geometries, "3D Point Cloud Analysis")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show 3D visualization: {e}")
            logger.error(f"3D visualization error: {e}")
    
    def reconstruct_3d_mesh(self):
        """Reconstruct 3D mesh from analysis results."""
        if not self.analysis_results:
            messagebox.showwarning("No Data", "Please run analysis first")
            return
        
        try:
            from analysis.point_cloud_processor import PointCloudProcessor
            
            config = AnalysisConfig()
            processor = PointCloudProcessor(config, self.root)
            processor.analysis_results = self.analysis_results
            
            # Suggest output filename
            output_filename = self.file_handler.suggest_output_path(
                self.file_path, "reconstructed_mesh.obj"
            )
            
            result = processor.reconstruct_mesh(output_filename)
            self._update_info_text(f"Mesh reconstruction: {result}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reconstruct mesh: {e}")
            logger.error(f"Mesh reconstruction error: {e}")
    
    # Cross-section methods
    def view_cross_section_normal(self):
        """View normal cross-section."""
        self._view_cross_section(with_profile=False)
    
    def view_cross_section_with_profile(self):
        """View cross-section with profile comparison."""
        if self.design_profile is None:
            messagebox.showwarning("No Profile", "Please import a design profile first")
            return
        self._view_cross_section(with_profile=True)
    
    def _view_cross_section(self, with_profile: bool):
        """View cross-section at specified Y position."""
        if not self.analysis_results:
            messagebox.showwarning("No Data", "Please run analysis first")
            return
        
        try:
            y_position = float(self.slice_pos_entry.get())
            
            # Extract points near Y position
            tolerance = 0.5  # meters
            ground_pts = self._extract_slice_points(self.analysis_results["ground"], y_position, tolerance)
            wall1_pts = self._extract_slice_points(self.analysis_results["wall1"], y_position, tolerance)
            wall2_pts = self._extract_slice_points(self.analysis_results["wall2"], y_position, tolerance)
            
            if len(ground_pts) == 0 and len(wall1_pts) == 0 and len(wall2_pts) == 0:
                messagebox.showwarning("No Data", f"No points found near Y={y_position}")
                return
            
            # Store slice data
            self.last_slice_data = {
                "y_position": y_position,
                "ground_pts": ground_pts,
                "wall1_pts": wall1_pts,
                "wall2_pts": wall2_pts
            }
            
            # Create interactive plot
            design_profile = self.design_profile if with_profile else None
            show_actual = self.show_profile_var.get()
            
            InteractivePlot(ground_pts, wall1_pts, wall2_pts, y_position, 
                          design_profile, show_actual)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid Y position value")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create cross-section: {e}")
            logger.error(f"Cross-section error: {e}")
    
    def _extract_slice_points(self, point_cloud, y_position: float, tolerance: float) -> np.ndarray:
        """Extract points within tolerance of Y position."""
        if len(point_cloud.points) == 0:
            return np.array([])
        
        points = np.asarray(point_cloud.points)
        y_coords = points[:, 1]
        mask = np.abs(y_coords - y_position) <= tolerance
        return points[mask]
    
    # AI Report methods
    def start_generate_report_thread(self):
        """Start AI report generation in a separate thread."""
        if not self.report_generator:
            messagebox.showerror("Error", "AI report generator not available")
            return
        
        if not self.analysis_results:
            messagebox.showwarning("No Data", "Please run analysis first")
            return
        
        self._update_status("🤖 Generating AI report... Please wait.")
        threading.Thread(target=self._generate_report, daemon=True).start()
    
    def _generate_report(self):
        """Generate AI report."""
        try:
            # Prepare analysis data
            analysis_data = {
                'file_info': {
                    'name': os.path.basename(self.file_path) if self.file_path else 'N/A',
                    'point_count': self.las_header_info.get('point_count', 0),
                    'size_mb': self.file_handler.get_file_info(self.file_path)['size_mb'] if self.file_path else 0,
                    'y_min': self.las_header_info.get('y_min', 0),
                    'y_max': self.las_header_info.get('y_max', 0)
                },
                'analysis_params': self.current_analysis_params,
                'results': {
                    'ground_points': len(self.analysis_results["ground"].points),
                    'wall1_points': len(self.analysis_results["wall1"].points),
                    'wall2_points': len(self.analysis_results["wall2"].points),
                    'status': 'Successful'
                }
            }
            
            report_text = self.report_generator.generate_analysis_report(analysis_data)
            self.root.after(0, self._show_report_window, report_text)
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "AI Report Error", f"Could not generate report: {e}")
            logger.error(f"Report generation error: {e}")
        finally:
            self.root.after(0, lambda: self._update_status("AI Report generated. Ready for next task."))
    
    def _show_report_window(self, report_text: str):
        """Show AI report in a new window."""
        report_window = tk.Toplevel(self.root)
        report_window.title("Generated AI Report")
        report_window.geometry("700x600")
        report_window.transient(self.root)
        
        # Text widget
        text_widget = scrolledtext.ScrolledText(report_window, wrap=tk.WORD, 
                                               font=("Segoe UI", 10))
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, report_text)
        text_widget.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(report_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(report_text)
            self._update_status("Report copied to clipboard.")
        
        ttk.Button(button_frame, text="Copy to Clipboard", 
                  command=copy_to_clipboard).pack(side=tk.LEFT, expand=True)
        ttk.Button(button_frame, text="Close", 
                  command=report_window.destroy).pack(side=tk.LEFT, expand=True, padx=5)
    
    # Export methods
    def export_cross_section(self):
        """Export cross-section data to CSV."""
        if not self.last_slice_data:
            messagebox.showwarning("No Data", "Please view a cross-section first")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Cross-section Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['X', 'Z', 'Type'])
                    
                    # Ground points
                    for pt in self.last_slice_data['ground_pts']:
                        writer.writerow([pt[0], pt[2], 'Ground'])
                    
                    # Wall 1 points
                    for pt in self.last_slice_data['wall1_pts']:
                        writer.writerow([pt[0], pt[2], 'Wall1'])
                    
                    # Wall 2 points
                    for pt in self.last_slice_data['wall2_pts']:
                        writer.writerow([pt[0], pt[2], 'Wall2'])
                
                self._update_info_text(f"Cross-section data exported to: {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")
                logger.error(f"Export error: {e}")
    
    # UI helper methods
    def _disable_result_buttons(self):
        """Disable result buttons."""
        self.show_3d_button.config(state=tk.DISABLED)
        self.reconstruct_3d_button.config(state=tk.DISABLED)
        self.report_button.config(state=tk.DISABLED)
        self.view_slice_btn.config(state=tk.DISABLED)
        self.compare_btn.config(state=tk.DISABLED)
        self.export_profile_btn.config(state=tk.DISABLED)
    
    def _enable_result_buttons(self):
        """Enable result buttons."""
        self.show_3d_button.config(state=tk.NORMAL)
        self.reconstruct_3d_button.config(state=tk.NORMAL)
        self.report_button.config(state=tk.NORMAL)
        self.view_slice_btn.config(state=tk.NORMAL)
        self.export_profile_btn.config(state=tk.NORMAL)
        if self.design_profile is not None:
            self.compare_btn.config(state=tk.NORMAL)
    
    def _enable_control_buttons(self):
        """Enable control buttons."""
        self.browse_button.config(state=tk.NORMAL)
        self.analyze_button.config(state=tk.NORMAL)
    
    def _update_info_text(self, text: str):
        """Update information text."""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, text)
        self.info_text.config(state=tk.DISABLED)
    
    def _update_status(self, message: str):
        """Update status message."""
        self.root.after(0, lambda: self.status_text.set(message))
    
    def _update_progress(self, value: int):
        """Update progress bar."""
        self.root.after(0, lambda: self.progress_bar.config(value=value))
    
    # Dialog methods
    def show_help_dialog(self):
        """Show help dialog."""
        help_text = """
Point Cloud Analysis Tool - User Guide

1. Import LAS File: Select a .las or .laz file to analyze
2. Set Parameters: Adjust analysis parameters as needed
3. Start Analysis: Click to begin point cloud processing
4. View Results: Use 3D visualization and cross-section tools
5. Generate Report: Create AI-powered analysis reports

For more information, visit the project documentation.
        """
        messagebox.showinfo("User Guide", help_text)
    
    def show_about_dialog(self):
        """Show about dialog."""
        about_text = """
Point Cloud Analysis Tool - Advanced Edition
Version 2.0

Developed with:
- Python & Tkinter
- Open3D for 3D processing
- Matplotlib for visualization
- Google Generative AI for reports
- LangChain for intelligent analysis

© 2024 - Advanced Point Cloud Analysis
        """
        messagebox.showinfo("About", about_text)
