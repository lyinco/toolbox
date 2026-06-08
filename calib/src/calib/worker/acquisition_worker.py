"""自动采集控制器（运行于独立 QThread，避免阻塞 UI）。"""
import cv2
from typing import Optional

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

from calib.core.acquisition.base import AcquisitionStrategy
from calib.core.pattern.base import CalibPatternBase


class AcquisitionController(QObject):
    """在后台线程中检测标定板并驱动采集策略。"""

    progress_updated = Signal(int, int)   # 当前张数, 目标张数
    preview_frame = Signal(np.ndarray)    # 带角点叠加的预览帧
    finished_signal = Signal(list)        # 采集到的 BGR 图像列表
    status_message = Signal(str)

    def __init__(
        self,
        pattern: CalibPatternBase,
        strategy: AcquisitionStrategy,
        parent=None,
    ):
        super().__init__(parent)
        self._pattern = pattern
        self._strategy = strategy
        self._acquired: list[np.ndarray] = []
        self._running = False

    def start(self) -> None:
        self._strategy.reset()
        self._acquired.clear()
        self._running = True
        target = getattr(self._strategy, "target_count", 20)
        self.status_message.emit("开始自动采集...")
        self.progress_updated.emit(0, target)

    def stop(self) -> None:
        """手动停止采集并发出已采集列表。"""
        if not self._running:
            return
        self._running = False
        images = list(self._acquired)
        self.finished_signal.emit(images)
        self.status_message.emit(f"采集已停止，共 {len(images)} 张")

    @Slot(np.ndarray)
    def process_frame(self, frame: np.ndarray) -> None:
        if not self._running:
            return

        raw = frame
        display = frame.copy()

        raw = cv2.imread('tests/data/charuo.jpg')
        print('process_frame: raw shape:', raw.shape)
        corners, cids = self._pattern.detect(raw)

        print('detected corners:', corners)
        print('detected cids:', cids)
        if cids is not None:
            display = self._pattern.draw(display, corners)

        if self._strategy.should_acquire(raw, corners):
            self._acquired.append(raw.copy())

        target = getattr(self._strategy, "target_count", 20)
        self.progress_updated.emit(self._strategy.acquired_count, target)
        self.preview_frame.emit(display)

        if self._strategy.is_done:
            self._finish()

    def _finish(self) -> None:
        self._running = False
        images = list(self._acquired)
        self.finished_signal.emit(images)
        self.status_message.emit(f"采集完成，共 {len(images)} 张")
