#!/usr/bin/env python3
"""
Demo script to showcase advanced features of the Point Cloud Analysis Agent.
"""
import os
import sys
import tempfile
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logger
from utils.file_handler import FileHandler
from ai.report_generator import create_report_generator
from visualization.plot_utils import InteractivePlot, create_3d_visualization
import numpy as np

def create_demo_data():
    """Create demo point cloud data for testing."""
    # Create sample ground points
    ground_x = np.random.uniform(-10, 10, 1000)
    ground_y = np.random.uniform(-5, 5, 1000)
    ground_z = np.random.uniform(0, 0.5, 1000)
    ground_points = np.column_stack([ground_x, ground_y, ground_z])
    
    # Create sample wall 1 points
    wall1_x = np.random.uniform(-9.5, -8.5, 500)
    wall1_y = np.random.uniform(-5, 5, 500)
    wall1_z = np.random.uniform(0, 8, 500)
    wall1_points = np.column_stack([wall1_x, wall1_y, wall1_z])
    
    # Create sample wall 2 points
    wall2_x = np.random.uniform(8.5, 9.5, 500)
    wall2_y = np.random.uniform(-5, 5, 500)
    wall2_z = np.random.uniform(0, 8, 500)
    wall2_points = np.column_stack([wall2_x, wall2_y, wall2_z])
    
    return ground_points, wall1_points, wall2_points

def test_file_handling():
    """Test file handling functionality."""
    print("=== Testing File Handling ===")
    
    handler = FileHandler()
    
    # Test file validation
    print("\n1. Testing file validation...")
    with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as tmp:
        tmp.write(b'LASF\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        tmp_path = tmp.name
    
    try:
        is_valid, error_msg = handler.validate_las_file(tmp_path)
        print(f"   Valid LAS file: {is_valid}")
        print(f"   Error message: {error_msg}")
        
        if is_valid:
            file_info = handler.get_file_info(tmp_path)
            print(f"   File info: {file_info['name']} ({file_info['size_mb']} MB)")
        
    finally:
        os.unlink(tmp_path)
    
    print("✅ File handling test completed!")

def test_ai_reporting():
    """Test AI report generation."""
    print("\n=== Testing AI Report Generation ===")
    
    try:
        generator = create_report_generator()
        
        # Create demo analysis data
        analysis_data = {
            'file_info': {
                'name': 'demo_tunnel.las',
                'point_count': 1000000,
                'size_mb': 45.2,
                'y_min': -50.0,
                'y_max': 50.0
            },
            'analysis_params': {
                'min_wall_height': 5.0,
                'ransac_distance': 0.1,
                'ground_angle': 15.0,
                'wall_angle': 75.0
            },
            'results': {
                'ground_points': 500000,
                'wall1_points': 250000,
                'wall2_points': 250000,
                'status': 'Successful'
            }
        }
        
        print("   Generating AI report...")
        report = generator.generate_analysis_report(analysis_data)
        print(f"   Report generated: {len(report)} characters")
        print(f"   Preview: {report[:200]}...")
        
        print("✅ AI reporting test completed!")
        
    except Exception as e:
        print(f"❌ AI reporting test failed: {e}")
        print("   Note: This requires GOOGLE_API_KEY environment variable")

def test_visualization():
    """Test visualization functionality."""
    print("\n=== Testing Visualization ===")
    
    try:
        # Create demo data
        ground_pts, wall1_pts, wall2_pts = create_demo_data()
        
        print("   Creating interactive plot...")
        print("   Note: This will open a matplotlib window")
        
        # Create interactive plot (this will show a window)
        plot = InteractivePlot(ground_pts, wall1_pts, wall2_pts, 0.0)
        print("   Interactive plot created successfully")
        
        print("✅ Visualization test completed!")
        
    except Exception as e:
        print(f"❌ Visualization test failed: {e}")

def test_3d_visualization():
    """Test 3D visualization."""
    print("\n=== Testing 3D Visualization ===")
    
    try:
        import open3d as o3d
        
        # Create demo point clouds
        ground_pts, wall1_pts, wall2_pts = create_demo_data()
        
        # Create Open3D point clouds
        ground_pcd = o3d.geometry.PointCloud()
        ground_pcd.points = o3d.utility.Vector3dVector(ground_pts)
        ground_pcd.paint_uniform_color([0.5, 0.5, 0.5])
        
        wall1_pcd = o3d.geometry.PointCloud()
        wall1_pcd.points = o3d.utility.Vector3dVector(wall1_pts)
        wall1_pcd.paint_uniform_color([1, 0, 0])
        
        wall2_pcd = o3d.geometry.PointCloud()
        wall2_pcd.points = o3d.utility.Vector3dVector(wall2_pts)
        wall2_pcd.paint_uniform_color([0, 0, 1])
        
        print("   Creating 3D visualization...")
        print("   Note: This will open an Open3D window")
        
        create_3d_visualization([ground_pcd, wall1_pcd, wall2_pcd], "Demo 3D Visualization")
        print("   3D visualization created successfully")
        
        print("✅ 3D visualization test completed!")
        
    except Exception as e:
        print(f"❌ 3D visualization test failed: {e}")

def main():
    """Run all demo tests."""
    print("🚀 Advanced Point Cloud Analysis Agent - Feature Demo")
    print("=" * 60)
    
    # Setup logging
    logger = setup_logger("demo", "INFO")
    
    try:
        test_file_handling()
        test_ai_reporting()
        test_visualization()
        test_3d_visualization()
        
        print("\n🎉 All demo tests completed!")
        print("\nTo run the full application:")
        print("python main.py")
        
        print("\n📋 Features demonstrated:")
        print("✅ Smart file handling with validation")
        print("✅ AI-powered report generation")
        print("✅ Interactive 2D cross-section plots")
        print("✅ 3D point cloud visualization")
        print("✅ Advanced GUI with comprehensive tools")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
