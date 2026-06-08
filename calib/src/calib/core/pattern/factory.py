"""标定板工厂 —— 按类型名创建标定板实例。"""

from typing import Optional

from .aruco_dictionaries import DEFAULT_ARUCO_DICTIONARY_NAME, dictionary_id_from_name
from .base import CalibPatternBase
from .chessboard import CalibPatternChessboard
from .charuco import ChArUcoPattern
from .circle_grid import CircleGridPattern


_registry: dict[str, type] = {
    "chessboard": CalibPatternChessboard,
    "circle_grid": CircleGridPattern,
    "charuco": ChArUcoPattern,
}


def register_pattern(pattern_type: str, cls: type) -> None:
    """运行时注册新标定板类型。"""
    _registry[pattern_type.lower()] = cls


class PatternFactory:
    """根据类型名创建标定板实例。"""

    @staticmethod
    def create(
        pattern_type: str,
        rows: int,
        cols: int,
        square_size_mm: float,
        marker_length_mm: Optional[float] = None,
        dictionary_id: int | None = None,
    ) -> CalibPatternBase:
        key = pattern_type.lower()
        cls = _registry.get(key)
        if cls is None:
            raise ValueError(
                f"未知标定板类型 '{pattern_type}'。已注册: {list(_registry.keys())}"
            )

        if key == "charuco":
            did = dictionary_id
            if did is None:
                did = dictionary_id_from_name(DEFAULT_ARUCO_DICTIONARY_NAME)

            if marker_length_mm is None:
                raise  ValueError( f"marker size 必须指定")

            return ChArUcoPattern(
                rows,
                cols,
                square_size_mm,
                marker_length_mm=marker_length_mm,
                dictionary_id=did,
            )
        return cls(rows, cols, square_size_mm)

    @staticmethod
    def registered_types() -> list[str]:
        return list(_registry.keys())
