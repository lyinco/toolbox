"""标定控制与结果显示面板。"""

import numpy as np
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QTextEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from calib.core.calibration.mono import MonoCalibrator, MonoCalibResult
from calib.core.pattern.base import CalibPatternBase
from calib.worker.calibration_worker import CalibrationWorker
from .widgets.error_chart import ErrorChart


class CalibrationPanel(QGroupBox):
    """标定操作与结果展示。"""

    calibrate_requested = Signal()
    export_requested = Signal()
    calibration_finished = Signal(MonoCalibResult)

    def __init__(self, parent=None):
        super().__init__("标定", parent)
        self.calib_result: MonoCalibResult | None = None
        self._worker: CalibrationWorker | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 标定按钮
        btn_row = QHBoxLayout()
        self._calibrate_btn = QPushButton("开始标定")
        self._calibrate_btn.setEnabled(False)
        self._calibrate_btn.clicked.connect(self.calibrate_requested.emit)
        btn_row.addWidget(self._calibrate_btn)
        layout.addLayout(btn_row)

        # 进度
        self._calib_progress = QProgressBar()
        self._calib_progress.setVisible(False)
        layout.addWidget(self._calib_progress)

        # 结果概要
        self._result_label = QLabel("-")
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        # 重投影误差图
        self._error_chart = ErrorChart()
        layout.addWidget(self._error_chart)

        # 逐张误差表
        self._error_table = QTableWidget()
        self._error_table.setColumnCount(2)
        self._error_table.setHorizontalHeaderLabels(["图片序号", "重投影误差 (px)"])
        self._error_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._error_table.setVisible(False)
        self._error_table.setMaximumHeight(150)
        layout.addWidget(self._error_table)

        # 导出
        export_row = QHBoxLayout()
        self._format_combo = QComboBox()
        self._format_combo.addItems(["json", "yaml"])
        export_row.addWidget(QLabel("格式:"))
        export_row.addWidget(self._format_combo)
        self._export_btn = QPushButton("导出")
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self.export_requested.emit)
        export_row.addWidget(self._export_btn)
        layout.addLayout(export_row)

    def on_acquisition_started(self) -> None:
        self._calibrate_btn.setEnabled(False)
        self._result_label.setText("采集中...")

    def on_acquisition_finished(self, count: int) -> None:
        self._calibrate_btn.setEnabled(count >= 3)
        self._result_label.setText(f"已采集 {count} 张，可开始标定")

    def start_calibration(
        self,
        images: list[np.ndarray],
        pattern: CalibPatternBase,
        calibrator: MonoCalibrator,
    ) -> None:
        self._calibrate_btn.setEnabled(False)
        self._export_btn.setEnabled(False)
        self._calib_progress.setVisible(True)
        self._calib_progress.setMaximum(len(images))
        self._calib_progress.setValue(0)
        self._error_table.setVisible(False)
        self._error_chart.clear()

        self._worker = CalibrationWorker(images, pattern, calibrator)
        self._worker.progress_updated.connect(self._on_calib_progress)
        self._worker.finished_signal.connect(self._on_calib_finished)
        self._worker.error_occurred.connect(self._on_calib_error)
        self._worker.start()

    def _on_calib_progress(self, current: int, total: int) -> None:
        self._calib_progress.setValue(current)

    def _on_calib_finished(self, result: MonoCalibResult) -> None:
        self._calib_progress.setVisible(False)
        self._calibrate_btn.setEnabled(True)
        self.calib_result = result

        if result.success:
            self._result_label.setText(
                f"标定完成\n"
                f"图片数: {result.num_images} | "
                f"分辨率: {result.image_size[0]}×{result.image_size[1]}\n"
                f"平均重投影误差: {result.mean_error:.4f} px\n"
                f"内参矩阵:\n{np.array2string(result.camera_matrix, precision=3, suppress_small=True)}\n"
                f"畸变系数: {np.array2string(result.dist_coeffs, precision=5, suppress_small=True)}"
            )
            self._export_btn.setEnabled(True)

            # 误差图
            self._error_chart.set_data(result.per_view_errors)

            # 逐张误差表
            self._error_table.setRowCount(len(result.per_view_errors))
            for i, err in enumerate(result.per_view_errors):
                self._error_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                item = QTableWidgetItem(f"{err:.4f}")
                if err > result.mean_error * 2:
                    item.setForeground(Qt.GlobalColor.red)
                self._error_table.setItem(i, 1, item)
            self._error_table.setVisible(True)
        else:
            self._result_label.setText(f"标定失败: {result.message}")
            self._error_chart.clear()
            self._error_table.setVisible(False)

        self.calibration_finished.emit(result)

    def _on_calib_error(self, message: str) -> None:
        self._calib_progress.setVisible(False)
        self._calibrate_btn.setEnabled(True)
        self._result_label.setText(f"错误: {message}")

    def export_format(self) -> str:
        return self._format_combo.currentText()

    def set_default_export_format(self, fmt: str) -> None:
        idx = self._format_combo.findText(fmt)
        if idx >= 0:
            self._format_combo.setCurrentIndex(idx)