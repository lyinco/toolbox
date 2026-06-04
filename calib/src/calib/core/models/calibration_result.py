"""标定结果与导出数据结构。"""

from typing import Any

from calib.core.calibration.mono import MonoCalibResult
from calib.core.pattern.base import CalibPatternBase


def build_export_payload(
    result: MonoCalibResult,
    pattern: CalibPatternBase,
) -> dict[str, Any]:
    """组装写入 JSON/YAML 的完整字典。"""
    data = result.to_dict()
    data["pattern"] = {
        "type": pattern.pattern_name,
        "rows": pattern.pattern_size()[1],
        "cols": pattern.pattern_size()[0],
        "square_size_mm": pattern.square_size_mm,
    }
    return data
