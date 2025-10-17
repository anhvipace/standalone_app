"""
PointCloudTool: Unified API and CLI for point cloud analysis

Features (from standalone_app):
- Load LAS, quick header info
- Plane segmentation (ground/walls) with Open3D RANSAC
- 3D visualization (non-blocking)
- Mesh reconstruction and export
- 2D cross-section interactive plotting and CSV export
- Optional AI report via Google Generative AI

Public API (importable):
- PointCloudTool(config)  # holds params and state
- load_las(path) -> dict(header)
- analyze(params) -> dict(ground, wall1, wall2)
- visualize_3d()
- reconstruct_mesh(alpha=0.5, outfile="reconstructed_mesh.obj") -> str
- cross_section(y, tol=0.5, with_profile=None, show_actual=False)
- export_cross_section_csv(outfile)
- generate_ai_report() -> str

CLI:
  python -m tool.pointcloud_tool --file data.las --analyze --show3d
"""
from __future__ import annotations

import os
import csv
import threading
from dataclasses import dataclass
from typing import Optional, Dict, Any

import numpy as np
import laspy
import open3d as o3d

# Optional imports
try:
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button as MplButton
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False

try:
    import alphashape
    ALPHASHAPE_AVAILABLE = True
except Exception:
    ALPHASHAPE_AVAILABLE = False

try:
    import google.generativeai as genai
    GOOGLE_GENAI_AVAILABLE = True
except Exception:
    GOOGLE_GENAI_AVAILABLE = False


@dataclass
class AnalysisParams:
    min_wall_height: float = 5.0
    ransac_distance: float = 0.1
    ground_angle_deg: float = 15.0
    wall_angle_deg: float = 75.0


