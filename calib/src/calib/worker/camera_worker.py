"""相机帧抓取工作线程。"""

import time
from typing import Optional

import numpy as np
from PySide6.QtCore import QThread, Signal

from calib.core.camera.interface import CameraInterface


class CameraWorker(QThread):
    """持续抓取相机帧并发送给 UI。"""

    frame_ready = Signal(np.ndarray)  # BGR 图像
    error_occurred = Signal(str)

    def __init__(self, camera: CameraInterface, parent=None):
        super().__init__(parent)
        self._camera = camera
        self._running = False
        self._fps_limit = 30
        self._last_time = 0.0

    def set_fps_limit(self, fps: int) -> None:
        self._fps_limit = max(1, fps)

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        interval = 1.0 / self._fps_limit

        while self._running:
            try:
                frame = self._camera.grab()
                if frame is None:
                    time.sleep(0.01)
                    continue

                now = time.time()
                if now - self._last_time < interval:
                    time.sleep(interval - (now - self._last_time))
                    continue

                self._last_time = now
                self.frame_ready.emit(frame)

            except Exception as e:
                self.error_occurred.emit(f"相机抓取失败: {e}")
                time.sleep(0.1)

        self._camera.close()