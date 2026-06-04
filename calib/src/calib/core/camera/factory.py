"""相机工厂 —— 按品牌名创建相机实例。"""

from typing import Optional

from .interface import CameraInterface
from .basler_camera import BaslerCamera
from .uvc_camera import UVCCamera


_registry: dict[str, type] = {
    "basler": BaslerCamera,
    "uvc": UVCCamera,
}


def register_camera(brand: str, cls: type) -> None:
    """运行时注册新品牌相机类。"""
    _registry[brand.lower()] = cls


class CameraFactory:
    """根据品牌名创建相机实例。"""

    @staticmethod
    def create(brand: str) -> Optional[CameraInterface]:
        cls = _registry.get(brand.lower())
        if cls is None:
            raise ValueError(
                f"未知相机品牌 '{brand}'。已注册: {list(_registry.keys())}"
            )
        return cls()

    @staticmethod
    def registered_brands() -> list[str]:
        return list(_registry.keys())