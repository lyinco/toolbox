"""通用 USB/UVC 相机实现（stub，供后续扩展）。"""

from typing import Optional

import cv2
import numpy as np

from .interface import CameraInterface


class UVCCamera(CameraInterface):
    """基于 OpenCV VideoCapture 的通用 USB 相机。"""

    def __init__(self):
        self._cap: Optional[cv2.VideoCapture] = None
        self._device_index: int = 0

    @property
    def brand(self) -> str:
        return "uvc"

    def open(self, config: dict) -> bool:
        self._device_index = config.get("device_index", 0)
        self._cap = cv2.VideoCapture(self._device_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            self._cap = None
            raise RuntimeError(f"无法打开摄像头 index={self._device_index}")
        return True

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def grab(self) -> Optional[np.ndarray]:
        if not self.is_open():
            return None
        ret, frame = self._cap.read()
        return frame if ret else None

    def set_exposure(self, value_us: float) -> None:
        if self.is_open():
            self._cap.set(cv2.CAP_PROP_EXPOSURE, value_us / 10000.0)

    def set_gain(self, value_db: float) -> None:
        if self.is_open():
            self._cap.set(cv2.CAP_PROP_GAIN, value_db)

    def get_resolution(self) -> tuple[int, int]:
        if self.is_open():
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return w, h
        return 0, 0