class PointCloudTool:
    def __init__(self, params: Optional[AnalysisParams] = None) -> None:
        self.params = params or AnalysisParams()
        self.file_path: Optional[str] = None
        self.header_info: Dict[str, Any] = {}
        self.results: Optional[Dict[str, o3d.geometry.PointCloud]] = None
        self.last_slice: Optional[Dict[str, Any]] = None

        # Configure AI if available
        self._ai_ready = False
        if GOOGLE_GENAI_AVAILABLE:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    self._ai_ready = True
                except Exception:
                    self._ai_ready = False

    # ----------------------- Core IO -----------------------
    def load_las(self, path: str) -> Dict[str, Any]:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"LAS file not found: {path}")
        with laspy.open(path) as f:
            header = f.header
            self.header_info = {
                "name": os.path.basename(path),
                "point_count": header.point_count,
                "y_min": header.y_min,
                "y_max": header.y_max,
            }
        self.file_path = path
        return dict(self.header_info)

    # ----------------------- Analysis ---------------------
    def analyze(self, progress_cb=None, status_cb=None) -> Dict[str, o3d.geometry.PointCloud]:
        if not self.file_path:
            raise RuntimeError("No LAS file loaded")

        def _status(msg):
            if status_cb:
                status_cb(msg)

        def _progress(v):
            if progress_cb:
                progress_cb(v)

        _status("1. Loading data...")
        _progress(5)
        with laspy.open(self.file_path) as f:
            las = f.read()
        points = np.vstack((las.x, las.y, las.z)).T
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)

        _status("2. Scanning and classifying planes...")
        _progress(15)
        ground_planes, wall_planes = [], []
        remaining_cloud = pcd
        z_axis = np.array([0.0, 0.0, 1.0])

        iteration = 0
        max_iterations = 15
        while len(remaining_cloud.points) > 20000 and iteration < max_iterations:
            iteration += 1
            _progress(15 + (iteration / max_iterations) * 80)
            _status(f"2.{iteration}. Finding plane...")

            plane_model, inliers = remaining_cloud.segment_plane(
                self.params.ransac_distance, 3, 1000
            )
            if len(inliers) < 1000:
                _status("No more significant planes found.")
                break

            num_before = len(remaining_cloud.points)
            current_plane = remaining_cloud.select_by_index(inliers)
            remaining_cloud = remaining_cloud.select_by_index(inliers, invert=True)
            if len(remaining_cloud.points) >= num_before:
                _status("Analysis stalled.")
                break

            angle = np.rad2deg(
                np.arccos(np.clip(abs(np.dot(plane_model[:3], z_axis)), -1.0, 1.0))
            )
            if angle < self.params.ground_angle_deg:
                ground_planes.append(current_plane)
            elif angle > self.params.wall_angle_deg:
                height = (
                    current_plane.get_max_bound()[2]
                    - current_plane.get_min_bound()[2]
                )
                if height > self.params.min_wall_height:
                    wall_planes.append(current_plane)

        if len(wall_planes) < 2:
            raise RuntimeError("Could not find at least 2 walls meeting criteria.")

        wall_planes.sort(key=lambda x: len(x.points), reverse=True)
        ground_cloud = o3d.geometry.PointCloud()
        for gp in ground_planes:
            ground_cloud.points.extend(gp.points)

        self.results = {"ground": ground_cloud, "wall1": wall_planes[0], "wall2": wall_planes[1]}
        _status("3. Analysis complete. Ready to show results.")
        _progress(100)
        return self.results

    # ----------------------- Visualization ----------------
    def _show_3d_non_blocking(self, geometries, window_name: str) -> None:
        def run_visualizer(geoms, name):
            vis = o3d.visualization.Visualizer()
            vis.create_window(window_name=name, width=1280, height=720)
            for geom in geoms:
                vis.add_geometry(geom)
            vis.run()
            vis.destroy_window()

        threading.Thread(target=run_visualizer, args=(geometries, window_name), daemon=True).start()

    def visualize_3d(self) -> None:
        if not self.results:
            raise RuntimeError("No analysis results to visualize")
        geometries = []
        if len(self.results["ground"].points) > 0:
            ground_pcd = self.results["ground"]
            ground_pcd.paint_uniform_color([0.5, 0.5, 0.5])
            geometries.append(ground_pcd)
        if len(self.results["wall1"].points) > 0:
            wall1_pcd = self.results["wall1"]
            wall1_pcd.paint_uniform_color([1, 0, 0])
            geometries.append(wall1_pcd)
        if len(self.results["wall2"].points) > 0:
            wall2_pcd = self.results["wall2"]
            wall2_pcd.paint_uniform_color([0, 0, 1])
            geometries.append(wall2_pcd)
        self._show_3d_non_blocking(geometries, "3D Point Cloud Analysis")

    # ----------------------- Mesh -------------------------
    def reconstruct_mesh(self, alpha: float = 0.5, outfile: str = "reconstructed_mesh.obj") -> str:
        if not self.results:
            raise RuntimeError("No analysis results to reconstruct from")
        combined = self.results["ground"] + self.results["wall1"] + self.results["wall2"]
        down = combined.voxel_down_sample(voxel_size=0.1)
        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(down, alpha=alpha)
        o3d.io.write_triangle_mesh(outfile, mesh)
        return outfile

    # ----------------------- Cross-section ----------------
    def cross_section(self, y_position: float, tolerance: float = 0.5,
                      with_profile: Optional[np.ndarray] = None, show_actual: bool = False) -> Dict[str, Any]:
        if not self.results:
            raise RuntimeError("No analysis results available")
        def _extract(pcd: o3d.geometry.PointCloud):
            if len(pcd.points) == 0:
                return np.array([])
            pts = np.asarray(pcd.points)
            mask = np.abs(pts[:, 1] - y_position) <= tolerance
            return pts[mask]
        ground_pts = _extract(self.results["ground"])
        wall1_pts = _extract(self.results["wall1"])
        wall2_pts = _extract(self.results["wall2"])
        self.last_slice = {
            "y_position": y_position,
            "ground_pts": ground_pts,
            "wall1_pts": wall1_pts,
            "wall2_pts": wall2_pts,
        }
        if MATPLOTLIB_AVAILABLE:
            self._plot_cross_section(ground_pts, wall1_pts, wall2_pts, y_position,
                                     with_profile, show_actual)
        return dict(self.last_slice)

    def _plot_cross_section(self, ground_pts, wall1_pts, wall2_pts, position_y,
                             design_profile=None, show_actual_profile=False) -> None:
        if not MATPLOTLIB_AVAILABLE:
            return
        fig, ax = plt.subplots(figsize=(14, 9))
        title = f"Interactive 2D Cross-Section at Y ≈ {position_y:.2f}m"
        ax.set_title(title)

        # Normalize left/right
        if wall1_pts.size > 0 and wall2_pts.size > 0 and wall1_pts[:, 0].mean() < wall2_pts[:, 0].mean():
            left_wall, right_wall = wall1_pts, wall2_pts
        else:
            left_wall, right_wall = wall2_pts, wall1_pts

        ax.scatter(ground_pts[:, 0], ground_pts[:, 2], s=2, color='black', picker=5, label='Ground')

        if design_profile is not None and len(design_profile) > 1:
            ax.scatter(wall1_pts[:, 0], wall1_pts[:, 2], s=2, color='gray')
            ax.scatter(wall2_pts[:, 0], wall2_pts[:, 2], s=2, color='gray', label='Clear')
            ax.plot(design_profile[:, 0], design_profile[:, 1], 'g--', linewidth=2, label='Design Profile')
        else:
            ax.scatter(left_wall[:, 0], left_wall[:, 2], s=2, color='blue', label='Left Wall')
            ax.scatter(right_wall[:, 0], right_wall[:, 2], s=2, color='red', label='Right Wall')

        if show_actual_profile and ALPHASHAPE_AVAILABLE:
            all_pts_2d = np.vstack((ground_pts[:, [0, 2]], left_wall[:, [0, 2]], right_wall[:, [0, 2]]))
            if len(all_pts_2d) > 3:
                try:
                    a_shape = alphashape.alphashape(all_pts_2d, 0.5)
                    if not a_shape.is_empty:
                        x, y = a_shape.exterior.coords.xy
                        ax.plot(x, y, color='yellow', linewidth=2, label='Actual Profile')
                except Exception:
                    pass

        ax.set_xlabel('X (m)'); ax.set_ylabel('Z (m)')
        ax.grid(True); ax.axis('equal'); ax.legend()

        # Distance measure button
        if MATPLOTLIB_AVAILABLE:
            points = []
            def onclick(event):
                if event.inaxes != ax:
                    return
                ix, iy = event.xdata, event.ydata
                points.append((ix, iy)); ax.plot(ix, iy, 'gx', markersize=10)
                fig.canvas.draw_idle()
                if len(points) == 2:
                    p1, p2 = points[0], points[1]
                    dx = abs(p1[0] - p2[0]); dz = abs(p1[1] - p2[1])
                    dist = np.sqrt(dx*dx + dz*dz)
                    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'g--')
                    ax.text((p1[0]+p2[0])/2, (p1[1]+p2[1])/2,
                            f'H: {dx:.2f}m\nV: {dz:.2f}m\nD: {dist:.2f}m', color='green')
                    fig.canvas.mpl_disconnect(cid)
            cid = fig.canvas.mpl_connect('button_press_event', onclick)
            ax_btn = plt.axes([0.7, 0.01, 0.1, 0.05])
            btn = MplButton(ax_btn, 'Measure Distance')
            btn.on_clicked(lambda _e: None)
            plt.show()

    def export_cross_section_csv(self, outfile: str) -> str:
        if not self.last_slice:
            raise RuntimeError("No cross-section available")
        with open(outfile, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['X', 'Z', 'Type'])
            for pt in self.last_slice['ground_pts']:
                writer.writerow([pt[0], pt[2], 'Ground'])
            for pt in self.last_slice['wall1_pts']:
                writer.writerow([pt[0], pt[2], 'Wall1'])
            for pt in self.last_slice['wall2_pts']:
                writer.writerow([pt[0], pt[2], 'Wall2'])
        return outfile

    # ----------------------- AI report --------------------
    def generate_ai_report(self) -> str:
        if not self._ai_ready:
            raise RuntimeError("Google API key not configured or google-generativeai not available")
        if not self.file_path:
            raise RuntimeError("No LAS file loaded")
        model = genai.GenerativeModel('models/gemini-flash-latest')
        prompt = f"""
As a professional engineering assistant, write a concise technical summary report based on the following point cloud analysis data:

File Name: {os.path.basename(self.file_path)}
Total Points: {self.header_info.get('point_count', 'N/A')}
Y-Axis Range: [{self.header_info.get('y_min', 'N/A')}, {self.header_info.get('y_max', 'N/A')}]

Analysis Parameters Used:
- Minimum Wall Height: {self.params.min_wall_height} m
- RANSAC Distance: {self.params.ransac_distance} m
- Ground Angle Threshold: {self.params.ground_angle_deg} degrees
- Wall Angle Threshold: {self.params.wall_angle_deg} degrees
"""
        response = model.generate_content(prompt)
        return response.text


def _parse_cli_args(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="PointCloudTool CLI")
    p.add_argument('--file', required=True, help='Path to LAS file')
    p.add_argument('--analyze', action='store_true', help='Run analysis')
    p.add_argument('--show3d', action='store_true', help='Show 3D visualization')
    p.add_argument('--mesh', action='store_true', help='Reconstruct mesh')
    p.add_argument('--cross', type=float, help='Show cross-section at Y')
    p.add_argument('--export-csv', help='Export last cross-section to CSV')
    p.add_argument('--alpha', type=float, default=0.5, help='Alpha for mesh reconstruction')
    return p.parse_args(argv)


def main(argv=None):
    args = _parse_cli_args(argv)
    tool = PointCloudTool()
    tool.load_las(args.file)
    if args.analyze:
        tool.analyze()
    if args.show3d:
        tool.visualize_3d()
    if args.mesh:
        out = tool.reconstruct_mesh(alpha=args.alpha)
        print(f"Mesh saved: {out}")
    if args.cross is not None:
        tool.cross_section(args.cross)
    if args.export_csv:
        out_csv = tool.export_cross_section_csv(args.export_csv)
        print(f"Cross-section exported: {out_csv}")


if __name__ == '__main__':  # pragma: no cover
    main()


