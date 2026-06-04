"""棋盘格标定板检测。"""

from typing import Optional, Tuple

import cv2
import numpy as np

from .base import CalibPatternBase


class CalibPatternChessboard(CalibPatternBase):
    """OpenCV 棋盘格标定板检测。"""

    def __init__(self, rows: int, cols: int, square_size_mm: float):
        self._rows = rows
        self._cols = cols
        self._square_size = square_size_mm

    @property
    def pattern_name(self) -> str:
        return "chessboard"

    def pattern_size(self) -> Tuple[int, int]:
        return (self._cols, self._rows)

    def detect(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(
            gray,
            (self._cols, self._rows),
            flags=cv2.CALIB_CB_ADAPTIVE_THRESH
            | cv2.CALIB_CB_NORMALIZE_IMAGE
            | cv2.CALIB_CB_FAST_CHECK,
        )
        if ret:
            # 亚像素优化
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_sub = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            return corners_sub.astype(np.float32), None
        return None, None

    def object_points(self) -> np.ndarray:
        objp = np.zeros((self._rows * self._cols, 3), dtype=np.float32)
        objp[:, :2] = np.mgrid[0 : self._cols, 0 : self._rows].T.reshape(-1, 2)
        objp *= self._square_size
        return objp

    def draw(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        img_draw = image.copy()
        cv2.drawChessboardCorners(img_draw, (self._cols, self._rows), corners, True)
        return img_draw

    @property
    def square_size_mm(self) -> float:
        return self._square_size