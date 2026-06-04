"""实时图像预览组件。"""

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class ImageViewer(QScrollArea):
    """支持缩放滚动的图像预览。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(320, 240)
        self._label.setStyleSheet("background-color: #1a1a1a;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

        self.setWidget(container)
        self.setWidgetResizable(True)

    def set_frame(self, frame: np.ndarray) -> None:
        """显示 BGR numpy 图像。

        Args:
            frame: BGR 格式的 numpy 数组 (H, W, 3)。
        """
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        rgb = frame[..., ::-1].copy()  # BGR → RGB
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        self._label.setPixmap(
            pix.scaled(
                self._label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def clear(self) -> None:
        self._label.clear()
        self._label.setText("无预览")