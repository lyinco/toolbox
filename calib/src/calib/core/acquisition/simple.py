"""简易自动采集策略：检测到标定板 + 间隔足够 → 采集。"""

import time
from typing import Optional

import cv2
import numpy as np

from .base import AcquisitionStrategy


class SimpleAcquisition(AcquisitionStrategy):
    """基于时间间隔 + 姿态变化检测的采集策略。"""

    def __init__(
        self,
        target_count: int = 20,
        min_interval_ms: int = 500,
        blur_threshold: float = 100.0,
    ):
        self._target = target_count
        self._interval = min_interval_ms / 1000.0
        self._blur_threshold = blur_threshold
        self._last_time: float = 0.0
        self._count: int = 0
        self._last_corners: Optional[np.ndarray] = None

    def reset(self) -> None:
        self._last_time = 0.0
        self._count = 0
        self._last_corners = None

    def should_acquire(self, image: np.ndarray, corners: Optional[np.ndarray]) -> bool:
        if self._count >= self._target:
            return False

        # 必须检测到标定板
        if corners is None:
            return False

        # 模糊检测
        if not self._is_sharp(image):
            return False

        # 时间间隔
        now = time.time()
        if now - self._last_time < self._interval:
            return False

        # 姿态变化检测：角点位置要有足够差异
        if self._last_corners is not None:
            diff = np.linalg.norm(
                corners.reshape(-1, 2) - self._last_corners.reshape(-1, 2), axis=1
            ).mean()
            if diff < 5.0:
                return False

        self._last_time = now
        self._last_corners = corners.copy()
        self._count += 1
        return True

    @property
    def acquired_count(self) -> int:
        return self._count

    @property
    def target_count(self) -> int:
        return self._target

    @property
    def is_done(self) -> bool:
        return self._count >= self._target

    def _is_sharp(self, image: np.ndarray) -> bool:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return lap_var >= self._blur_threshold