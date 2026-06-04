"""标定板工厂 —— 按类型名创建标定板实例。"""

from typing import Optional

from .base import CalibPatternBase
from .chessboard import CalibPatternChessboard
from .charuco import ChArUcoPattern
from .circle_grid import CircleGridPattern


_registry: dict[str, type] = {
    "chessboard": CalibPatternChessboard,
    "charuco": ChArUcoPattern,
    "circle_grid": CircleGridPattern,
}


def register_pattern(pattern_type: str, cls: type) -> None:
    """运行时注册新标定板类型。"""
    _registry[pattern_type.lower()] = cls


class PatternFactory:
    """根据类型名创建标定板实例。"""

    @staticmethod
    def create(pattern_type: str, rows: int, cols: int, square_size_mm: float) -> Optional[CalibPatternBase]:
        cls = _registry.get(pattern_type.lower())
        if cls is None:
            raise ValueError(
                f"未知标定板类型 '{pattern_type}'。已注册: {list(_registry.keys())}"
            )
        return cls(rows, cols, square_size_mm)

    @staticmethod
    def registered_types() -> list[str]:
        return list(_registry.keys())