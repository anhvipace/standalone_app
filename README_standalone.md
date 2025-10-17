# Point Cloud Analysis Tool - Standalone Version

Ứng dụng phân tích point cloud LAS hoàn chỉnh với giao diện đồ họa và tính năng AI.

## 🚀 **Tính năng chính**

### **Phân tích Point Cloud**
- ✅ Đọc và xử lý file LAS/LAZ
- ✅ Phân loại mặt đất và tường bằng RANSAC
- ✅ Tạo mô hình 3D mesh
- ✅ Visualization 3D tương tác

### **Mặt cắt ngang 2D**
- ✅ Xem mặt cắt ngang tại vị trí Y bất kỳ
- ✅ Đo khoảng cách tương tác
- ✅ So sánh với profile thiết kế
- ✅ Tạo alpha shape profile thực tế

### **AI & Báo cáo**
- ✅ Tạo báo cáo kỹ thuật tự động (cần API key)
- ✅ Phân tích thông minh kết quả
- ✅ Export dữ liệu ra CSV

### **Giao diện người dùng**
- ✅ Giao diện hiện đại với dark theme
- ✅ Progress tracking real-time
- ✅ Menu system hoàn chỉnh
- ✅ Error handling thông minh

## 📦 **Cài đặt**

### **Cách 1: Tự động (Khuyến nghị)**
```bash
python run_app.py
```
Script sẽ tự động kiểm tra và cài đặt dependencies.

### **Cách 2: Thủ công**
```bash
# Cài đặt dependencies
pip install -r requirements_standalone.txt

# Chạy ứng dụng
python standalone_app.py
```

## 🔑 **Cấu hình API Key (Tùy chọn)**

Để sử dụng tính năng AI Report:

1. **Lấy API key**: Truy cập https://aistudio.google.com/
2. **Cài đặt biến môi trường**:
   ```bash
   # Windows
   set GOOGLE_API_KEY=your_api_key_here
   
   # Linux/Mac
   export GOOGLE_API_KEY=your_api_key_here
   ```

## 🎯 **Hướng dẫn sử dụng**

### **1. Import dữ liệu**
- Click "📁 Import .LAS" để chọn file LAS/LAZ
- Thông tin file sẽ hiển thị tự động

### **2. Cấu hình tham số**
- **Min Wall Height**: Chiều cao tường tối thiểu (m)
- **RANSAC Distance**: Khoảng cách RANSAC (m)
- **Ground Angle**: Góc mặt đất (độ)
- **Wall Angle**: Góc tường (độ)

### **3. Phân tích**
- Click "▶ Start Analysis" để bắt đầu
- Theo dõi tiến trình trên progress bar

### **4. Xem kết quả**
- **Show 3D Points**: Xem point cloud 3D với màu sắc phân loại
- **Reconstruct 3D Mesh**: Tạo và xem mesh 3D
- **🤖 Generate AI Report**: Tạo báo cáo AI (cần API key)

### **5. Mặt cắt ngang**
- Nhập **Y Position** để chọn vị trí mặt cắt
- **View 2D Cross-section**: Xem mặt cắt ngang 2D
- **Compare Profile**: So sánh với profile thiết kế
- **Export Cross-section**: Xuất dữ liệu ra CSV

### **6. Import Profile thiết kế**
- Click "📐 Import Profile" để import file CSV
- Format CSV: X, Z (mỗi dòng một điểm)

## 📊 **Format dữ liệu**

### **File LAS/LAZ**
- Hỗ trợ định dạng LAS và LAZ
- Tự động đọc thông tin header
- Validation file trước khi xử lý

### **Profile CSV**
```
X,Z
-5.0,0.0
-4.0,1.0
0.0,2.0
4.0,1.0
5.0,0.0
```

### **Export CSV**
```
X,Z,Type
-5.0,0.0,Ground
-4.0,1.0,Wall1
0.0,2.0,Wall2
```

## 🛠️ **Troubleshooting**

### **Lỗi thường gặp**

1. **"No points found near Y position"**
   - Thử thay đổi Y position
   - Kiểm tra file LAS có dữ liệu tại vị trí đó

2. **"Could not find at least 2 walls"**
   - Điều chỉnh tham số phân tích
   - Giảm Min Wall Height
   - Tăng RANSAC Distance

3. **"AI Report Error"**
   - Kiểm tra API key đã cài đặt chưa
   - Kiểm tra kết nối internet

### **Performance Tips**

- **File lớn**: Sử dụng voxel downsampling
- **Memory**: Đóng các cửa sổ 3D không cần thiết
- **Speed**: Giảm số iteration RANSAC

## 📁 **Cấu trúc file**

```
├── standalone_app.py          # Ứng dụng chính
├── run_app.py                # Script launcher
├── requirements_standalone.txt # Dependencies
├── README_standalone.md      # Hướng dẫn này
└── u-type_tunnel_0k630 cut_1.las # File mẫu
```

## 🔧 **Dependencies**

- **numpy**: Xử lý số học
- **laspy**: Đọc file LAS/LAZ
- **open3d**: Xử lý 3D và visualization
- **matplotlib**: Vẽ đồ thị 2D
- **alphashape**: Tạo alpha shape
- **sv_ttk**: Modern Tkinter theme
- **google-generativeai**: AI report (tùy chọn)

## 👨‍💻 **Tác giả**

**Hoàng Anh** - Point Cloud Analysis Tool v2.0

## 📄 **License**

MIT License - Sử dụng tự do cho mục đích học tập và nghiên cứu.

## 🆘 **Hỗ trợ**

Nếu gặp vấn đề, hãy kiểm tra:
1. Dependencies đã cài đặt đầy đủ
2. File LAS có định dạng đúng
3. API key (nếu dùng AI Report)
4. Kết nối internet (cho AI features)

---

**Chúc bạn sử dụng hiệu quả! 🎉**


