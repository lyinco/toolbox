"""相机控制面板。"""

import numpy as np
from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from calib.core.acquisition.base import AcquisitionStrategy
from calib.core.camera.factory import CameraFactory
from calib.core.camera.interface import CameraInterface
from calib.core.pattern.base import CalibPatternBase
from calib.worker.acquisition_worker import AcquisitionController
from calib.worker.camera_worker import CameraWorker


class CameraPanel(QGroupBox):
    """相机连接、断开、预览、采集控制。"""

    connect_requested = Signal()
    disconnect_requested = Signal()
    start_acquisition_requested = Signal()
    stop_acquisition_requested = Signal()
    preview_frame = Signal(np.ndarray)
    images_acquired = Signal(list)

    def __init__(self, parent=None):
        super().__init__("相机", parent)
        self._camera_worker: CameraWorker | None = None
        self._acq_thread: QThread | None = None
        self._acq_controller: AcquisitionController | None = None
        self._acq_active = False
        self._preview_fps = 30

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        brand_row = QHBoxLayout()
        brand_row.addWidget(QLabel("品牌:"))
        self._brand_combo = QComboBox()
        for b in CameraFactory.registered_brands():
            self._brand_combo.addItem(b.title(), b)
        brand_row.addWidget(self._brand_combo)
        layout.addLayout(brand_row)

        btn_row = QHBoxLayout()
        self._connect_btn = QPushButton("连接")
        self._connect_btn.clicked.connect(self.connect_requested.emit)
        self._disconnect_btn = QPushButton("断开")
        self._disconnect_btn.setEnabled(False)
        self._disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        btn_row.addWidget(self._connect_btn)
        btn_row.addWidget(self._disconnect_btn)
        layout.addLayout(btn_row)

        acq_row = QHBoxLayout()
        self._start_acq_btn = QPushButton("开始采集")
        self._start_acq_btn.setEnabled(False)
        self._start_acq_btn.clicked.connect(self.start_acquisition_requested.emit)
        self._stop_acq_btn = QPushButton("停止采集")
        self._stop_acq_btn.setEnabled(False)
        self._stop_acq_btn.clicked.connect(self._on_stop_acquisition)
        acq_row.addWidget(self._start_acq_btn)
        acq_row.addWidget(self._stop_acq_btn)
        layout.addLayout(acq_row)

        self._acq_progress = QProgressBar()
        self._acq_progress.setVisible(False)
        layout.addWidget(self._acq_progress)

        self._status_label = QLabel("未连接")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

    def set_preview_fps(self, fps: int) -> None:
        self._preview_fps = max(1, fps)

    def selected_brand(self) -> str:
        return self._brand_combo.currentData()

    def on_connected(self, brand: str) -> None:
        self._connect_btn.setEnabled(False)
        self._disconnect_btn.setEnabled(True)
        self._start_acq_btn.setEnabled(True)
        self._status_label.setText(f"已连接: {brand}")

    def on_disconnected(self) -> None:
        self._connect_btn.setEnabled(True)
        self._disconnect_btn.setEnabled(False)
        self._start_acq_btn.setEnabled(False)
        self._stop_acq_btn.setEnabled(False)
        self._acq_progress.setVisible(False)
        self._status_label.setText("未连接")

    def start_preview(self, camera: CameraInterface) -> None:
        self._camera_worker = CameraWorker(camera)
        self._camera_worker.set_fps_limit(self._preview_fps)
        self._camera_worker.frame_ready.connect(self._on_preview_frame)
        self._camera_worker.start()

    def stop_preview(self) -> None:
        self._restore_preview_only()
        if self._camera_worker:
            self._camera_worker.stop()
            self._camera_worker.wait(3000)
            self._camera_worker = None

    def _on_preview_frame(self, frame: np.ndarray) -> None:
        if not self._acq_active:
            self.preview_frame.emit(frame)

    def start_acquisition(
        self,
        pattern: CalibPatternBase,
        strategy: AcquisitionStrategy,
    ) -> None:
        if self._camera_worker is None:
            return

        self._restore_preview_only()
        self._acq_active = True
        self._stop_acq_btn.setEnabled(True)
        self._acq_progress.setVisible(True)
        target = getattr(strategy, "target_count", 20)
        self._acq_progress.setMaximum(target)
        self._acq_progress.setValue(0)

        self._acq_thread = QThread()
        self._acq_controller = AcquisitionController(pattern, strategy)
        self._acq_controller.moveToThread(self._acq_thread)

        self._camera_worker.frame_ready.disconnect(self._on_preview_frame)
        self._camera_worker.frame_ready.connect(
            self._acq_controller.process_frame,
            Qt.ConnectionType.QueuedConnection,
        )
        self._acq_controller.preview_frame.connect(self.preview_frame.emit)
        self._acq_controller.progress_updated.connect(self._on_acq_progress)
        self._acq_controller.finished_signal.connect(self._on_acquisition_complete)
        self._acq_controller.status_message.connect(self._status_label.setText)

        self._acq_thread.started.connect(self._acq_controller.start)
        self._acq_thread.start()

    def stop_acquisition(self) -> None:
        if self._acq_controller and self._acq_active:
            self._acq_controller.stop()
        else:
            self._restore_preview_only()

    def _on_acq_progress(self, current: int, target: int) -> None:
        self._acq_progress.setMaximum(target)
        self._acq_progress.setValue(current)

    def _on_stop_acquisition(self) -> None:
        self.stop_acquisition()
        self.stop_acquisition_requested.emit()

    def _restore_preview_only(self) -> None:
        if self._camera_worker and self._acq_controller:
            try:
                self._camera_worker.frame_ready.disconnect(self._acq_controller.process_frame)
            except (TypeError, RuntimeError):
                pass
            self._camera_worker.frame_ready.connect(self._on_preview_frame)

        if self._acq_thread:
            self._acq_thread.quit()
            self._acq_thread.wait(3000)
            self._acq_thread = None
            self._acq_controller = None

        self._acq_active = False
        self._stop_acq_btn.setEnabled(False)
        self._acq_progress.setVisible(False)

    def _on_acquisition_complete(self, images: list) -> None:
        self._status_label.setText(f"采集完成: {len(images)} 张")
        self._restore_preview_only()
        self.images_acquired.emit(images)
