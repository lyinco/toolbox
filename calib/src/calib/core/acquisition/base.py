"""采集策略抽象基类。"""

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class AcquisitionStrategy(ABC):
    """决定"当前帧是否应当采集"。新增策略只需继承此类。"""

    @abstractmethod
    def reset(self) -> None:
        """重置内部状态。"""
        ...

    @abstractmethod
    def should_acquire(self, image: np.ndarray, corners: Optional[np.ndarray]) -> bool:
        """判断当前帧是否应采集。

        Args:
            image: 原始 BGR 图像。
            corners: 已检测到的角点（None 表示未检测到标定板）。
        """
        ...

    @property
    @abstractmethod
    def acquired_count(self) -> int:
        """已采集帧数。"""
        ...

    @property
    @abstractmethod
    def is_done(self) -> bool:
        """是否已完成采集目标。"""
        ...