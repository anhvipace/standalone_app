"""
Plotting utilities for point cloud visualization.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button as MplButton
import alphashape
from typing import Optional, Tuple, List

from utils.logger import get_logger

logger = get_logger(__name__)


class InteractivePlot:
    """Interactive 2D cross-section plot with measurement capabilities."""
    
    def __init__(self, ground_pts: np.ndarray, wall_1_pts: np.ndarray, 
                 wall_2_pts: np.ndarray, position_y: float, 
                 design_profile: Optional[np.ndarray] = None, 
                 show_actual_profile: bool = False):
        """
        Initialize interactive plot.
        
        Args:
            ground_pts: Ground points array (N, 3)
            wall_1_pts: Wall 1 points array (N, 3)
            wall_2_pts: Wall 2 points array (N, 3)
            position_y: Y position for cross-section
            design_profile: Design profile points (N, 2) [x, z]
            show_actual_profile: Whether to show actual profile
        """
        self.fig, self.ax = plt.subplots(figsize=(14, 9))
        self.original_title = f'Interactive 2D Cross-Section at Y ≈ {position_y:.2f}m'
        self.ax.set_title(self.original_title)
        
        self.draw_data(ground_pts, wall_1_pts, wall_2_pts, design_profile, show_actual_profile)
        
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Z (m)')
        self.ax.grid(True)
        self.ax.axis('equal')
        self.ax.legend()

        self.mode = None
        self.points = []
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)

        # Add measurement button
        ax_dist = plt.axes([0.7, 0.01, 0.1, 0.05])
        self.btn_dist = MplButton(ax_dist, 'Measure Distance')
        self.btn_dist.on_clicked(lambda event: self.set_mode('distance'))
        
        plt.show()

    def draw_data(self, ground_pts: np.ndarray, wall_1_pts: np.ndarray, 
                  wall_2_pts: np.ndarray, design_profile: Optional[np.ndarray], 
                  show_actual_profile: bool):
        """Draw the point cloud data on the plot."""
        # Determine left and right walls based on X position
        if (wall_1_pts.size > 0 and wall_2_pts.size > 0 and 
            wall_1_pts[:, 0].mean() < wall_2_pts[:, 0].mean()):
            left_wall, right_wall = wall_1_pts, wall_2_pts
        else:
            left_wall, right_wall = wall_2_pts, wall_1_pts

        # Plot ground points
        self.ax.scatter(ground_pts[:, 0], ground_pts[:, 2], s=2, color='black', 
                       picker=5, label='Ground')

        # Plot walls
        if design_profile is not None and len(design_profile) > 1:
            self.ax.scatter(wall_1_pts[:, 0], wall_1_pts[:, 2], s=2, color='gray')
            self.ax.scatter(wall_2_pts[:, 0], wall_2_pts[:, 2], s=2, color='gray', 
                           label='Clear')
            self.ax.plot(design_profile[:, 0], design_profile[:, 1], 'g--', 
                        linewidth=2, label='Design Profile')
        else:
            self.ax.scatter(left_wall[:, 0], left_wall[:, 2], s=2, color='blue', 
                           label='Left Wall')
            self.ax.scatter(right_wall[:, 0], right_wall[:, 2], s=2, color='red', 
                           label='Right Wall')

        # Show actual profile if requested
        if show_actual_profile:
            self._draw_actual_profile(ground_pts, left_wall, right_wall)

    def _draw_actual_profile(self, ground_pts: np.ndarray, left_wall: np.ndarray, 
                           right_wall: np.ndarray):
        """Draw actual profile using alpha shape."""
        try:
            all_points_2d = np.vstack((
                ground_pts[:, [0, 2]], 
                left_wall[:, [0, 2]], 
                right_wall[:, [0, 2]]
            ))
            
            if len(all_points_2d) > 3:
                alpha_shape = alphashape.alphashape(all_points_2d, 0.5)
                if not alpha_shape.is_empty:
                    x, y = alpha_shape.exterior.coords.xy
                    self.ax.plot(x, y, color='yellow', linewidth=2, 
                               label='Actual Profile')
        except Exception as e:
            logger.warning(f"Could not generate alpha shape: {e}")

    def set_mode(self, mode: str):
        """Set measurement mode."""
        self.mode = mode
        self.points = []
        self.ax.set_title(f"DISTANCE MODE: Select 2 points", fontsize=10, color='green')
        self.fig.canvas.draw_idle()

    def onclick(self, event):
        """Handle mouse click events."""
        if not self.mode or event.inaxes != self.ax:
            return
            
        ix, iy = event.xdata, event.ydata
        self.points.append((ix, iy))
        self.ax.plot(ix, iy, 'gx', markersize=10)
        self.fig.canvas.draw_idle()
        
        if self.mode == 'distance' and len(self.points) == 2:
            self._calculate_distance()

    def _calculate_distance(self):
        """Calculate and display distance between two points."""
        p1, p2 = self.points[0], self.points[1]
        dx = abs(p1[0] - p2[0])
        dz = abs(p1[1] - p2[1])
        dist = np.sqrt(dx**2 + dz**2)
        
        # Draw line and text
        self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'g--')
        self.ax.text(np.mean([p1[0], p2[0]]), np.mean([p1[1], p2[1]]),
                    f' H: {dx:.2f}m\n V: {dz:.2f}m\n D: {dist:.2f}m', 
                    color='green')
        
        self.reset_mode()

    def reset_mode(self):
        """Reset measurement mode."""
        self.mode = None
        self.points = []
        self.ax.set_title(self.original_title, fontsize=12, color='black')
        self.fig.canvas.draw_idle()


def create_3d_visualization(geometries: List, window_name: str = "3D Visualization"):
    """
    Create 3D visualization in a separate thread.
    
    Args:
        geometries: List of Open3D geometries to visualize
        window_name: Name of the visualization window
    """
    import threading
    import open3d as o3d
    
    def run_visualizer(geoms, name):
        try:
            vis = o3d.visualization.Visualizer()
            vis.create_window(window_name=name, width=1280, height=720)
            for geom in geoms:
                vis.add_geometry(geom)
            vis.run()
            vis.destroy_window()
        except Exception as e:
            logger.error(f"3D visualization error: {e}")
    
    threading.Thread(target=run_visualizer, args=(geometries, window_name), daemon=True).start()
