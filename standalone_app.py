"""
Standalone Point Cloud Analysis Tool - Dual Mode with AI Suggestions - v2.4
Tác giả: Hoàng Anh
"""
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import threading
import os
import csv
import numpy as np
import laspy
import open3d as o3d
import time # Thêm thư viện time để xử lý lỗi Quota

try:
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button as MplButton
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Cần cài đặt các thư viện:
# pip install sv_ttk alphashape laspy open3d matplotlib numpy google-generativeai
import sv_ttk
try:
    import alphashape
    ALPHASHAPE_AVAILABLE = True
except ImportError:
    ALPHASHAPE_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# --- CẤU HÌNH API KEY (AN TOÀN) ---
if GEMINI_AVAILABLE:
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("WARNING: GOOGLE_API_KEY environment variable not set. AI features will be disabled.")
            print("Huong dan thiet lap API key:")
            print("   1. Truy cap: https://aistudio.google.com/")
            print("   2. Tao API key")
            print("   3. Thiet lap bien moi truong (Yeu cau khoi dong lai Terminal/PC):")
            print("      PowerShell: [System.Environment]::SetEnvironmentVariable('GOOGLE_API_KEY', 'your_key_here', 'User')")
            GEMINI_AVAILABLE = False
        else:
            print(f"API key found: {api_key[:10]}...{api_key[-5:]}")
            genai.configure(api_key=api_key)
            print("Gemini API configured successfully")

            # Test API connection and list available models
            try:
                print("Testing API connection...")
                models = genai.list_models()
                available_models = []
                for model in models:
                    if 'generateContent' in model.supported_generation_methods:
                        available_models.append(model.name)
                print(f"Found {len(available_models)} available models (subset):")
                for model_name in available_models[:5]: # Chỉ in 5 model đầu
                    print(f"   - {model_name}")
            except Exception as test_e:
                print(f"Warning: Could not test API connection: {test_e}")
    except Exception as e:
        print(f"Error configuring Generative AI: {e}")
        GEMINI_AVAILABLE = False

# ==========================================================
# SUPPORTING CLASSES AND LOGIC FUNCTIONS
# ==========================================================

class InteractivePlot:
    # ... (Giữ nguyên toàn bộ class InteractivePlot)
    def __init__(self, ground_pts, wall_1_pts, wall_2_pts, position_y, design_profile=None, show_actual_profile=False):
        if not MATPLOTLIB_AVAILABLE: messagebox.showwarning("Missing Dependency", "matplotlib is required to show cross-sections."); return
        self.fig, self.ax = plt.subplots(figsize=(14, 9))
        self.original_title = f'Interactive 2D Cross-Section at Y ≈ {position_y:.2f}m'
        self.ax.set_title(self.original_title)
        self.draw_data(ground_pts, wall_1_pts, wall_2_pts, design_profile, show_actual_profile)
        self.ax.set_xlabel('X (m)'); self.ax.set_ylabel('Z (m)')
        self.ax.grid(True); self.ax.axis('equal'); self.ax.legend()
        self.mode = None; self.points = []
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        ax_dist = plt.axes([0.7, 0.01, 0.1, 0.05])
        self.btn_dist = MplButton(ax_dist, 'Measure Distance')
        self.btn_dist.on_clicked(lambda event: self.set_mode('distance'))
        plt.show()
    def draw_data(self, ground_pts, wall_1_pts, wall_2_pts, design_profile, show_actual_profile):
        if wall_1_pts.size > 0 and wall_2_pts.size > 0 and wall_1_pts[:, 0].mean() < wall_2_pts[:, 0].mean(): left_wall, right_wall = wall_1_pts, wall_2_pts
        else: left_wall, right_wall = wall_2_pts, wall_1_pts
        self.ax.scatter(ground_pts[:, 0], ground_pts[:, 2], s=2, color='black', picker=5, label='Ground')
        if design_profile is not None and len(design_profile) > 1:
            self.ax.scatter(wall_1_pts[:, 0], wall_1_pts[:, 2], s=2, color='gray'); self.ax.scatter(wall_2_pts[:, 0], wall_2_pts[:, 2], s=2, color='gray', label='Clear')
            self.ax.plot(design_profile[:, 0], design_profile[:, 1], 'g--', linewidth=2, label='Design Profile')
        else:
            self.ax.scatter(left_wall[:, 0], left_wall[:, 2], s=2, color='blue', label='Left Wall'); self.ax.scatter(right_wall[:, 0], right_wall[:, 2], s=2, color='red', label='Right Wall')
        if show_actual_profile and ALPHASHAPE_AVAILABLE:
            all_points_2d = np.vstack((ground_pts[:, [0, 2]], left_wall[:, [0, 2]], right_wall[:, [0, 2]]))
            if len(all_points_2d) > 3:
                try:
                    alpha_shape = alphashape.alphashape(all_points_2d, 0.5)
                    if not alpha_shape.is_empty: x, y = alpha_shape.exterior.coords.xy; self.ax.plot(x, y, color='yellow', linewidth=2, label='Actual Profile')
                except Exception as e: print(f"Could not generate alpha shape: {e}")
    def set_mode(self, mode): self.mode = mode; self.points = []; self.ax.set_title(f"DISTANCE MODE: Select 2 points", fontsize=10, color='green'); self.fig.canvas.draw_idle()
    def onclick(self, event):
        if not self.mode or event.inaxes != self.ax: return
        ix, iy = event.xdata, event.ydata
        self.points.append((ix, iy)); self.ax.plot(ix, iy, 'gx', markersize=10); self.fig.canvas.draw_idle()
        if self.mode == 'distance' and len(self.points) == 2:
            p1, p2 = self.points[0], self.points[1]
            dx = abs(p1[0] - p2[0]); dz = abs(p1[1] - p2[1]); dist = np.sqrt(dx**2 + dz**2)
            self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'g--')
            self.ax.text(np.mean([p1[0], p2[0]]), np.mean([p1[1], p2[1]]), f' H: {dx:.2f}m\n V: {dz:.2f}m\n D: {dist:.2f}m', color='green')
            self.reset_mode()
    def reset_mode(self): self.mode = None; self.points = []; self.ax.set_title(self.original_title, fontsize=12, color='black'); self.fig.canvas.draw_idle()

