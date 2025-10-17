
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
from typing import Optional

import sv_ttk

# Import from new structure
try:
    from agent.agent_core import PointCloudAnalysisAgent
    from config import UIConfig, ModelConfig
    from utils.logger import get_logger
    from utils.exceptions import AgentExecutionError
    from utils.file_handler import FileHandler
except ImportError as e:
    print(f"Warning: Could not import from new structure: {e}")
    # Fallback to basic imports
    import logging
    get_logger = lambda name: logging.getLogger(name)
    AgentExecutionError = Exception

class AgentApp:
    def __init__(self, master):
        self.master = master
        master.title("AI Agent - Point Cloud Processor (Enhanced)")
        sv_ttk.set_theme("dark")
        master.geometry("900x700")

        # Initialize components
        self.logger = get_logger(__name__)
        try:
            self.file_handler = FileHandler(master)
        except:
            self.file_handler = None
        self.agent: Optional[PointCloudAnalysisAgent] = None
        self.file_path: Optional[str] = None
        
        # Initialize agent
        self._initialize_agent()

        # --- Giao diện ---
        main_frame = ttk.Frame(master, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Chọn file LAS", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        file_input_frame = ttk.Frame(file_frame)
        file_input_frame.pack(fill=tk.X)
        
        ttk.Label(file_input_frame, text="File LAS:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_input_frame, textvariable=self.file_path_var, 
                                   font=("Segoe UI", 10))
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.browse_button = ttk.Button(file_input_frame, text="Browse", 
                                       command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT)

        # Khung nhập liệu
        input_frame = ttk.LabelFrame(main_frame, text="Mục tiêu cho AI Agent", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        self.goal_entry = ttk.Entry(input_frame, font=("Segoe UI", 10))
        self.goal_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.goal_entry.insert(0, "Phân tích file LAS đã chọn và tạo mô hình 3D mesh")

        self.run_button = ttk.Button(input_frame, text="Bắt đầu", command=self.start_agent_thread)
        self.run_button.pack(side=tk.LEFT)

        # Khung hiển thị quá trình suy nghĩ
        output_frame = ttk.LabelFrame(main_frame, text="Quá trình làm việc của AI", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, relief="flat", font=("Consolas", 9))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        
        # Status and progress
        self.status_var = tk.StringVar(value="Sẵn sàng - Chọn file LAS để bắt đầu")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                font=("Segoe UI", 9, "italic"))
        status_label.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

    def _initialize_agent(self):
        """Initialize the AI agent."""
        try:
            # Try to create agent with new structure
            if 'PointCloudAnalysisAgent' in globals():
                config = ModelConfig()
                self.agent = PointCloudAnalysisAgent(config, self.master)
                self.logger.info("Agent initialized successfully")
            else:
                # Fallback to old structure
                from agent_core import create_agent_executor
                self.agent_executor = create_agent_executor()
                self.agent = None  # Use old agent_executor
                self.logger.info("Agent executor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {e}")
            messagebox.showerror("Lỗi khởi tạo", f"Không thể khởi tạo AI agent: {e}")

    def browse_file(self):
        """Browse and select LAS file."""
        file_path = filedialog.askopenfilename(
            title="Chọn file LAS",
            filetypes=[
                ("LAS files", "*.las"),
                ("LAZ files", "*.laz"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.file_path = file_path
            self.file_path_var.set(file_path)
            
            # Update goal with file name
            file_name = os.path.basename(file_path)
            self.goal_entry.delete(0, tk.END)
            self.goal_entry.insert(0, f"Phân tích file '{file_name}' và tạo mô hình 3D mesh")
            
            # Show file info
            try:
                if hasattr(self, 'file_handler') and self.file_handler:
                    file_info = self.file_handler.get_file_info(file_path)
                    self.status_var.set(f"Đã chọn: {file_info['name']} ({file_info['size_mb']} MB) - Sẵn sàng phân tích")
                    self._update_output(f"File đã chọn: {file_info['name']}\nKích thước: {file_info['size_mb']} MB\n")
                else:
                    # Fallback to basic file info
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    self.status_var.set(f"Đã chọn: {file_name} ({file_size:.2f} MB) - Sẵn sàng phân tích")
                    self._update_output(f"File đã chọn: {file_name}\nKích thước: {file_size:.2f} MB\n")
            except Exception as e:
                self.logger.warning(f"Failed to get file info: {e}")
                # Basic fallback
                file_name = os.path.basename(file_path)
                self.status_var.set(f"Đã chọn: {file_name} - Sẵn sàng phân tích")
                self._update_output(f"File đã chọn: {file_name}\n")

    def start_agent_thread(self):
        goal = self.goal_entry.get()
        if not goal:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mục tiêu")
            return
        
        if not self.file_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn file LAS trước")
            return

        self.run_button.config(state=tk.DISABLED)
        self.browse_button.config(state=tk.DISABLED)
        self.status_var.set("Đang chạy AI Agent...")
        self.progress_bar.config(value=10)
        
        self._update_output(f"Bắt đầu thực hiện mục tiêu: {goal}\n")
        self._update_output(f"File: {os.path.basename(self.file_path)}\n\n")
        
        threading.Thread(target=self.run_agent, args=(goal,), daemon=True).start()

    def run_agent(self, goal):
        """Run the AI agent with enhanced error handling and progress tracking."""
        try:
            # Update progress
            self.master.after(0, lambda: self.progress_bar.config(value=30))
            self.master.after(0, lambda: self.status_var.set("Đang tải file LAS..."))
            
            # Enhance goal with file path
            enhanced_goal = f"{goal}\n\nFile path: {self.file_path}"
            
            # Update progress
            self.master.after(0, lambda: self.progress_bar.config(value=50))
            self.master.after(0, lambda: self.status_var.set("Đang phân tích dữ liệu..."))
            
            # Run agent based on available type
            if self.agent and hasattr(self.agent, 'execute'):
                # New agent structure
                result = self.agent.execute(enhanced_goal)
                final_output = result
            elif hasattr(self, 'agent_executor'):
                # Old agent structure
                result = self.agent_executor.invoke({"input": enhanced_goal})
                final_output = result.get('output', 'Không có kết quả đầu ra.')
            else:
                raise Exception("Không có agent nào được khởi tạo")
            
            # Update progress
            self.master.after(0, lambda: self.progress_bar.config(value=100))
            self.master.after(0, lambda: self.status_var.set("Hoàn thành phân tích"))
            
        except Exception as e:
            self.logger.error(f"Agent execution failed: {e}")
            final_output = f"Đã xảy ra lỗi: {e}"
            self.master.after(0, lambda: self.status_var.set("Lỗi trong quá trình phân tích"))
            self.master.after(0, lambda: self.progress_bar.config(value=0))

        # Update UI
        self.master.after(0, self._update_output, f"\n\n--- KẾT QUẢ CUỐI CÙNG ---\n{final_output}")
        self.master.after(0, self._enable_buttons)

    def _update_output(self, text):
        """Update output text with thread safety."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.config(state=tk.DISABLED)
        self.output_text.see(tk.END) # Cuộn xuống cuối

    def _enable_buttons(self):
        """Re-enable buttons after analysis completion."""
        self.run_button.config(state=tk.NORMAL)
        self.browse_button.config(state=tk.NORMAL)

if __name__ == '__main__':
    root = tk.Tk()
    app = AgentApp(root)
    root.mainloop()