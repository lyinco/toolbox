"""标定板选择组件。"""

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QWidget,
)

from calib.config import PatternConfig
from calib.core.pattern.aruco_dictionaries import (
    ARUCO_DICTIONARY_CHOICES,
    DEFAULT_ARUCO_DICTIONARY_NAME,
    dictionary_id_from_name,
)
from calib.core.pattern.factory import PatternFactory


class PatternSelector(QGroupBox):
    """选择标定板类型和规格。"""

    pattern_changed = Signal()

    def __init__(self, pattern_config: Optional[PatternConfig] = None, parent=None):
        super().__init__("标定板", parent)
        self._pattern_config = pattern_config
        self._setup_ui()
        self._apply_config_defaults()
        self._on_type_changed()
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)

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

        # ChArUco 专用
        self._marker_size_spin = QDoubleSpinBox()
        self._marker_size_spin.setRange(0.1, 500.0)
        self._marker_size_spin.setValue(15.0)
        self._marker_size_spin.setSuffix(" mm")
        self._marker_size_row = QWidget()
        marker_row_layout = QFormLayout(self._marker_size_row)
        marker_row_layout.setContentsMargins(0, 0, 0, 0)
        marker_row_layout.addRow("Marker 边长:", self._marker_size_spin)

        self._dict_combo = QComboBox()
        for label, _ in ARUCO_DICTIONARY_CHOICES:
            self._dict_combo.addItem(label, label)
        default_idx = self._dict_combo.findData(DEFAULT_ARUCO_DICTIONARY_NAME)
        if default_idx >= 0:
            self._dict_combo.setCurrentIndex(default_idx)
        self._dict_row = QWidget()
        dict_row_layout = QFormLayout(self._dict_row)
        dict_row_layout.setContentsMargins(0, 0, 0, 0)
        dict_row_layout.addRow("Dictionary:", self._dict_combo)

        layout.addRow(self._marker_size_row)
        layout.addRow(self._dict_row)

        self._square_size_spin.valueChanged.connect(self._on_square_size_changed)
        self._on_square_size_changed(self._square_size_spin.value())

    def _apply_config_defaults(self) -> None:
        if self._pattern_config is None:
            return
        cfg = self._pattern_config
        idx = self._type_combo.findData(cfg.pattern_type)
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)
        self._rows_spin.setValue(cfg.rows)
        self._cols_spin.setValue(cfg.cols)
        self._square_size_spin.setValue(cfg.square_size_mm)
        if getattr(cfg, "marker_length_mm", None) is not None:
            self._marker_size_spin.setValue(cfg.marker_length_mm)
        dict_name = getattr(cfg, "aruco_dictionary", DEFAULT_ARUCO_DICTIONARY_NAME)
        didx = self._dict_combo.findData(dict_name)
        if didx >= 0:
            self._dict_combo.setCurrentIndex(didx)

    def _on_type_changed(self) -> None:
        is_charuco = self.selected_type() == "charuco"
        self._marker_size_row.setVisible(is_charuco)
        self._dict_row.setVisible(is_charuco)
        self.pattern_changed.emit()

    def _on_square_size_changed(self, square_mm: float) -> None:
        max_marker = max(0.1, square_mm - 0.01)
        self._marker_size_spin.setMaximum(max_marker)
        if self._marker_size_spin.value() >= square_mm:
            self._marker_size_spin.setValue(min(15.0, max_marker))

    def selected_type(self) -> str:
        return self._type_combo.currentData()

    def rows(self) -> int:
        return self._rows_spin.value()

    def cols(self) -> int:
        return self._cols_spin.value()

    def square_size(self) -> float:
        return self._square_size_spin.value()

    def marker_length_mm(self) -> float:
        return self._marker_size_spin.value()

    def aruco_dictionary_id(self) -> int:
        name = self._dict_combo.currentData()
        return dictionary_id_from_name(name)

    def aruco_dictionary_name(self) -> str:
        return self._dict_combo.currentData()