def analyze_point_cloud(input_path, params, status_callback, progress_callback):
    # ... (Giữ nguyên)
    try:
        status_callback("1. Loading data..."); progress_callback(5)
        with laspy.open(input_path) as f: las = f.read()
        pcd = o3d.geometry.PointCloud(); pcd.points = o3d.utility.Vector3dVector(np.vstack((las.x, las.y, las.z)).T)
        status_callback("2. Scanning and classifying planes..."); progress_callback(15)
        ground_planes, wall_planes = [], []; remaining_cloud = pcd; z_axis = np.array([0, 0, 1]); iteration = 0; max_iterations = 15; min_points_threshold = 5000
        while len(remaining_cloud.points) > min_points_threshold and iteration < max_iterations:
            iteration += 1; progress = 15 + (iteration / max_iterations) * 80; progress_callback(progress); status_callback(f"2.{iteration}. Finding plane...")
            plane_model, inliers = remaining_cloud.segment_plane(params["RANSAC_DISTANCE"], 3, 1000)
            if len(inliers) < 1000: status_callback("No more significant planes found."); break
            num_before = len(remaining_cloud.points); current_plane = remaining_cloud.select_by_index(inliers); remaining_cloud = remaining_cloud.select_by_index(inliers, invert=True)
            if len(remaining_cloud.points) >= num_before: status_callback("Analysis stalled."); break
            angle = np.rad2deg(np.arccos(np.clip(abs(np.dot(plane_model[:3], z_axis)), -1.0, 1.0)))
            if angle < params["GROUND_ANGLE"]: ground_planes.append(current_plane)
            elif angle > params["WALL_ANGLE"]:
                try:
                    height = current_plane.get_max_bound()[2] - current_plane.get_min_bound()[2]
                    if height > params["MIN_WALL_HEIGHT"]: wall_planes.append(current_plane)
                except IndexError: print("Warning: Could not calculate height for a potential wall plane."); continue
        if len(wall_planes) < 2: raise Exception(f"Could not find at least 2 walls meeting criteria.")
        wall_planes.sort(key=lambda x: len(x.points), reverse=True)
        ground_cloud = o3d.geometry.PointCloud()
        if ground_planes:
            for gp in ground_planes: ground_cloud.points.extend(gp.points)
        status_callback("3. Analysis complete. Ready to show results."); progress_callback(100)
        return {"ground": ground_cloud, "wall1": wall_planes[0], "wall2": wall_planes[1]}
    except Exception as e: progress_callback(0); status_callback(f"Error: {e}"); return None

