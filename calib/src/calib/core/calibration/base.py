"""标定求解器抽象基类。"""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from calib.core.pattern.base import CalibPatternBase


class CalibratorBase(ABC):
    """单目 / 双目 / 多机标定求解器的统一接口。"""

    @abstractmethod
    def calibrate(self, images: list[np.ndarray], pattern: CalibPatternBase) -> Any:
        ...
