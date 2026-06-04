"""标定计算工作线程。"""

import numpy as np
from PySide6.QtCore import QThread, Signal

from calib.core.calibration.mono import MonoCalibrator, MonoCalibResult
from calib.core.pattern.base import CalibPatternBase


class CalibrationWorker(QThread):
    """在后台执行标定计算，避免冻结 UI。"""

    started_signal = Signal()
    progress_updated = Signal(int, int)       # 当前/总计
    finished_signal = Signal(MonoCalibResult)
    error_occurred = Signal(str)

    def __init__(
        self,
        images: list[np.ndarray],
        pattern: CalibPatternBase,
        calibrator: MonoCalibrator,
        parent=None,
    ):
        super().__init__(parent)
        self._images = images
        self._pattern = pattern
        self._calibrator = calibrator

    def run(self) -> None:
        self.started_signal.emit()
        try:
            total = len(self._images)

            # 预检测角点（可选：Calibrator 内部也会检测，这里分开是为了进度反馈）
            valid_images = []
            for i, img in enumerate(self._images):
                corners, _ = self._pattern.detect(img)
                if corners is not None:
                    valid_images.append(img)
                self.progress_updated.emit(i + 1, total)

            if len(valid_images) < 3:
                self.finished_signal.emit(
                    MonoCalibResult(
                        success=False,
                        message=f"有效图片不足: {len(valid_images)} 张 (至少 3 张)",
                        camera_matrix=np.eye(3),
                        dist_coeffs=np.zeros(5),
                        rvecs=[], tvecs=[], per_view_errors=[],
                        mean_error=float("inf"), image_size=(0, 0),
                        num_images=len(valid_images),
                    )
                )
                return

            # 标定
            result = self._calibrator.calibrate(valid_images, self._pattern)
            self.finished_signal.emit(result)

        except Exception as e:
            self.error_occurred.emit(f"标定失败: {e}")