"""主窗口 —— 整合所有面板。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from calib.config import AppConfig
from calib.core.session import CalibrationSession
from calib.ui.calibration_panel import CalibrationPanel
from calib.ui.camera_panel import CameraPanel
from calib.ui.pattern_selector import PatternSelector
from calib.ui.widgets.image_viewer import ImageViewer


class MainWindow(QMainWindow):
    """标定工具主窗口。"""

    def __init__(self, config: AppConfig):
        super().__init__()
        self._config = config
        self._session = CalibrationSession(config)

        self.setWindowTitle(config.ui.window_title)
        self.resize(config.ui.window_width, config.ui.window_height)

        self._setup_ui()
        self._setup_statusbar()
        self._connect_signals()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        left_panel = QVBoxLayout()
        self._image_viewer = ImageViewer()
        left_panel.addWidget(self._image_viewer)

        right_panel = QVBoxLayout()
        self._pattern_selector = PatternSelector()
        right_panel.addWidget(self._pattern_selector)

        self._camera_panel = CameraPanel()
        self._camera_panel.set_preview_fps(self._config.ui.preview_max_fps)
        right_panel.addWidget(self._camera_panel)

        self._calibration_panel = CalibrationPanel()
        self._calibration_panel.set_default_export_format(
            self._config.export.default_format
        )
        right_panel.addWidget(self._calibration_panel)
        right_panel.addStretch()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter)

    def _setup_statusbar(self) -> None:
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("就绪")

    def _connect_signals(self) -> None:
        self._camera_panel.connect_requested.connect(self._on_connect_camera)
        self._camera_panel.disconnect_requested.connect(self._on_disconnect_camera)
        self._camera_panel.start_acquisition_requested.connect(self._on_start_acquisition)
        self._camera_panel.stop_acquisition_requested.connect(self._on_stop_acquisition)
        self._camera_panel.preview_frame.connect(self._image_viewer.set_frame)
        self._camera_panel.images_acquired.connect(self._on_images_acquired)

        self._calibration_panel.calibrate_requested.connect(self._on_calibrate)
        self._calibration_panel.export_requested.connect(self._on_export)
        self._calibration_panel.calibration_finished.connect(self._on_calibration_finished)

    def _on_connect_camera(self) -> None:
        brand = self._camera_panel.selected_brand()
        try:
            self._session.connect_camera(brand)
            self._camera_panel.on_connected(brand)
            self._statusbar.showMessage(f"已连接: {brand}")
            self._camera_panel.start_preview(self._session.camera)
        except Exception as e:
            QMessageBox.critical(self, "相机错误", str(e))
            self._statusbar.showMessage(f"连接失败: {e}")

    def _on_disconnect_camera(self) -> None:
        self._camera_panel.stop_preview()
        self._session.disconnect_camera()
        self._camera_panel.on_disconnected()
        self._statusbar.showMessage("已断开")

    def _on_start_acquisition(self) -> None:
        if self._session.camera is None or not self._session.camera.is_open():
            QMessageBox.warning(self, "提示", "请先连接相机")
            return

        ptype = self._pattern_selector.selected_type()
        self._session.create_pattern(
            ptype,
            self._pattern_selector.rows(),
            self._pattern_selector.cols(),
            self._pattern_selector.square_size(),
        )
        strategy = self._session.create_acquisition_strategy()

        self._camera_panel.start_acquisition(self._session.pattern, strategy)
        self._statusbar.showMessage("自动采集中...")
        self._calibration_panel.on_acquisition_started()

    def _on_stop_acquisition(self) -> None:
        self._camera_panel.stop_acquisition()
        self._statusbar.showMessage("已停止采集")

    def _on_images_acquired(self, images: list) -> None:
        self._session.set_acquired_images(images)
        self._statusbar.showMessage(f"采集完成，共 {len(images)} 张")
        self._calibration_panel.on_acquisition_finished(len(images))

    def _on_calibrate(self) -> None:
        if not self._session.acquired_images or self._session.pattern is None:
            QMessageBox.warning(self, "提示", "请先采集标定图片")
            return

        calibrator = self._session.create_mono_calibrator()
        self._calibration_panel.start_calibration(
            self._session.acquired_images,
            self._session.pattern,
            calibrator,
        )
        self._statusbar.showMessage("标定计算中...")

    def _on_calibration_finished(self, result) -> None:
        self._session.set_calib_result(result)
        if result.success:
            self._statusbar.showMessage(
                f"标定完成 | 平均重投影误差: {result.mean_error:.4f} px"
            )
        else:
            self._statusbar.showMessage(f"标定失败: {result.message}")

    def _on_export(self) -> None:
        if self._session.calib_result is None or not self._session.calib_result.success:
            QMessageBox.warning(self, "提示", "无有效的标定结果可导出")
            return

        fmt = self._calibration_panel.export_format()
        try:
            path = self._session.export_calibration(fmt)
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))
            return

        self._statusbar.showMessage(f"已导出: {path}")
        QMessageBox.information(self, "导出成功", f"标定结果已保存至:\n{path}")
