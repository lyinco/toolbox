"""标定板选择组件。"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
)

from calib.core.pattern.factory import PatternFactory


class PatternSelector(QGroupBox):
    """选择标定板类型和规格。"""

    pattern_changed = Signal()

    def __init__(self, parent=None):
        super().__init__("标定板", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)

        self._type_combo = QComboBox()
        for t in PatternFactory.registered_types():
            self._type_combo.addItem(t, t)
        layout.addRow("类型:", self._type_combo)

        self._rows_spin = QSpinBox()
        self._rows_spin.setRange(2, 50)
        self._rows_spin.setValue(8)
        layout.addRow("内角点行数:", self._rows_spin)

        self._cols_spin = QSpinBox()
        self._cols_spin.setRange(2, 50)
        self._cols_spin.setValue(11)
        layout.addRow("内角点列数:", self._cols_spin)

        self._square_size_spin = QDoubleSpinBox()
        self._square_size_spin.setRange(1.0, 500.0)
        self._square_size_spin.setValue(20.0)
        self._square_size_spin.setSuffix(" mm")
        layout.addRow("方格边长:", self._square_size_spin)

    def selected_type(self) -> str:
        return self._type_combo.currentData()

    def rows(self) -> int:
        return self._rows_spin.value()

    def cols(self) -> int:
        return self._cols_spin.value()

    def square_size(self) -> float:
        return self._square_size_spin.value()