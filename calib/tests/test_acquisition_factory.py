"""采集策略工厂单元测试。"""

import unittest

from calib.config import AcquisitionConfig
from calib.core.acquisition.factory import create_acquisition_strategy
from calib.core.acquisition.simple import SimpleAcquisition


class TestAcquisitionFactory(unittest.TestCase):
    def test_create_simple(self):
        cfg = AcquisitionConfig(strategy="simple", target_count=10)
        strategy = create_acquisition_strategy(cfg)
        self.assertIsInstance(strategy, SimpleAcquisition)
        self.assertEqual(strategy.target_count, 10)


if __name__ == "__main__":
    unittest.main()
