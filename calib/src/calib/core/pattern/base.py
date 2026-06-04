"""标定板抽象基类。"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

import numpy as np


class CalibPatternBase(ABC):
    """标定板检测与生成抽象。新增类型请继承并实现，例如 CalibPatternChessboard。"""

    @property
    @abstractmethod
    def pattern_name(self) -> str:
        """返回类型标识，如 'chessboard', 'charuco', 'circle_grid'。"""
        ...

    @abstractmethod
    def pattern_size(self) -> Tuple[int, int]:
        """返回 (cols, rows) —— 内角点数。"""
        ...

    @abstractmethod
    def detect(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """检测标定板。

        Returns:
            (corners, ids): corners 为 (N,1,2) 角点图像坐标，ids 为 (N,) 角点 ID。
            chessboard 等无 ID 的类型 ids 返回 None。
        """
        ...

    @abstractmethod
    def object_points(self) -> np.ndarray:
        """返回世界坐标系下的三维点 (N,3)，以标定板平面为 z=0。"""
        ...

    @abstractmethod
    def draw(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """在图像上绘制检测结果，返回带叠加的图像。"""
        ...

    @property
    @abstractmethod
    def square_size_mm(self) -> float:
        """方格/圆间距 (mm)。"""
        ...