"""应用启动逻辑。"""

import sys

from PySide6.QtWidgets import QApplication

from calib import default_output_dir, package_root
from calib.config import AppConfig
from calib.ui import MainWindow


def main() -> None:
    config_path = package_root() / "config" / "defaults.yaml"
    config = AppConfig.load(config_path)

    out_dir = default_output_dir()
    if config.export.output_dir:
        out_dir = __import__("pathlib").Path(config.export.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    window = MainWindow(config)
    window.show()
    sys.exit(app.exec())
