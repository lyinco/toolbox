"""JSON 导出器。"""

import json
from pathlib import Path
from typing import Any

import numpy as np


class JsonExporter:
    """将标定结果导出为 JSON 文件。"""

    def __init__(self, output_dir: str = ""):
        self._output_dir = Path(output_dir) if output_dir else Path.cwd() / "output"
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, data: dict, filename: str = "calibration.json") -> Path:
        """导出数据为 JSON。

        Args:
            data: 可序列化的字典。
            filename: 输出文件名（可带 .json 后缀）。

        Returns:
            输出文件的 Path。
        """
        if not filename.endswith(".json"):
            filename += ".json"

        out_path = self._output_dir / filename

        # 处理 numpy 数组
        def _serialize(obj: Any):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            raise TypeError(f"无法序列化 {type(obj)}")

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=_serialize)

        return out_path