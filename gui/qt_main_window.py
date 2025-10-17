from __future__ import annotations

import os
import csv
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFileDialog, QMessageBox, QTextEdit,
    QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout, QLineEdit,
    QGroupBox, QCheckBox, QStatusBar, QProgressBar, QLabel
)

import numpy as np

from tool.pointcloud_tool import PointCloudTool, AnalysisParams


class AnalysisWorker(QObject):
    statusUpdated = Signal(str)
    progressUpdated = Signal(int)
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, tool: PointCloudTool) -> None:
        super().__init__()
        self._tool = tool

    @Slot()
    def run(self) -> None:
        try:
            def _status(msg: str):
                self.statusUpdated.emit(msg)
            def _progress(v: float | int):
                try:
                    self.progressUpdated.emit(int(v))
                except Exception:
                    self.progressUpdated.emit(0)
            results = self._tool.analyze(progress_cb=_progress, status_cb=_status)
            self.finished.emit(results)
        except Exception as e:
            self.failed.emit(str(e))


class QtMainWindow(QMainWindow):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Point Cloud Analysis Tool - Qt UI")
        self.resize(1000, 720)

        # State
        self.tool = PointCloudTool()
        self.design_profile: Optional[np.ndarray] = None
        self.current_params: AnalysisParams = AnalysisParams()

        # UI
        self._setup_menu()
        self._setup_central()
        self._setup_status()

        self._update_buttons_enabled(False)

    # ---------- UI Setup ----------
    def _setup_menu(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        help_menu = menubar.addMenu("Help")

        act_open = QAction("Open LAS...", self)
        act_open.triggered.connect(self.on_open_las)
        file_menu.addAction(act_open)

        act_profile = QAction("Import Profile (CSV)...", self)
        act_profile.triggered.connect(self.on_import_profile)
        file_menu.addAction(act_profile)

        file_menu.addSeparator()
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        act_about = QAction("About", self)
        act_about.triggered.connect(self.on_about)
        help_menu.addAction(act_about)

    def _setup_central(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Controls row
        controls = QHBoxLayout()
        self.btn_analyze = QPushButton("Start Analysis")
        self.btn_analyze.clicked.connect(self.on_start_analysis)
        self.btn_show3d = QPushButton("Show 3D Points")
        self.btn_show3d.clicked.connect(self.on_show3d)
        self.btn_mesh = QPushButton("Reconstruct 3D Mesh")
        self.btn_mesh.clicked.connect(self.on_mesh)
        self.btn_report = QPushButton("Generate AI Report")
        self.btn_report.clicked.connect(self.on_report)

        controls.addWidget(self.btn_analyze)
        controls.addWidget(self.btn_show3d)
        controls.addWidget(self.btn_mesh)
        controls.addWidget(self.btn_report)
        layout.addLayout(controls)

        # Parameters
        params_box = QGroupBox("Analysis Parameters")
        form = QFormLayout(params_box)
        self.ed_min_wall = QLineEdit("5.0")
        self.ed_ransac = QLineEdit("0.1")
        self.ed_ground = QLineEdit("15.0")
        self.ed_wall = QLineEdit("75.0")
        form.addRow("Min Wall Height (m):", self.ed_min_wall)
        form.addRow("RANSAC Distance (m):", self.ed_ransac)
        form.addRow("Ground Angle (°):", self.ed_ground)
        form.addRow("Wall Angle (°):", self.ed_wall)
        layout.addWidget(params_box)

        # Cross-section controls
        xs_row = QHBoxLayout()
        self.ed_ypos = QLineEdit()
        self.ed_ypos.setPlaceholderText("Y position (m)")
        self.chk_actual = QCheckBox("Show Actual Profile")
        self.btn_xs = QPushButton("View Cross-section")
        self.btn_xs.clicked.connect(self.on_cross_section)
        self.btn_export_csv = QPushButton("Export Cross-section CSV")
        self.btn_export_csv.clicked.connect(self.on_export_csv)
        xs_row.addWidget(QLabel("Y:"))
        xs_row.addWidget(self.ed_ypos)
        xs_row.addWidget(self.chk_actual)
        xs_row.addWidget(self.btn_xs)
        xs_row.addWidget(self.btn_export_csv)
        layout.addLayout(xs_row)

        # Info
        self.info = QTextEdit()
        self.info.setReadOnly(True)
        layout.addWidget(self.info, 1)

    def _setup_status(self) -> None:
        sb = QStatusBar(self)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        sb.addPermanentWidget(self.progress, 1)
        self.setStatusBar(sb)

    # ---------- Helpers ----------
    def _update_buttons_enabled(self, enabled: bool) -> None:
        self.btn_analyze.setEnabled(enabled)
        self.btn_show3d.setEnabled(enabled)
        self.btn_mesh.setEnabled(enabled)
        self.btn_report.setEnabled(enabled)
        self.btn_xs.setEnabled(enabled)
        self.btn_export_csv.setEnabled(enabled)

    def _append_info(self, text: str) -> None:
        self.info.append(text)

    # ---------- Menu actions ----------
    @Slot()
    def on_open_las(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open LAS", "", "LAS files (*.las);;All files (*.*)")
        if not path:
            return
        try:
            header = self.tool.load_las(path)
            mid_y = (header.get("y_min", 0.0) + header.get("y_max", 0.0)) / 2.0
            self.ed_ypos.setText(f"{mid_y:.2f}")
            info = (
                f"Loaded: {os.path.basename(path)}\n"
                f"Point Count: {header.get('point_count', 'N/A')}\n"
                f"Y-Range: [{header.get('y_min', 'N/A')}, {header.get('y_max', 'N/A')}]"
            )
            self.info.clear()
            self._append_info(info)
            self.statusBar().showMessage("LAS loaded")
            self._update_buttons_enabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load LAS: {e}")

    @Slot()
    def on_import_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Profile", "", "CSV files (*.csv);;All files (*.*)")
        if not path:
            return
        try:
            rows = []
            with open(path, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        rows.append([float(row[0]), float(row[1])])
            self.design_profile = np.array(rows)
            self._append_info(f"Profile loaded: {len(rows)} points")
            self.statusBar().showMessage("Profile imported")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import profile: {e}")

    # ---------- Analysis ----------
    @Slot()
    def on_start_analysis(self) -> None:
        try:
            params = AnalysisParams(
                min_wall_height=float(self.ed_min_wall.text()),
                ransac_distance=float(self.ed_ransac.text()),
                ground_angle_deg=float(self.ed_ground.text()),
                wall_angle_deg=float(self.ed_wall.text()),
            )
            # Validate
            if params.ransac_distance <= 0:
                raise ValueError("RANSAC Distance must be > 0")
            if not (0.0 <= params.ground_angle_deg <= 90.0):
                raise ValueError("Ground Angle must be between 0 and 90")
            if not (0.0 <= params.wall_angle_deg <= 90.0):
                raise ValueError("Wall Angle must be between 0 and 90")
            if params.min_wall_height <= 0:
                raise ValueError("Min Wall Height must be > 0")
            self.tool.params = params
        except ValueError as ve:
            QMessageBox.warning(self, "Parameter Error", str(ve))
            return
        except Exception as e:
            QMessageBox.warning(self, "Parameter Error", f"Invalid parameters: {e}")
            return

        self._update_buttons_enabled(False)
        self.progress.setValue(0)
        self.statusBar().showMessage("Analyzing…")

        self._thread = QThread(self)
        self._worker = AnalysisWorker(self.tool)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.statusUpdated.connect(self.statusBar().showMessage)
        self._worker.progressUpdated.connect(self.progress.setValue)
        self._worker.finished.connect(self._on_analysis_finished)
        self._worker.failed.connect(self._on_analysis_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.start()

    @Slot(dict)
    def _on_analysis_finished(self, results: Dict[str, Any]) -> None:
        self._append_info("Analysis completed. Results ready.")
        self.statusBar().showMessage("Analysis completed")
        self._update_buttons_enabled(True)

    @Slot(str)
    def _on_analysis_failed(self, err: str) -> None:
        QMessageBox.critical(self, "Analysis Error", err)
        self.statusBar().showMessage("Analysis failed")
        self._update_buttons_enabled(True)
        self.progress.setValue(0)

    # ---------- Actions ----------
    @Slot()
    def on_show3d(self) -> None:
        try:
            self.tool.visualize_3d()
        except Exception as e:
            QMessageBox.warning(self, "Show 3D", f"Failed: {e}")

    @Slot()
    def on_mesh(self) -> None:
        try:
            out = self.tool.reconstruct_mesh(alpha=0.5)
            self._append_info(f"Mesh saved to: {out}")
            self.statusBar().showMessage("Mesh reconstructed")
        except Exception as e:
            QMessageBox.warning(self, "Mesh", f"Failed: {e}")

    @Slot()
    def on_cross_section(self) -> None:
        if not self.tool.results:
            QMessageBox.information(self, "Cross-section", "Run analysis first.")
            return
        try:
            y = float(self.ed_ypos.text())
        except Exception:
            QMessageBox.warning(self, "Cross-section", "Invalid Y value")
            return
        try:
            self.tool.cross_section(y_position=y, tolerance=0.5,
                                    with_profile=self.design_profile,
                                    show_actual=self.chk_actual.isChecked())
            self.statusBar().showMessage("Cross-section shown")
        except Exception as e:
            QMessageBox.warning(self, "Cross-section", f"Failed: {e}")

    @Slot()
    def on_export_csv(self) -> None:
        if not self.tool.last_slice:
            QMessageBox.information(self, "Export CSV", "View a cross-section first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Cross-section", "cross_section.csv", "CSV files (*.csv)")
        if not path:
            return
        try:
            out = self.tool.export_cross_section_csv(path)
            self._append_info(f"Cross-section exported: {out}")
            self.statusBar().showMessage("Cross-section exported")
        except Exception as e:
            QMessageBox.warning(self, "Export CSV", f"Failed: {e}")

    @Slot()
    def on_report(self) -> None:
        try:
            text = self.tool.generate_ai_report()
            # Simple display in a message box for now
            dlg = QMessageBox(self)
            dlg.setWindowTitle("AI Report")
            dlg.setIcon(QMessageBox.Information)
            dlg.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            dlg.setText(text if text else "(Empty report)")
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "AI Report", f"Failed: {e}")

    @Slot()
    def on_about(self) -> None:
        QMessageBox.information(self, "About", "Point Cloud Analysis Tool (Qt UI)\nAuthor: Hoang Anh")



