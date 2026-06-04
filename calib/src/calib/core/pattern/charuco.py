"""ChArUco 标定板（stub，供后续扩展）。"""

from typing import Optional, Tuple

import numpy as np

from .base import CalibPatternBase


class ChArUcoPattern(CalibPatternBase):
    def __init__(self, rows: int, cols: int, square_size_mm: float):
        self._rows = rows
        self._cols = cols
        self._square_size = square_size_mm

    @property
    def pattern_name(self) -> str:
        return "charuco"

    def pattern_size(self) -> Tuple[int, int]:
        return (self._cols, self._rows)

    def detect(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        raise NotImplementedError("ChArUco 将在后续扩展中实现")

    def object_points(self) -> np.ndarray:
        raise NotImplementedError("ChArUco 将在后续扩展中实现")

    def draw(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        raise NotImplementedError("ChArUco 将在后续扩展中实现")

    @property
    def square_size_mm(self) -> float:
        return self._square_size