# ==========================================================
# MAIN APPLICATION WINDOW (TKINTER)
# ==========================================================
class AnalysisApp:
    def __init__(self, master):
        # ... (Giữ nguyên)
        self.master = master; master.title("Point Cloud Analysis Tool - Hoàng Anh"); sv_ttk.set_theme("dark")
        window_width, window_height = 850, 800; screen_width, screen_height = master.winfo_screenwidth(), master.winfo_screenheight()
        center_x, center_y = int(screen_width/2 - window_width / 2), int(screen_height/2 - window_height / 2); master.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.create_menu(); self.main_frame = ttk.Frame(master, padding="10"); self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.analysis_results = None; self.file_path = None; self.design_profile = None; self.last_slice_data = None
        self.params = {}; self.status_text = tk.StringVar(value="Please select a .LAS file."); self.show_profile_var = tk.BooleanVar(value=False)
        self.las_header_info = {}; self.current_analysis_params = {}; self.analysis_mode = tk.StringVar(value="tunnel")
        self.create_widgets()

    def create_menu(self):
        # ... (Giữ nguyên)
        menubar = tk.Menu(self.master); help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hướng dẫn", command=self.show_help_dialog); help_menu.add_separator(); help_menu.add_command(label="Giới thiệu", command=self.show_about_dialog)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu); self.master.config(menu=menubar)

    def create_widgets(self):
        # ... (Giữ nguyên)
        content_frame = ttk.Frame(self.main_frame); content_frame.pack(fill=tk.BOTH, expand=True)
        control_frame = ttk.Frame(content_frame); control_frame.pack(fill=tk.X, pady=5, anchor='n')
        self.browse_button = ttk.Button(control_frame, text="📁 Import .LAS", command=self.browse_las_file); self.browse_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.profile_button = ttk.Button(control_frame, text="📐 Import Profile", command=self.import_profile); self.profile_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.analyze_button = ttk.Button(control_frame, text="▶ Start Analysis", command=self.start_analysis_thread, state=tk.DISABLED); self.analyze_button.pack(side=tk.LEFT, padx=5, ipady=5)
        param_frame = ttk.LabelFrame(content_frame, text="Analysis Parameters", padding="10"); param_frame.pack(fill=tk.X, pady=10, anchor='n')
        param_list = {"MIN_WALL_HEIGHT": ("Min Wall Height (m):", "5.0"), "RANSAC_DISTANCE": ("RANSAC Distance (m):", "0.1"), "GROUND_ANGLE": ("Ground Angle (°):", "15.0"), "WALL_ANGLE": ("Wall Angle (°):", "75.0")}
        for i, (key, (text, default_val)) in enumerate(param_list.items()):
            ttk.Label(param_frame, text=text, font=("Segoe UI", 10, "bold")).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            entry = ttk.Entry(param_frame, width=10); entry.grid(row=i, column=1, sticky=tk.W, padx=5, pady=5); entry.insert(0, default_val); self.params[key] = entry
        self.suggest_params_button = ttk.Button(param_frame, text="🤖 AI Suggest", command=self.suggest_parameters_thread, state=tk.DISABLED)
        self.suggest_params_button.grid(row=len(param_list), column=0, columnspan=2, pady=(10,5)) 

        mode_frame = ttk.LabelFrame(content_frame, text="Analysis Mode", padding="10"); mode_frame.pack(fill=tk.X, pady=5, anchor='n')
        ttk.Radiobutton(mode_frame, text="Phân tích Hầm/Hành lang (Đất + 2 Tường)", variable=self.analysis_mode, value="tunnel").pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(mode_frame, text="Giám định Hư hỏng (Bề mặt + Vùng vỡ)", variable=self.analysis_mode, value="damage").pack(anchor=tk.W, padx=5)
        result_frame = ttk.LabelFrame(content_frame, text="Show & Export Results", padding="10"); result_frame.pack(fill=tk.X, pady=10, anchor='n')
        top_row_frame = ttk.Frame(result_frame); top_row_frame.pack(fill=tk.X, pady=(0, 5))
        self.show_3d_button = ttk.Button(top_row_frame, text="Show 3D Points", command=self.show_3d_result, state=tk.DISABLED); self.show_3d_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.reconstruct_3d_button = ttk.Button(top_row_frame, text="Reconstruct 3D Mesh", command=self.reconstruct_3d_mesh, state=tk.DISABLED); self.reconstruct_3d_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.report_button = ttk.Button(top_row_frame, text="🤖 Generate AI Report", command=self.start_generate_report_thread, state=tk.DISABLED); self.report_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.export_profile_btn = ttk.Button(top_row_frame, text="Export 2D Slice...", command=self.export_cross_section, state=tk.DISABLED); self.export_profile_btn.pack(side=tk.RIGHT, padx=5, ipady=5)
        bottom_row_frame = ttk.Frame(result_frame); bottom_row_frame.pack(fill=tk.X)
        ttk.Label(bottom_row_frame, text="Y Position (for 2D Slice):").pack(side=tk.LEFT, padx=(0, 5)); self.slice_pos_entry = ttk.Entry(bottom_row_frame, width=10); self.slice_pos_entry.pack(side=tk.LEFT)
        self.view_slice_btn = ttk.Button(bottom_row_frame, text="View 2D Slice", command=self.view_cross_section_normal, state=tk.DISABLED); self.view_slice_btn.pack(side=tk.LEFT, padx=5)
        self.compare_btn = ttk.Button(bottom_row_frame, text="Compare 2D Profile", command=self.view_cross_section_with_profile, state=tk.DISABLED); self.compare_btn.pack(side=tk.LEFT, padx=5)
        self.profile_checkbox = ttk.Checkbutton(bottom_row_frame, text="Show AlphaShape (2D)", variable=self.show_profile_var, onvalue=True, offvalue=False); self.profile_checkbox.pack(side=tk.LEFT, padx=(10, 5))
        info_frame = ttk.LabelFrame(content_frame, text="Information / Logs", padding="10"); info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, height=8, state=tk.DISABLED); self.info_text.pack(fill=tk.BOTH, expand=True)
        status_label = ttk.Label(self.main_frame, textvariable=self.status_text, font=("Segoe UI", 9, "italic")); status_label.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(5,0))
        self.progress_bar = ttk.Progressbar(self.main_frame, orient='horizontal', mode='determinate'); self.progress_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0,5))
        ai_frame = ttk.LabelFrame(self.main_frame, text="🤖 AI Agent Command", padding="10"); ai_frame.pack(fill=tk.X, pady=(5, 0), padx=10, side=tk.BOTTOM)
        self.ai_entry = ttk.Entry(ai_frame, font=("Segoe UI", 10)); self.ai_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3); self.ai_entry.bind("<Return>", self.start_ai_agent_task)
        self.ai_button = ttk.Button(ai_frame, text="Send Command", command=self.start_ai_agent_task); self.ai_button.pack(side=tk.LEFT, padx=5)
        if not GEMINI_AVAILABLE:
            self.report_button.config(state=tk.DISABLED); self.suggest_params_button.config(state=tk.DISABLED)
            self.ai_entry.insert(0, "AI features disabled (check API key/install)"); self.ai_entry.config(state=tk.DISABLED); self.ai_button.config(state=tk.DISABLED)

    def _show_3d_non_blocking(self, geometries, window_name): # Giữ nguyên
        def run_visualizer(geoms, name): vis = o3d.visualization.Visualizer(); vis.create_window(window_name=name, width=1280, height=720); [vis.add_geometry(g) for g in geoms]; vis.run(); vis.destroy_window()
        threading.Thread(target=run_visualizer, args=(geometries, window_name), daemon=True).start()
    def disable_result_buttons(self): # Giữ nguyên
        self.show_3d_button.config(state=tk.DISABLED); self.reconstruct_3d_button.config(state=tk.DISABLED); self.report_button.config(state=tk.DISABLED)
        self.view_slice_btn.config(state=tk.DISABLED); self.compare_btn.config(state=tk.DISABLED); self.export_profile_btn.config(state=tk.DISABLED)
    def enable_result_buttons(self): # Giữ nguyên
        self.show_3d_button.config(state=tk.NORMAL); self.reconstruct_3d_button.config(state=tk.NORMAL)
        if GEMINI_AVAILABLE: self.report_button.config(state=tk.NORMAL)
        if self.analysis_results and "ground" in self.analysis_results:
             self.view_slice_btn.config(state=tk.NORMAL)
             self.export_profile_btn.config(state=tk.NORMAL)
             if self.design_profile is not None:
                 self.compare_btn.config(state=tk.NORMAL)
        else:
             self.view_slice_btn.config(state=tk.DISABLED)
             self.export_profile_btn.config(state=tk.DISABLED)
             self.compare_btn.config(state=tk.DISABLED)

    def browse_las_file(self):
        # ... (Giữ nguyên)
        path = filedialog.askopenfilename(filetypes=[("LAS Point Cloud", "*.las"), ("All files", "*.*")])
        if path:
            self.file_path = path; self.status_text.set(f"Selected: {os.path.basename(path)}. Ready."); self.analyze_button.config(state=tk.NORMAL); self.disable_result_buttons()
            try:
                with laspy.open(path) as f:
                    header = f.header; self.las_header_info = {"point_count": header.point_count, "y_min": header.y_min, "y_max": header.y_max}
                    middle_y = (header.y_min + header.y_max) / 2.0; self.slice_pos_entry.delete(0, tk.END); self.slice_pos_entry.insert(0, f"{middle_y:.2f}")
                    info_str = (f"Point Count: {header.point_count:,}\nY-Range: [{header.y_min:.2f}, {header.y_max:.2f}]"); self.update_info_text(info_str)
                    if GEMINI_AVAILABLE: self.suggest_params_button.config(state=tk.NORMAL)
            except Exception as e: self.update_info_text(f"Error reading file:\n{e}"); self.suggest_params_button.config(state=tk.DISABLED)

    def start_analysis_thread(self): # Giữ nguyên
        if not self.file_path: return
        try: self.current_analysis_params = {key: float(entry.get()) for key, entry in self.params.items()}
        except ValueError: messagebox.showerror("Error", "Invalid parameter value."); return
        self.browse_button.config(state=tk.DISABLED); self.analyze_button.config(state=tk.DISABLED); self.disable_result_buttons(); self.safe_update_progress(0)
        mode = self.analysis_mode.get()
        if mode == "tunnel": threading.Thread(target=self.run_analysis, args=(self.current_analysis_params,), daemon=True).start()
        elif mode == "damage": threading.Thread(target=self.run_damage_analysis, args=(self.current_analysis_params,), daemon=True).start()

    def start_generate_report_thread(self): # Giữ nguyên
        if not self.analysis_results: messagebox.showwarning("No Data", "Run analysis first."); return
        if not GEMINI_AVAILABLE: messagebox.showwarning("AI Disabled", "AI features disabled."); return
        self.status_text.set("🤖 Generating AI report..."); threading.Thread(target=self.generate_report, daemon=True).start()

    def generate_report(self): # *** ĐÃ CẬP NHẬT MODEL LIST ***
        model_names = ['gemini-2.5-flash', 'gemini-2.5-pro-preview-05-06', 'gemini-2.5-pro-preview-03-25']
        model = None; response = None; report_mode_name = "Unknown"; report_findings = "Analysis results N/A."; parameters_to_show = f"- RANSAC Distance: {self.current_analysis_params.get('RANSAC_DISTANCE', 'N/A')} m"
        if self.analysis_results:
            if "ground" in self.analysis_results: report_mode_name = "Tunnel/Corridor"; report_findings = "Segmented ground + 2 walls."; parameters_to_show += (f"\n- Min Wall H: {self.current_analysis_params.get('MIN_WALL_HEIGHT', 'N/A')} m\n- Ground Angle: {self.current_analysis_params.get('GROUND_ANGLE', 'N/A')}°\n- Wall Angle: {self.current_analysis_params.get('WALL_ANGLE', 'N/A')}°")
            elif "main_surface" in self.analysis_results: report_mode_name = "Damage Inspect"; num_damage = len(self.analysis_results['damage_points'].points); report_findings = f"Isolated main surface, found {num_damage:,} potential damaged points."
            if "damage_bbox" in self.analysis_results and self.analysis_results["damage_bbox"]: bbox = self.analysis_results["damage_bbox"].get_oriented_bounding_box(); ext = bbox.extent; report_findings += (f"\n- Approx. BBox (LxWxH): {ext[0]:.2f}x{ext[1]:.2f}x{ext[2]:.2f}m")
        prompt = f"""Report:\n**Info:** File: {os.path.basename(self.file_path) if self.file_path else 'N/A'}, Mode: {report_mode_name}, Points: {self.las_header_info.get('point_count', 'N/A'):,}, Y-Range: [{self.las_header_info.get('y_min', 'N/A'):.2f}m, {self.las_header_info.get('y_max', 'N/A'):.2f}m]\n**Params:** {parameters_to_show}\n**Outcome:** Status: OK. Findings: {report_findings}\n**Instructions:** Formal summary with headings (Summary, Mode, Params, Results), brief interpretation."""
        last_err = "No connection."
        for name in model_names:
            try: self.safe_update_status(f"Generating report with {name}..."); model = genai.GenerativeModel(name); response = model.generate_content(prompt); self.safe_update_status(f"Report generated with {name}"); break
            except Exception as e: last_err = str(e); self._handle_gemini_error(e, name); continue
        if response and model:
            try: self.master.after(0, self.show_report_window, response.text)
            except Exception as e: self.master.after(0, messagebox.showerror, "AI Report Error", f"Display error: {e}")
        else:
            if not any(kw in last_err.lower() for kw in ["quota", "429", "permission", "403", "expired", "invalid"]): self.master.after(0, messagebox.showerror, "AI Report Error", f"Could not generate: {last_err}")
        self.safe_update_status("AI Report task done.")

    def show_report_window(self, report_text): # Giữ nguyên
        win = tk.Toplevel(self.master); win.title("AI Report"); win.geometry("600x500"); win.transient(self.master)
        txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Segoe UI", 10)); txt.pack(fill="both", expand=True, padx=10, pady=10); txt.insert(tk.END, report_text); txt.config(state=tk.DISABLED)
        frm = ttk.Frame(win); frm.pack(fill=tk.X, padx=10, pady=(0, 10))
        def copy(): self.master.clipboard_clear(); self.master.clipboard_append(report_text); self.safe_update_status("Report copied.")
        ttk.Button(frm, text="Copy", command=copy).pack(side=tk.LEFT, expand=True); ttk.Button(frm, text="Close", command=win.destroy).pack(side=tk.LEFT, expand=True, padx=5)

    def show_help_dialog(self): # Giữ nguyên
        help_title = "Hướng dẫn - v2.4"; help_text = """Quy trình:\n1. Import .LAS\n2. Chọn Mode\n3. (Tùy chọn) AI Suggest Params\n4. Chỉnh Params (RANSAC Dist quan trọng!)\n5. Start Analysis\n6. Xem Kết quả (3D, Mesh, 2D Slice...)\n7. (Tùy chọn) AI Agent Command (cần đường dẫn đầy đủ)\n8. (Tùy chọn) Generate AI Report"""
        messagebox.showinfo(help_title, help_text)
    def show_about_dialog(self): # Giữ nguyên
        about_title = "Giới thiệu - v2.4"; about_text = """Point Cloud Analysis Tool v2.4\nTác giả: Hoàng Anh (17/10/2025)\n\nTool desktop phân tích LAS, tích hợp AI (Gemini).\n- 2 Mode: Tunnel, Damage Inspect.\n- Hiển thị 3D (Điểm, Mesh, BBox).\n- 2D Slice (Tunnel Mode).\n- AI Suggest Params, AI Agent, AI Report.\n\nLibs: Tkinter, sv_ttk, Laspy, Open3D, NumPy, Matplotlib, Google Generative AI."""
        messagebox.showinfo(about_title, about_text)
    def import_profile(self): # Giữ nguyên
        path = filedialog.askopenfilename(filetypes=[("CSV Profile", "*.csv")])
        if not path: return
        try:
            profile_pts = []
            with open(path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        try:
                            profile_pts.append([float(row[0]), float(row[1])])
                        except ValueError: continue 
            if len(profile_pts) < 2: raise Exception("Not enough valid points.")
            self.design_profile = np.array(profile_pts)
            self.status_text.set(f"Profile loaded: {os.path.basename(path)}")
            if self.analysis_results: self.enable_result_buttons()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load profile: {e}")
            self.design_profile = None

    def update_info_text(self, text): self.info_text.config(state=tk.NORMAL); self.info_text.delete("1.0", tk.END); self.info_text.insert(tk.END, text); self.info_text.config(state=tk.DISABLED) # Giữ nguyên

    def show_3d_result(self): # Giữ nguyên
        if not self.analysis_results: messagebox.showwarning("No Data", "Run analysis first."); return
        geoms = []; title = "3D Result"
        if "ground" in self.analysis_results: self.safe_update_status("Displaying Tunnel results..."); g=self.analysis_results['ground'].paint_uniform_color([.5,.5,.5]); w1=self.analysis_results['wall1'].paint_uniform_color([1,0,0]); w2=self.analysis_results['wall2'].paint_uniform_color([0,0,1]); geoms=[g,w1,w2]; title="3D Tunnel"
        elif "main_surface" in self.analysis_results: self.safe_update_status("Displaying Damage results..."); s=self.analysis_results['main_surface'].paint_uniform_color([.8,.8,.8]); d=self.analysis_results['damage_points'].paint_uniform_color([1,0,0]); geoms=[s,d]; title="3D Damage"
        if "damage_bbox" in self.analysis_results and self.analysis_results["damage_bbox"]: geoms.append(self.analysis_results["damage_bbox"])
        if not geoms: messagebox.showwarning("No Data", "Results empty/invalid."); return
        self._show_3d_non_blocking(geoms, title)

    def reconstruct_3d_mesh(self): # Giữ nguyên
        if not self.analysis_results: messagebox.showwarning("No Data", "Run analysis first"); return
        try:
            pcd = o3d.geometry.PointCloud(); vox=0.1; alp=0.5; self.safe_update_status("Combining points..."); self.safe_update_progress(10)
            if "ground" in self.analysis_results: pcd+=self.analysis_results["ground"]; pcd+=self.analysis_results["wall1"]; pcd+=self.analysis_results["wall2"]; vox=0.1; alp=0.5
            elif "main_surface" in self.analysis_results: pcd+=self.analysis_results["main_surface"]; pcd+=self.analysis_results["damage_points"]; vox=0.05; alp=0.2
            else: messagebox.showerror("Error", "Unknown results."); self.safe_update_status("Error: Unknown results."); return
            if not pcd.has_points(): messagebox.showwarning("No Data", "No points for mesh."); self.safe_update_status("No points for mesh."); return
            self.safe_update_status("Downsampling..."); self.safe_update_progress(30); down_pcd = pcd.voxel_down_sample(vox)
            self.safe_update_status("Creating mesh..."); self.safe_update_progress(70); mesh = None
            if down_pcd.has_points():
                try: self.safe_update_status("Estimating normals..."); down_pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=vox*2, max_nn=30)); self.safe_update_status("Ball Pivoting..."); radii=[vox, vox*2]; mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(down_pcd, o3d.utility.DoubleVector(radii))
                except Exception as bp_e: print(f"BP failed: {bp_e}"); self.safe_update_status("BP failed. Trying Alpha..."); mesh = None
                if mesh and mesh.has_triangles(): mesh.remove_degenerate_triangles(); mesh.remove_duplicated_triangles(); mesh.remove_duplicated_vertices(); mesh.remove_non_manifold_edges()
                if not mesh or not mesh.has_triangles(): self.safe_update_status("Trying Alpha Shape..."); mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(down_pcd, alp); mesh.compute_vertex_normals()
                if not mesh or not mesh.has_triangles(): raise Exception("Mesh failed.")
                self.safe_update_progress(100); self.safe_update_status("Mesh created. Displaying...")
                self._show_3d_non_blocking([mesh], "3D Mesh")
            else: raise Exception("Downsample empty.")
        except Exception as e: messagebox.showerror("Error", f"Mesh failed: {e}"); self.safe_update_status(f"Mesh failed: {e}"); self.safe_update_progress(0)

    def _view_cross_section(self, with_profile): # Giữ nguyên
        if not self.analysis_results: messagebox.showwarning("No Data", "Run analysis first"); return "Error: No results."
        if "ground" not in self.analysis_results: messagebox.showwarning("Not Applicable", "2D Slice only for Tunnel mode."); return "Error: Not applicable."
        try:
            y=float(self.slice_pos_entry.get()); tol=0.5; g=self._extract_slice_points(self.analysis_results["ground"], y, tol); w1=self._extract_slice_points(self.analysis_results["wall1"], y, tol); w2=self._extract_slice_points(self.analysis_results["wall2"], y, tol)
            if len(g)==0 and len(w1)==0 and len(w2)==0: messagebox.showwarning("No Data", f"No points near Y={y}"); return f"Warn: No points near Y={y}"
            self.last_slice_data = {"y": y, "g": g, "w1": w1, "w2": w2}; d = self.design_profile if with_profile else None; s = self.show_profile_var.get()
            InteractivePlot(g, w1, w2, y, d, s); return None
        except ValueError: messagebox.showerror("Error", "Invalid Y"); return "Error: Invalid Y"
        except Exception as e: messagebox.showerror("Error", f"Slice failed: {e}"); return f"Error: {e}"
    def _extract_slice_points(self, pcd, y, tol): # Giữ nguyên
        if not pcd.has_points(): return np.array([])
        pts = np.asarray(pcd.points); mask = np.abs(pts[:, 1] - y) <= tol; return pts[mask]
    def view_cross_section_normal(self): self._view_cross_section(False) # Giữ nguyên
    def view_cross_section_with_profile(self): # Giữ nguyên
        if self.design_profile is None: messagebox.showwarning("No Data", "Import Profile first."); return
        self._view_cross_section(True)
    def export_cross_section(self): # Giữ nguyên
        if not self.last_slice_data:
            if not self.analysis_results or "ground" not in self.analysis_results: messagebox.showwarning("Not Applicable", "Export only for Tunnel mode after viewing slice."); return
            else: messagebox.showwarning("No Data", "View slice first."); return
        fp = filedialog.asksaveasfilename(title="Save Slice Data", defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if fp:
            try:
                with open(fp, 'w', newline='') as f:
                    w = csv.writer(f); w.writerow(['Y', self.last_slice_data['y']]); w.writerow(['Tol', 0.5]); w.writerow([]); w.writerow(['X', 'Z', 'Type'])
                    for pt in self.last_slice_data['g']: w.writerow([pt[0], pt[2], 'Ground'])
                    for pt in self.last_slice_data['w1']: w.writerow([pt[0], pt[2], 'Wall1'])
                    for pt in self.last_slice_data['w2']: w.writerow([pt[0], pt[2], 'Wall2'])
                self.update_info_text(f"Slice exported: {fp}")
            except Exception as e: messagebox.showerror("Error", f"Export failed: {e}")

    def run_analysis(self, params): # Giữ nguyên
        results = analyze_point_cloud(self.file_path, params, self.safe_update_status, self.safe_update_progress)
        if results: self.analysis_results = results; self.master.after(0, self.enable_result_buttons)
        else: self.master.after(0, lambda: messagebox.showerror("Analysis Error", "Tunnel analysis failed."))
        def finalize(): self.browse_button.config(state=tk.NORMAL); self.analyze_button.config(state=tk.NORMAL); self.master.after(2000, lambda: self.safe_update_progress(0))
        self.master.after(0, finalize)
    def run_damage_analysis(self, params): # Giữ nguyên
        try:
            self.safe_update_status("1. Loading..."); self.safe_update_progress(5)
            with laspy.open(self.file_path) as f: las = f.read()
            pcd = o3d.geometry.PointCloud(); pcd.points = o3d.utility.Vector3dVector(np.vstack((las.x, las.y, las.z)).T)
            self.safe_update_status("2. Finding surface..."); self.safe_update_progress(30)
            plane, inliers = pcd.segment_plane(params["RANSAC_DISTANCE"], 3, 1000)
            if len(inliers) < 1000: raise Exception("No significant surface.")
            surf = pcd.select_by_index(inliers); dmg = pcd.select_by_index(inliers, invert=True)
            n_dmg = len(dmg.points); info = f"Found {n_dmg:,} damaged/outlier points."
            bbox = None
            if dmg.has_points():
                try:
                    bbox = dmg.get_oriented_bounding_box(); ext = bbox.extent; info += (f"\nApprox Dim (LxWxH): {ext[0]:.2f}x{ext[1]:.2f}x{ext[2]:.2f}m"); bbox.color = (1,0,0)
                except Exception as be: print(f"BBox failed: {be}")
            self.safe_update_status(f"3. Done. {info.splitlines()[0]}"); self.safe_update_progress(100)
            self.analysis_results = {"main_surface": surf, "damage_points": dmg, "damage_bbox": bbox}
            self.master.after(0, self.update_info_text, info); self.master.after(0, self.enable_result_buttons)
        except Exception as e: self.safe_update_progress(0); self.safe_update_status(f"Damage analysis error: {e}"); self.master.after(0, lambda: messagebox.showerror("Error", f"Damage analysis failed: {e}"))
        def finalize(): self.browse_button.config(state=tk.NORMAL); self.analyze_button.config(state=tk.NORMAL); self.master.after(2000, lambda: self.safe_update_progress(0))
        self.master.after(0, finalize)

    def safe_update_status(self, msg): self.master.after(0, lambda: self.status_text.set(msg)) # Giữ nguyên
    def safe_update_progress(self, val): self.master.after(0, lambda: self.progress_bar.config(value=val)) # Giữ nguyên

    # --- AI AGENT FUNCTIONS ---
    def start_ai_agent_task(self, event=None): # Giữ nguyên
        prompt = self.ai_entry.get()
        if not prompt: return
        if not GEMINI_AVAILABLE: messagebox.showwarning("AI Disabled", "Check API key/install."); return
        self.status_text.set(f"🤖 Agent processing..."); self.ai_entry.delete(0, tk.END); self.ai_button.config(state=tk.DISABLED)
        threading.Thread(target=self._run_agent_logic, args=(prompt,), daemon=True).start()
    
    def _run_agent_logic(self, prompt): # *** ĐÃ CẬP NHẬT MODEL LIST ***
        models = ['gemini-2.5-flash', 'gemini-2.5-pro-preview-05-06', 'gemini-2.5-pro-preview-03-25']
        model=None; response=None; avail=[]
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods: avail.append(m.name)
            if avail: models = [m for m in models if m in avail] + [m for m in avail if m not in models]
        except Exception as e: print(f"List models failed: {e}")
        last_err = "No connection."
        
        agent_tools = [
            self._agent_tool_run_analysis,
            self._agent_tool_run_damage_analysis,
            self._agent_tool_view_2d_slice,
            self._agent_tool_show_3d
        ]

        for name in models:
            try:
                self.safe_update_status(f"Agent trying {name}..."); 
                model = genai.GenerativeModel(name, tools=agent_tools)
                response = model.generate_content(prompt); 
                self.safe_update_status(f"Connected with {name}"); break
            except Exception as e: last_err = str(e); self._handle_gemini_error(e, name); continue
        
        if response and model:
            try:
                part = response.candidates[0].content.parts[0]
                if hasattr(part, 'function_call'): 
                    fc = part.function_call; 
                    args_dict = {k: v for k, v in fc.args.items()}
                    self.master.after(0, self._execute_agent_command, fc.name, args_dict)
                elif hasattr(part, 'text'): 
                    self.safe_update_status(f"🤖 AI: {response.text}"); 
                    self.master.after(0, lambda: self.ai_button.config(state=tk.NORMAL))
                else: 
                    self.safe_update_status("Error: Unexpected AI response."); 
                    self.master.after(0, lambda: self.ai_button.config(state=tk.NORMAL))
            except Exception as e: self.safe_update_status(f"Response processing error: {e}"); self.master.after(0, lambda: self.ai_button.config(state=tk.NORMAL))
        else:
            if not any(kw in last_err.lower() for kw in ["quota", "429", "permission", "403", "expired", "invalid"]): self.safe_update_status(f"AI connection failed: {last_err}")
            self.master.after(0, lambda: self.ai_button.config(state=tk.NORMAL))

    def _execute_agent_command(self, name, args): # Giữ nguyên
        tool_map = {"run_analysis": self._agent_tool_run_analysis, "run_damage_analysis": self._agent_tool_run_damage_analysis, "view_2d_slice": self._agent_tool_view_2d_slice, "show_3d": self._agent_tool_show_3d}
        if name in tool_map:
            try:
                msg = tool_map[name](**args)
                if isinstance(msg, str):
                    self.safe_update_status(f"🤖 Agent: {msg}") 
            except Exception as e:
                self.safe_update_status(f"Error executing '{name}': {e}")
        else:
            self.safe_update_status(f"Error: Unknown command '{name}'.")
        
        self.ai_button.config(state=tk.NORMAL)

    def _handle_gemini_error(self, e, model_name): # Giữ nguyên
        err = str(e)
        if "404" in err and "models" in err: self.safe_update_status(f"{model_name} unavailable, trying next...")
        elif "quota" in err.lower() or "429" in err: self.safe_update_status("API quota exceeded. Try later."); return True 
        elif "permission" in err.lower() or "403" in err or "API key expired" in err or "API_KEY_INVALID" in err: self.safe_update_status("Invalid/Expired API key or permission."); return True
        else: self.safe_update_status(f"Error with {model_name}: {e}")
        return False 

    # --- AGENT TOOL DEFINITIONS ---
    def _agent_tool_run_analysis(self, file_path: str): # Giữ nguyên
        """Runs TUNNEL analysis (ground + 2 walls) on a .las file."""
        if not os.path.exists(file_path): return f"File not found: '{file_path}'."
        self.file_path = p = file_path; self.analysis_mode.set("tunnel"); self.start_analysis_thread()
        return f"Analyzing '{os.path.basename(p)}' (Tunnel Mode)..."
    def _agent_tool_view_2d_slice(self, y_position: float): # Giữ nguyên
        """Displays 2D slice at Y. Only works for TUNNEL mode."""
        self.slice_pos_entry.delete(0, tk.END); self.slice_pos_entry.insert(0, str(y_position)); return self._view_cross_section(False)
    def _agent_tool_show_3d(self): # Giữ nguyên
        """Shows the 3D visualization of the last analysis result."""
        self.show_3d_result() 
    def _agent_tool_run_damage_analysis(self, file_path: str): # Giữ nguyên
        """Runs DAMAGE ANALYSIS (surface + defects) on a .las file. Use for 'damage', 'inspect', 'crack', etc."""
        if not os.path.exists(file_path): return f"File not found: '{file_path}'."
        self.file_path = p = file_path; self.analysis_mode.set("damage"); self.start_analysis_thread()
        return f"Analyzing DAMAGE on '{os.path.basename(p)}'..."

    # --- HÀM GỢI Ý THAM SỐ (ĐÃ CẬP NHẬT) ---
    def suggest_parameters_thread(self): # *** CẬP NHẬT: Thêm progress bar ***
        if not self.las_header_info: messagebox.showwarning("No Data", "Load .LAS file first."); return
        if not GEMINI_AVAILABLE: messagebox.showwarning("AI Disabled", "AI features disabled."); return
        
        self.status_text.set("🤖 AI suggesting params..."); 
        self.suggest_params_button.config(state=tk.DISABLED)
        
        # BẮT ĐẦU THANH PROGRESS
        self.master.after(0, self.start_indeterminate_progress)
        
        threading.Thread(target=self._suggest_parameters_logic, daemon=True).start()
    
    def _suggest_parameters_logic(self): # *** CẬP NHẬT: Prompt mới, gọi dialog, dừng progress bar ***
        try:
            pc=self.las_header_info.get('point_count', 'N/A')
            ymin=self.las_header_info.get('y_min', 'N/A')
            ymax=self.las_header_info.get('y_max', 'N/A')
            mode=self.analysis_mode.get()
            
            try:
                intro = f"Suggest params for LAS:\n- Pts: {pc:,}\n- Y: [{ymin:.2f}m, {ymax:.2f}m]\n\n"
            except (ValueError, TypeError):
                 intro = f"Suggest params for LAS:\n- Pts: {pc}\n- Y: [{ymin}, {ymax}]\n\n"

            # Cập nhật prompt để yêu cầu lý do
            mode_params = ""
            if mode == "tunnel": 
                mode_params = "RANSAC_DISTANCE, GROUND_ANGLE, WALL_ANGLE, MIN_WALL_HEIGHT"
            elif mode == "damage": 
                mode_params = "RANSAC_DISTANCE"
            else: 
                self.safe_update_status("Error: Unknown mode."); return

            task = f"""Goal: {mode}. Suggest parameters.

RULES:
1. Provide parameters for: {mode_params}.
2. Format EACH line as: PARAM: value.
3. AFTER all parameters, add this exact header: ## Rationale
4. Below the header, explain each choice briefly in bullet points.
"""
            
            prompt = intro + task
            models = ['gemini-2.5-flash', 'gemini-2.5-pro-preview-05-06', 'gemini-2.5-pro-preview-03-25']
            text = None; last_err = None
            
            for name in models:
                try: 
                    self.safe_update_status(f"Requesting suggestions from {name}..."); 
                    m = genai.GenerativeModel(name); 
                    resp = m.generate_content(prompt); 
                    text = resp.text; 
                    self.safe_update_status("Received suggestions."); break
                except Exception as e: 
                    last_err = e; print(f"Suggest fail {name}: {e}"); 
                    self.safe_update_status(f"Failed {name}, trying next..."); 
                    if self._handle_gemini_error(e, name): break 
                    continue
            
            if text:
                # Tách phần tham số và phần lý do
                parts = text.split("## Rationale", 1)
                param_text = parts[0]
                rationale_text = parts[1] if len(parts) > 1 else "No rationale provided by AI."

                sug = self._parse_suggestion_response(param_text) # Hàm parse cũ vẫn hoạt động
                
                if sug: 
                    # Tạo nội dung cho hộp thoại
                    full_message = "🤖 AI đề xuất các tham số sau:\n\n"
                    for k, v in sug.items():
                        full_message += f"  - {k}: {v}\n"
                    full_message += f"\n## Lý do đề xuất\n{rationale_text.strip()}"
                    
                    # Gọi hộp thoại xác nhận thay vì áp dụng trực tiếp
                    self.master.after(0, self.show_suggestion_dialog, sug, full_message)
                else: 
                    self.safe_update_status("AI response unclear.")
            else: 
                msg = f"Suggest failed: {last_err}"; self.safe_update_status(msg)
                if not any(kw in str(last_err).lower() for kw in ["quota", "429", "permission", "403", "expired", "invalid"]):
                    self.master.after(0, messagebox.showerror, "AI Suggest Error", msg)
        
        except Exception as e: 
            msg = f"Suggest error: {e}"; self.safe_update_status(msg); 
            self.master.after(0, messagebox.showerror, "AI Suggest Error", msg)
        finally: 
            # DỪNG THANH PROGRESS
            self.master.after(0, self.stop_indeterminate_progress)
            self.master.after(0, lambda: self.suggest_params_button.config(state=tk.NORMAL))

    def _parse_suggestion_response(self, text): # *** ĐÃ SỬA LỖI LOGIC ***
        """Phân tích văn bản trả về từ AI để lấy giá trị tham số."""
        sug = {}; lines = text.splitlines()
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1); 
                name_raw = parts[0].strip().replace("-", "").upper(); 
                val_str = parts[1].strip().split(" ")[0].replace(",", ".") 
                
                try:
                    val = float(val_str)
                    
                    for key in self.params.keys():
                        if key in name_raw:
                            sug[key] = val
                            break 
                
                except ValueError:
                    continue
        return sug

    def _apply_suggested_parameters(self, suggested_params): # Giữ nguyên
        count = 0
        for key, value in suggested_params.items():
            if key in self.params: 
                entry = self.params[key]; 
                entry.delete(0, tk.END); 
                entry.insert(0, f"{value:.2f}"); 
                count +=1
        if count > 0: self.safe_update_status(f"Applied {count} AI suggested params.")
        else: self.safe_update_status("Could not apply suggestions.")

    # --- (HÀM MỚI) CÁC HÀM HỖ TRỢ CHO PROGRESS BAR VÀ DIALOG ---
    
    def start_indeterminate_progress(self):
        """Kích hoạt progress bar ở chế độ quay vòng."""
        try:
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
        except Exception as e:
            print(f"Error starting progress bar: {e}")

    def stop_indeterminate_progress(self):
        """Dừng progress bar và reset về 0."""
        try:
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate', value=0)
        except Exception as e:
            print(f"Error stopping progress bar: {e}")

    def show_suggestion_dialog(self, suggestions, message):
        """Hiển thị hộp thoại Yes/No với các đề xuất của AI."""
        # Tùy chỉnh tiêu đề và nội dung nút
        answer = messagebox.askyesno(
            title="Áp dụng đề xuất của AI?", 
            message=message,
            detail="Chọn 'Yes' để áp dụng các giá trị này, 'No' để hủy."
        )
        
        if answer:
            self._apply_suggested_parameters(suggestions) # Hàm này đã có sẵn
        else:
            self.safe_update_status("Đã hủy bỏ đề xuất của AI.")

if __name__ == '__main__':
    root = tk.Tk()
    app = AnalysisApp(root)
    root.mainloop()