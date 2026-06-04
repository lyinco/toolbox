"""CameraInterface 单元测试。"""

import unittest
import numpy as np
from calib.core.camera.interface import CameraInterface
from calib.core.camera.factory import CameraFactory


class TestCameraInterface(unittest.TestCase):
    """验证抽象接口和工厂注册。"""

    def test_factory_registered_brands(self):
        brands = CameraFactory.registered_brands()
        self.assertIn("basler", brands)
        self.assertIn("uvc", brands)

    def test_factory_create_basler(self):
        cam = CameraFactory.create("basler")
        self.assertEqual(cam.brand, "basler")
        self.assertFalse(cam.is_open())

    def test_factory_create_uvc(self):
        cam = CameraFactory.create("uvc")
        self.assertEqual(cam.brand, "uvc")
        self.assertFalse(cam.is_open())

    def test_factory_create_unknown_raises(self):
        with self.assertRaises(ValueError):
            CameraFactory.create("does_not_exist")

    def test_context_manager(self):
        cam = CameraFactory.create("uvc")
        self.assertFalse(cam.is_open())


if __name__ == "__main__":
    unittest.main()