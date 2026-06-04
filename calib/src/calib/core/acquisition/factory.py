"""采集策略工厂。"""

from calib.config import AcquisitionConfig
from calib.core.acquisition.base import AcquisitionStrategy
from calib.core.acquisition.coverage import CoverageAcquisition
from calib.core.acquisition.simple import SimpleAcquisition


def create_acquisition_strategy(cfg: AcquisitionConfig) -> AcquisitionStrategy:
    """根据配置创建采集策略实例。"""
    name = cfg.strategy.lower()
    if name == "simple":
        return SimpleAcquisition(
            target_count=cfg.target_count,
            min_interval_ms=cfg.min_interval_ms,
            blur_threshold=cfg.blur_threshold,
        )
    if name == "coverage":
        return CoverageAcquisition(
            target_count=cfg.target_count,
            coverage_min_samples=cfg.coverage_min_samples,
        )
    raise ValueError(
        f"未知采集策略 '{cfg.strategy}'。可选: simple, coverage"
    )
