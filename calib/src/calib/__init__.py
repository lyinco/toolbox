"""CalibTool — 桌面相机标定应用。"""

from pathlib import Path

__version__ = "0.1.0"


def package_root() -> Path:
    """Python 包根目录（含 config/、core/ 等）。"""
    return Path(__file__).resolve().parent


def project_root() -> Path:
    """项目根目录（含 pyproject.toml、output/、tests/）。"""
    return package_root().parent.parent


def default_output_dir() -> Path:
    """默认标定结果输出目录。"""
    return project_root() / "output"
