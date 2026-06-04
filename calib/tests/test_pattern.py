"""标定板检测单元测试。"""

import unittest
import numpy as np
import cv2
from calib.core.pattern.factory import PatternFactory


class TestCalibPatternChessboard(unittest.TestCase):
    """验证 CalibPatternChessboard 棋盘格检测。"""

    @classmethod
    def setUpClass(cls):
        cls._rows = 8
        cls._cols = 11
        cls._square_size = 20.0
        cls.pattern = PatternFactory.create("chessboard", cls._rows, cls._cols, cls._square_size)

        # 使用 OpenCV 内置函数生成标准棋盘格图像
        size = 800
        cls._synthetic = np.zeros((size, size), dtype=np.uint8)
        # 画完整棋盘格（含外边框），内部角点 = rows x cols
        full_rows = cls._rows + 1
        full_cols = cls._cols + 1
        cell = (size - 40) // max(full_rows, full_cols)
        offset_x = (size - full_cols * cell) // 2
        offset_y = (size - full_rows * cell) // 2
        for r in range(full_rows):
            for c in range(full_cols):
                if (r + c) % 2 == 0:
                    x1 = offset_x + c * cell
                    y1 = offset_y + r * cell
                    cv2.rectangle(cls._synthetic, (x1, y1), (x1 + cell, y1 + cell), 255, -1)
        # 轻微模糊 + 加噪声使角点可检测
        cls._synthetic = cv2.GaussianBlur(cls._synthetic, (5, 5), 1.0)
        noise = np.random.randint(0, 8, (size, size), dtype=np.uint8)
        cls._synthetic = cv2.add(cls._synthetic, noise)
        cls._synthetic_bgr = cv2.cvtColor(cls._synthetic, cv2.COLOR_GRAY2BGR)

    def test_pattern_name(self):
        self.assertEqual(self.pattern.pattern_name, "chessboard")

    def test_pattern_size(self):
        self.assertEqual(self.pattern.pattern_size(), (self._cols, self._rows))

    def test_object_points_shape(self):
        objp = self.pattern.object_points()
        self.assertEqual(objp.shape, (self._rows * self._cols, 3))
        self.assertAlmostEqual(objp[-1, 0], (self._cols - 1) * self._square_size, places=1)
        self.assertAlmostEqual(objp[-1, 1], (self._rows - 1) * self._square_size, places=1)

    def test_detect_on_synthetic(self):
        corners, ids = self.pattern.detect(self._synthetic_bgr)
        self.assertIsNotNone(corners, "应在合成棋盘格图像上检测到角点")
        self.assertEqual(corners.shape[0], self._rows * self._cols)

    def test_detect_on_blank(self):
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        corners, ids = self.pattern.detect(blank)
        self.assertIsNone(corners)

    def test_draw(self):
        corners, _ = self.pattern.detect(self._synthetic_bgr)
        drawn = self.pattern.draw(self._synthetic_bgr, corners)
        self.assertEqual(drawn.shape, self._synthetic_bgr.shape)


if __name__ == "__main__":
    unittest.main()