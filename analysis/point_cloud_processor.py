"""
Point cloud processing and analysis functionality.
"""
import os
from typing import Dict, List, Optional, Tuple
import numpy as np
import laspy
import open3d as o3d
from langchain.agents import tool

from utils.exceptions import (
    FileNotFoundError,
    InvalidFileFormatError,
    AnalysisError,
    MeshReconstructionError
)
from utils.logger import get_logger
from utils.file_handler import FileHandler
from config import AnalysisConfig

logger = get_logger(__name__)


class PointCloudProcessor:
    """Handles point cloud loading, analysis, and processing."""
    
    def __init__(self, config: AnalysisConfig, parent_window=None):
        """
        Initialize the point cloud processor.
        
        Args:
            config: Analysis configuration parameters
            parent_window: Parent window for file dialogs
        """
        self.config = config
        self.parent_window = parent_window
        self.file_handler = FileHandler(parent_window)
        self.current_file_path: Optional[str] = None
        self.header_info: Optional[Dict] = None
        self.analysis_results: Optional[Dict] = None
        
    def load_las_file(self, file_path: str) -> str:
        """
        Load and read basic information from a .las file.
        This must be the first step in any analysis workflow.
        If file is not found, will show dialog to select file.
        
        Args:
            file_path: Path to the .las file
            
        Returns:
            Status message indicating success or failure
            
        Raises:
            FileNotFoundError: If the file doesn't exist and user cancels dialog
            InvalidFileFormatError: If the file format is invalid
        """
        # Try to find the file with dialog support
        actual_file_path = self.file_handler.find_las_file(file_path)
        if not actual_file_path:
            raise FileNotFoundError(f"File not found and no file selected: '{file_path}'")
        
        try:
            with laspy.open(actual_file_path) as f:
                header = f.header
                self.header_info = {
                    "point_count": header.point_count,
                    "x_min": header.x_min,
                    "x_max": header.x_max,
                    "y_min": header.y_min,
                    "y_max": header.y_max,
                    "z_min": header.z_min,
                    "z_max": header.z_max,
                    "file_path": actual_file_path
                }
                self.current_file_path = actual_file_path
                
            # Get file info for logging
            file_info = self.file_handler.get_file_info(actual_file_path)
            
            logger.info(f"Successfully loaded LAS file: {file_info['name']} ({file_info['size_mb']} MB)")
            return (f"Success: Loaded file '{file_info['name']}' with "
                   f"{self.header_info['point_count']:,} points ({file_info['size_mb']} MB). "
                   "Data ready for analysis.")
                   
        except Exception as e:
            logger.error(f"Failed to load LAS file: {e}")
            raise InvalidFileFormatError(f"Cannot read .las file. Details: {e}")
    
    def _load_point_cloud(self) -> o3d.geometry.PointCloud:
        """
        Load point cloud data from the current LAS file.
        
        Returns:
            Open3D point cloud object
            
        Raises:
            AnalysisError: If point cloud loading fails
        """
        if not self.current_file_path:
            raise AnalysisError("No LAS file loaded. Call load_las_file first.")
            
        try:
            with laspy.open(self.current_file_path) as f:
                las = f.read()
            
            # Convert LAS data to Open3D point cloud
            points = np.vstack((las.x, las.y, las.z)).transpose()
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points)
            
            logger.info(f"Loaded point cloud with {len(pcd.points)} points")
            return pcd
            
        except Exception as e:
            logger.error(f"Failed to load point cloud: {e}")
            raise AnalysisError(f"Failed to load point cloud: {e}")
    
    def analyze_point_cloud(self) -> str:
        """
        Run the main analysis algorithm on the loaded point cloud to classify ground and walls.
        
        Returns:
            Status message indicating success or failure
            
        Raises:
            AnalysisError: If analysis fails
        """
        if not self.header_info:
            raise AnalysisError("No LAS file loaded. Call load_las_file first.")
        
        try:
            pcd = self._load_point_cloud()
            
            # Initialize analysis variables
            ground_planes: List[o3d.geometry.PointCloud] = []
            wall_planes: List[o3d.geometry.PointCloud] = []
            remaining_cloud = pcd
            z_axis = np.array([0, 0, 1])
            iteration = 0
            
            logger.info("Starting point cloud analysis...")
            
            # RANSAC plane segmentation
            while len(remaining_cloud.points) > 20000 and iteration < 15:
                iteration += 1
                plane_model, inliers = remaining_cloud.segment_plane(
                    self.config.ransac_distance, 3, 1000
                )
                
                if len(inliers) < 1000:
                    break
                
                current_plane = remaining_cloud.select_by_index(inliers)
                remaining_cloud = remaining_cloud.select_by_index(inliers, invert=True)
                
                # Calculate angle with z-axis
                angle = np.rad2deg(np.arccos(
                    np.clip(abs(np.dot(plane_model[:3], z_axis)), -1.0, 1.0)
                ))
                
                # Classify as ground or wall based on angle
                if angle < self.config.ground_angle:
                    ground_planes.append(current_plane)
                elif angle > self.config.wall_angle:
                    height = (current_plane.get_max_bound()[2] - 
                            current_plane.get_min_bound()[2])
                    if height > self.config.min_wall_height:
                        wall_planes.append(current_plane)
            
            # Validate results
            if len(wall_planes) < 2:
                raise AnalysisError("Analysis failed: Not enough walls found (need at least 2)")
            
            # Sort walls by point count (largest first)
            wall_planes.sort(key=lambda x: len(x.points), reverse=True)
            
            # Combine ground planes
            ground_cloud = o3d.geometry.PointCloud()
            if ground_planes:
                for gp in ground_planes:
                    ground_cloud.points.extend(gp.points)
            
            # Store results
            self.analysis_results = {
                "ground": ground_cloud,
                "wall1": wall_planes[0],
                "wall2": wall_planes[1],
                "all_walls": wall_planes
            }
            
            total_ground_points = len(ground_cloud.points)
            total_wall_points = sum(len(wall.points) for wall in wall_planes[:2])
            
            logger.info(f"Analysis completed: {total_ground_points} ground points, "
                       f"{total_wall_points} wall points")
            
            return (f"Analysis successful. Found {total_ground_points:,} ground points "
                   f"and {total_wall_points:,} wall points.")
                   
        except Exception as e:
            logger.error(f"Point cloud analysis failed: {e}")
            raise AnalysisError(f"Analysis failed: {e}")
    
    def reconstruct_mesh(self, output_filename: str) -> str:
        """
        Reconstruct a 3D mesh from analysis results and save it to file.
        
        Args:
            output_filename: Path where to save the mesh file
            
        Returns:
            Status message indicating success or failure
            
        Raises:
            MeshReconstructionError: If mesh reconstruction fails
        """
        if not self.analysis_results:
            raise MeshReconstructionError("No analysis results available. Run analyze_point_cloud first.")
        
        try:
            # Combine all point clouds
            combined_pcd = (self.analysis_results["ground"] + 
                          self.analysis_results["wall1"] + 
                          self.analysis_results["wall2"])
            
            # Downsample for better performance
            down_pcd = combined_pcd.voxel_down_sample(voxel_size=self.config.voxel_size)
            
            # Create mesh using alpha shape
            mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(
                down_pcd, alpha=self.config.alpha_shape_alpha
            )
            
            # Save mesh
            o3d.io.write_triangle_mesh(output_filename, mesh)
            
            logger.info(f"Mesh saved to: {output_filename}")
            return f"Success: 3D mesh created and saved to '{output_filename}'."
            
        except Exception as e:
            logger.error(f"Mesh reconstruction failed: {e}")
            raise MeshReconstructionError(f"Mesh reconstruction failed: {e}")


