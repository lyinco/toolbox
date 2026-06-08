"""全局应用配置，从 defaults.yaml 加载并暴露为 dataclass。"""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_DEFAULTS_PATH = Path(__file__).parent / "defaults.yaml"


@dataclass
class PatternConfig:
    pattern_type: str = "chessboard"
    rows: int = 8
    cols: int = 11
    square_size_mm: float = 20.0
    marker_length_mm: float = 15.0
    aruco_dictionary: str = "DICT_4X4_50"


@dataclass
class AcquisitionConfig:
    strategy: str = "simple"
    target_count: int = 20
    min_interval_ms: int = 500
    blur_threshold: float = 100.0
    coverage_min_samples: int = 15


@dataclass
class CalibrationConfig:
    fix_principal_point: bool = False
    fix_aspect_ratio: bool = True
    zero_tangent_dist: bool = False
    max_iter: int = 30
    eps: float = 1e-6


@dataclass
class UIConfig:
    window_title: str = "CalibTool"
    window_width: int = 1280
    window_height: int = 800
    preview_max_fps: int = 30


@dataclass
class ExportConfig:
    output_dir: str = ""
    default_format: str = "json"


@dataclass
class AppConfig:
    pattern: PatternConfig = field(default_factory=PatternConfig)
    acquisition: AcquisitionConfig = field(default_factory=AcquisitionConfig)
    calibration: CalibrationConfig = field(default_factory=CalibrationConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    export: ExportConfig = field(default_factory=ExportConfig)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "AppConfig":
        path = path or _DEFAULTS_PATH
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        return cls(
            pattern=PatternConfig(**raw.get("pattern", {})),
            acquisition=AcquisitionConfig(**raw.get("acquisition", {})),
            calibration=CalibrationConfig(**raw.get("calibration", {})),
            ui=UIConfig(**raw.get("ui", {})),
            export=ExportConfig(**raw.get("export", {})),
        )