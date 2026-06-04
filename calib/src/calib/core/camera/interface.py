"""相机抽象接口 —— 所有品牌相机必须实现此基类。"""

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class CameraInterface(ABC):
    """相机统一抽象。新增品牌只需继承并实现全部抽象方法。"""

    @property
    @abstractmethod
    def brand(self) -> str:
        """返回品牌标识字符串，如 'basler', 'hikvision', 'uvc'。"""
        ...

    @abstractmethod
    def open(self, config: dict) -> bool:
        """打开相机并应用配置。返回 True 表示成功。"""
        ...

    @abstractmethod
    def close(self) -> None:
        """关闭相机并释放资源。"""
        ...

    @abstractmethod
    def is_open(self) -> bool:
        """返回相机是否已打开。"""
        ...

    @abstractmethod
    def grab(self) -> Optional[np.ndarray]:
        """抓取一帧，返回 BGR numpy 数组；失败返回 None。"""
        ...

    @abstractmethod
    def set_exposure(self, value_us: float) -> None:
        """设置曝光时间 (微秒)。"""
        ...

    @abstractmethod
    def set_gain(self, value_db: float) -> None:
        """设置增益 (dB)。"""
        ...

    @abstractmethod
    def get_resolution(self) -> tuple[int, int]:
        """返回当前分辨率 (width, height)。"""
        ...

    def set_roi(self, x: int, y: int, w: int, h: int) -> None:
        """设置 ROI（默认实现为空，子类按需覆写）。"""
        pass

    def get_intrinsics_guess(self) -> Optional[dict]:
        """返回厂商提供的近似内参（如相机矩阵、畸变系数），无则返回 None。"""
        return None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()