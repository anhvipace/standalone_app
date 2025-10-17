import numpy as np
import os

# Try to import langchain tool decorator
try:
    from langchain.agents import tool
except ImportError:
    # Fallback decorator if langchain is not available
    def tool(func):
        return func

# Tool backend (unified implementation)
try:
    from tool.pointcloud_tool import PointCloudTool, AnalysisParams
except Exception:
    PointCloudTool = None  # Fallback; functions will guard
    AnalysisParams = None

# Biến toàn cục để lưu trạng thái, giống như bộ nhớ tạm của Agent
ANALYSIS_RESULTS = None
LAS_HEADER_INFO = None
_TOOL_INSTANCE = None
_CURRENT_FILE = None

@tool
def load_las_file(file_path: str) -> str:
    """
    Tải và đọc thông tin cơ bản từ một file .las.
    Đây phải là bước đầu tiên trong mọi quy trình phân tích.
    """
    global LAS_HEADER_INFO, _TOOL_INSTANCE, _CURRENT_FILE
    if not os.path.exists(file_path):
        return f"Lỗi: Không tìm thấy file tại đường dẫn '{file_path}'."
    
    try:
        if PointCloudTool is None:
            return "Lỗi: Backend tool chưa sẵn sàng (thiếu module tool.pointcloud_tool)."
        if _TOOL_INSTANCE is None:
            _TOOL_INSTANCE = PointCloudTool()
        header = _TOOL_INSTANCE.load_las(file_path)
        LAS_HEADER_INFO = {
            "point_count": header.get("point_count"),
            "y_min": header.get("y_min"),
            "y_max": header.get("y_max"),
        }
        _CURRENT_FILE = file_path
        return (
            f"Thành công: Đã tải file '{os.path.basename(file_path)}' với "
            f"{LAS_HEADER_INFO['point_count']:,} điểm. Dữ liệu đã sẵn sàng để phân tích."
        )
    except Exception as e:
        return f"Lỗi: Không thể đọc file .las. Chi tiết: {e}"

@tool
def run_analysis(min_wall_height: float, ransac_distance: float, ground_angle: float, wall_angle: float) -> str:
    """
    Chạy thuật toán phân tích chính trên file .las đã được tải để phân loại mặt đất và tường.
    Cần gọi `load_las_file` trước khi chạy hàm này.
    """
    global ANALYSIS_RESULTS, _TOOL_INSTANCE
    if LAS_HEADER_INFO is None or _TOOL_INSTANCE is None:
        return "Lỗi: Chưa có file .las nào được tải. Hãy dùng công cụ `load_las_file` trước."

    try:
        params = AnalysisParams(
            min_wall_height=float(min_wall_height),
            ransac_distance=float(ransac_distance),
            ground_angle_deg=float(ground_angle),
            wall_angle_deg=float(wall_angle),
        )
        _TOOL_INSTANCE.params = params
        results = _TOOL_INSTANCE.analyze()
        ANALYSIS_RESULTS = results
        ground_n = len(results["ground"].points)
        wall_n = len(results["wall1"].points) + len(results["wall2"].points)
        return (
            f"Phân tích thành công. Đã tìm thấy {ground_n:,} điểm đất và {wall_n:,} điểm tường."
        )

    except Exception as e:
        return f"Phân tích thất bại với lỗi: {e}"

@tool
def reconstruct_and_save_3d_mesh(output_filename: str) -> str:
    """
    Tái tạo một mô hình 3D mesh từ kết quả phân tích và lưu nó ra file.
    Cần chạy `run_analysis` thành công trước.
    """
    global _TOOL_INSTANCE
    if ANALYSIS_RESULTS is None or _TOOL_INSTANCE is None:
        return "Lỗi: Chưa có kết quả phân tích. Hãy chạy `run_analysis` trước."
        
    try:
        _TOOL_INSTANCE.reconstruct_mesh(outfile=output_filename)
        return f"Thành công: Đã tạo và lưu mô hình 3D mesh tại '{output_filename}'."
    except Exception as e:
        return f"Lỗi khi tái tạo mesh: {e}"