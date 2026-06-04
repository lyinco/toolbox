"""覆盖度导向的采集策略（stub，供后续扩展）。"""

from typing import Optional

import numpy as np

from .base import AcquisitionStrategy


class CoverageAcquisition(AcquisitionStrategy):
    """基于图像覆盖度的智能采集策略 —— 后续扩展。"""

    def __init__(self, target_count: int = 20, coverage_min_samples: int = 15):
        self._target = target_count
        self._min_samples = coverage_min_samples
        self._count: int = 0

    def reset(self) -> None:
        self._count = 0

    def should_acquire(self, image: np.ndarray, corners: Optional[np.ndarray]) -> bool:
        raise NotImplementedError("CoverageAcquisition 将在后续扩展中实现")

    @property
    def acquired_count(self) -> int:
        return self._count

    @property
    def is_done(self) -> bool:
        return self._count >= self._target