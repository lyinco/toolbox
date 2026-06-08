"""ChArUco 标定板 detect 单元测试。"""

import unittest
from pathlib import Path

import cv2
import numpy as np

from calib.core.pattern.charuco import ChArUcoPattern
from calib.core.pattern.factory import PatternFactory

# 与 tests/data/charuo.jpg 中实物板一致（内角点 rows×cols，方格 mm，ArUco 字典）
_CHARUCO_ROWS = 8
_CHARUCO_COLS = 11
_SQUARE_SIZE_MM = 20
_MARKER_LENGTH_MM = 14.67
_CHARUCO_DICT = cv2.aruco.DICT_4X4_50
_MIN_DETECTED_CORNERS = 4


def _charuco_image_path() -> Path:
    data_dir = Path(__file__).resolve().parent / "data"
    for name in ("charuco.jpg", "charuo.jpg"):
        path = data_dir / name
        if path.is_file():
            return path
    return data_dir / "charuco.jpg"


class TestChArUcoPattern(unittest.TestCase):
    """验证 ChArUcoPattern.detect（使用 tests/data 下的实拍图）。"""

    @classmethod
    def setUpClass(cls):
        cls._rows = _CHARUCO_ROWS
        cls._cols = _CHARUCO_COLS
        cls._square_size = _SQUARE_SIZE_MM
        cls.pattern = PatternFactory.create(
            "charuco", cls._rows, cls._cols, cls._square_size,
            marker_length_mm=_MARKER_LENGTH_MM,
            dictionary_id=_CHARUCO_DICT,
        )

        image_path = _charuco_image_path()
        if not image_path.is_file():
            cls._sample_bgr = None
            cls._image_path = image_path
            return

        cls._image_path = image_path
        cls._sample_bgr = cv2.imread(str(image_path))
        if cls._sample_bgr is None:
            raise RuntimeError(f"无法读取测试图片: {image_path}")

    def setUp(self):
        if self._sample_bgr is None:
            self.skipTest(f"缺少测试图片: {self._image_path}")

    def test_pattern_name(self):
        self.assertEqual(self.pattern.pattern_name, "charuco")

    def test_pattern_size(self):
        self.assertEqual(self.pattern.pattern_size(), (self._cols, self._rows))

    def test_factory_creates_charuco(self):
        self.assertIsInstance(self.pattern, ChArUcoPattern)

    def test_detect_on_sample_image(self):
        corners, ids = self.pattern.detect(self._sample_bgr)
        print('corners:', corners)
        print('ids:', ids)

        self.assertIsNotNone(corners, "应在 charuco 实拍图上检测到角点")
        self.assertIsNotNone(ids, "应返回角点 ID")
        self.assertGreaterEqual(len(corners), _MIN_DETECTED_CORNERS)
        self.assertEqual(corners.ndim, 3)
        self.assertEqual(corners.shape[1:], (1, 2))
        self.assertEqual(len(ids), len(corners))
        self.assertTrue(np.all(ids >= 0))

    def test_draw_on_sample_image(self):
        print('testing draw on sample image...')
        corners, _ = self.pattern.detect(self._sample_bgr)
        print('corners:', corners)
        self.assertIsNotNone(corners)
        drawn = self.pattern.draw(self._sample_bgr, corners)
        self.assertEqual(drawn.shape, self._sample_bgr.shape)


if __name__ == "__main__":
    unittest.main()
