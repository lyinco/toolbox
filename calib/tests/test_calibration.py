"""单目标定单元测试。"""

import unittest
import numpy as np
import cv2
from calib.core.calibration.mono import MonoCalibrator, MonoCalibResult
from calib.core.pattern.factory import PatternFactory


class TestMonoCalibrator(unittest.TestCase):
    """验证标定求解器。"""

    @classmethod
    def setUpClass(cls):
        cls._rows = 8
        cls._cols = 11
        cls._square_size = 20.0

        # 虚拟内参
        cls.size = (800, 600)
        fx, fy = 800.0, 800.0
        cx, cy = 400.0, 300.0
        cls.true_mtx = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float32)
        cls.true_dist = np.array([0.1, -0.2, 0.001, 0.002, 0.05], dtype=np.float32)

        cls.pattern = PatternFactory.create("chessboard", cls._rows, cls._cols, cls._square_size)
        objp = cls.pattern.object_points()

        # 生成合成棋盘格图像（渲染完整棋盘格 + 投影 + 畸变）
        np.random.seed(42)
        cls._images = []
        full_rows = cls._rows + 1
        full_cols = cls._cols + 1

        for i in range(15):
            # 随机外参
            rot_vec = (np.random.rand(3) - 0.5) * 0.5
            tvec = np.array([
                np.random.uniform(-80, 80),
                np.random.uniform(-80, 80),
                np.random.uniform(400, 700),
            ], dtype=np.float32)

            # 生成棋盘格图像：渲染每个方格角点，投影到图像平面
            img = np.ones((cls.size[1], cls.size[0]), dtype=np.uint8) * 128
            cell = 30  # 像素方格大小

            # 生成棋盘格世界坐标（所有方格角点，含外边框）
            grid_pts = []
            for r in range(full_rows):
                for c in range(full_cols):
                    grid_pts.append([c * cls._square_size, r * cls._square_size, 0.0])
            grid_pts = np.array(grid_pts, dtype=np.float32)

            # 投影
            imgpts, _ = cv2.projectPoints(grid_pts, rot_vec, tvec, cls.true_mtx, cls.true_dist)
            imgpts = imgpts.reshape(-1, 2).astype(np.int32)

            # 画棋盘格（填充黑白方格）
            for r in range(full_rows):
                for c in range(full_cols):
                    if (r + c) % 2 == 0:
                        idx_tl = r * full_cols + c
                        idx_tr = r * full_cols + c + 1
                        idx_bl = (r + 1) * full_cols + c
                        idx_br = (r + 1) * full_cols + c + 1
                        if idx_br < len(imgpts):
                            pts = np.array([
                                imgpts[idx_tl], imgpts[idx_tr],
                                imgpts[idx_br], imgpts[idx_bl]
                            ], dtype=np.int32)
                            cv2.fillPoly(img, [pts], 0)

            # 轻微模糊模拟真实图像
            img = cv2.GaussianBlur(img, (3, 3), 0.5)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            cls._images.append(img_bgr)

    def test_calibrate_basic(self):
        calib = MonoCalibrator()
        result = calib.calibrate(self._images, self.pattern)

        self.assertTrue(result.success, f"标定应成功: {result.message}")
        self.assertLess(result.mean_error, 2.0, "平均重投影误差应 < 2px")

        # 检查内参是否接近真值
        fx_err = abs(result.camera_matrix[0, 0] - self.true_mtx[0, 0]) / self.true_mtx[0, 0]
        fy_err = abs(result.camera_matrix[1, 1] - self.true_mtx[1, 1]) / self.true_mtx[1, 1]
        self.assertLess(fx_err, 0.10, "fx 误差应 < 10%")
        self.assertLess(fy_err, 0.10, "fy 误差应 < 10%")

    def test_calibrate_insufficient_images(self):
        calib = MonoCalibrator()
        result = calib.calibrate(self._images[:2], self.pattern)
        self.assertFalse(result.success)

    def test_result_to_dict(self):
        calib = MonoCalibrator()
        result = calib.calibrate(self._images, self.pattern)
        d = result.to_dict()
        self.assertIn("camera_matrix", d)
        self.assertIn("dist_coeffs", d)
        self.assertIn("mean_reprojection_error", d)
        self.assertIsInstance(d["camera_matrix"], list)
        self.assertEqual(len(d["camera_matrix"]), 3)
        self.assertEqual(len(d["camera_matrix"][0]), 3)


if __name__ == "__main__":
    unittest.main()