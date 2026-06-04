"""重投影误差可视化图表。"""

import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout, QWidget


class ErrorChart(QWidget):
    """使用 pyqtgraph 绘制逐张重投影误差折线图。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setBackground("w")
        self._plot_widget.setLabel("left", "重投影误差 (px)")
        self._plot_widget.setLabel("bottom", "图片序号")
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot_widget)

        self._curve = None
        self._mean_line = None

    def set_data(self, errors: list[float]) -> None:
        """绘制误差折线图。

        Args:
            errors: 每张图片的重投影误差列表 (px)。
        """
        self._plot_widget.clear()
        if not errors:
            return

        x = list(range(1, len(errors) + 1))
        self._curve = self._plot_widget.plot(
            x, errors,
            pen=pg.mkPen(color="blue", width=2),
            symbol="o", symbolSize=8, symbolBrush="red",
        )

        # 平均线
        mean_val = sum(errors) / len(errors)
        self._mean_line = pg.InfiniteLine(
            pos=mean_val, angle=0,
            pen=pg.mkPen(color="green", width=2, style=pg.QtCore.Qt.DashLine),
            label=f"平均 {mean_val:.4f}",
        )
        self._plot_widget.addItem(self._mean_line)

        # 标注最大误差
        max_idx = errors.index(max(errors))
        max_pt = pg.TextItem(
            text=f"最大 {max(errors):.4f}",
            color="red", anchor=(0.5, 1.5),
        )
        max_pt.setPos(x[max_idx], errors[max_idx])
        self._plot_widget.addItem(max_pt)

    def clear(self) -> None:
        self._plot_widget.clear()