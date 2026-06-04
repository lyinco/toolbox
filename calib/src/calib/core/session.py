"""标定会话编排 —— 连接相机、采集、标定、导出的业务入口。"""

from pathlib import Path
from typing import Optional

import numpy as np

from calib import default_output_dir
from calib.config import AppConfig
from calib.core.acquisition.base import AcquisitionStrategy
from calib.core.acquisition.factory import create_acquisition_strategy
from calib.core.calibration.mono import MonoCalibResult, MonoCalibrator
from calib.core.camera.factory import CameraFactory
from calib.core.camera.interface import CameraInterface
from calib.core.export.json_exporter import JsonExporter
from calib.core.export.yaml_exporter import YamlExporter
from calib.core.models.calibration_result import build_export_payload
from calib.core.pattern.base import CalibPatternBase
from calib.core.pattern.factory import PatternFactory


class CalibrationSession:
    """一次标定工作流的状态与操作。"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.camera: Optional[CameraInterface] = None
        self.pattern: Optional[CalibPatternBase] = None
        self.acquired_images: list[np.ndarray] = []
        self.calib_result: Optional[MonoCalibResult] = None

    def connect_camera(self, brand: str, device_config: Optional[dict] = None) -> CameraInterface:
        device_config = device_config or {"device_index": 0}
        self.camera = CameraFactory.create(brand)
        if not self.camera.open(device_config):
            raise RuntimeError(f"无法打开相机: {brand}")
        return self.camera

    def disconnect_camera(self) -> None:
        if self.camera:
            self.camera.close()
            self.camera = None

    def create_pattern(
        self,
        pattern_type: str,
        rows: int,
        cols: int,
        square_size_mm: float,
    ) -> CalibPatternBase:
        self.pattern = PatternFactory.create(pattern_type, rows, cols, square_size_mm)
        return self.pattern

    def create_acquisition_strategy(self) -> AcquisitionStrategy:
        return create_acquisition_strategy(self.config.acquisition)

    def create_mono_calibrator(self) -> MonoCalibrator:
        c = self.config.calibration
        return MonoCalibrator(
            fix_principal_point=c.fix_principal_point,
            fix_aspect_ratio=c.fix_aspect_ratio,
            zero_tangent_dist=c.zero_tangent_dist,
            max_iter=c.max_iter,
            eps=c.eps,
        )

    def set_acquired_images(self, images: list[np.ndarray]) -> None:
        self.acquired_images = list(images)

    def set_calib_result(self, result: MonoCalibResult) -> None:
        self.calib_result = result

    def output_directory(self) -> Path:
        if self.config.export.output_dir:
            return Path(self.config.export.output_dir)
        return default_output_dir()

    def export_calibration(self, fmt: str) -> Path:
        if self.calib_result is None or not self.calib_result.success:
            raise ValueError("无有效的标定结果可导出")
        if self.pattern is None:
            raise ValueError("缺少标定板信息")

        data = build_export_payload(self.calib_result, self.pattern)
        outdir = str(self.output_directory())

        if fmt == "json":
            return Path(JsonExporter(outdir).export(data, "camera_intrinsics.json"))
        if fmt == "yaml":
            return Path(YamlExporter(outdir).export(data, "camera_intrinsics.yaml"))
        raise ValueError(f"不支持的导出格式: {fmt}")