# Global processor instance for tool functions
_global_processor: Optional[PointCloudProcessor] = None


def set_global_processor(processor: PointCloudProcessor):
    """Set the global processor instance for tool functions."""
    global _global_processor
    _global_processor = processor


# Tool functions for LangChain agent
@tool
def load_las_file(file_path: str) -> str:
    """
    Load and read basic information from a .las file.
    This must be the first step in any analysis workflow.
    If file is not found, will show dialog to select file.
    """
    global _global_processor
    if _global_processor is None:
        # Create a temporary processor without parent window
        processor = PointCloudProcessor(AnalysisConfig())
    else:
        processor = _global_processor
    
    return processor.load_las_file(file_path)


@tool
def run_analysis(min_wall_height: float = 2.0, 
                ransac_distance: float = 0.1, 
                ground_angle: float = 15.0, 
                wall_angle: float = 60.0) -> str:
    """
    Run the main analysis algorithm on the loaded point cloud to classify ground and walls.
    Call load_las_file before using this tool.
    """
    global _global_processor
    if _global_processor is None:
        raise AnalysisError("No processor available. Call load_las_file first.")
    
    config = AnalysisConfig(
        min_wall_height=min_wall_height,
        ransac_distance=ransac_distance,
        ground_angle=ground_angle,
        wall_angle=wall_angle
    )
    _global_processor.config = config
    return _global_processor.analyze_point_cloud()


@tool
def reconstruct_and_save_3d_mesh(output_filename: str) -> str:
    """
    Reconstruct a 3D mesh from analysis results and save it to file.
    Call run_analysis successfully before using this tool.
    """
    global _global_processor
    if _global_processor is None:
        raise MeshReconstructionError("No processor available. Call load_las_file first.")
    
    return _global_processor.reconstruct_mesh(output_filename)
