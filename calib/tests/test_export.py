"""导出模块单元测试。"""

import json
import unittest
import tempfile
from pathlib import Path

import numpy as np
import yaml

from calib.core.export.json_exporter import JsonExporter
from calib.core.export.yaml_exporter import YamlExporter


class TestExporters(unittest.TestCase):
    """验证 JSON/YAML 导出。"""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._data = {
            "camera_matrix": np.eye(3).tolist(),
            "dist_coeffs": np.zeros(5).tolist(),
            "image_size": [640, 480],
            "mean_reprojection_error": 0.15,
        }

    def test_json_export(self):
        exporter = JsonExporter(self._tmpdir)
        path = exporter.export(self._data, "test.json")
        self.assertTrue(path.exists())

        with open(path, "r") as f:
            loaded = json.load(f)
        self.assertAlmostEqual(loaded["mean_reprojection_error"], 0.15)

    def test_json_export_auto_suffix(self):
        exporter = JsonExporter(self._tmpdir)
        path = exporter.export(self._data, "no_suffix")
        self.assertTrue(path.name.endswith(".json"))

    def test_yaml_export(self):
        exporter = YamlExporter(self._tmpdir)
        path = exporter.export(self._data, "test.yaml")
        self.assertTrue(path.exists())

        with open(path, "r") as f:
            loaded = yaml.safe_load(f)
        self.assertAlmostEqual(loaded["mean_reprojection_error"], 0.15)

    def test_yaml_export_auto_suffix(self):
        exporter = YamlExporter(self._tmpdir)
        path = exporter.export(self._data, "no_suffix")
        self.assertTrue(path.name.endswith(".yaml"))

    def test_json_with_ndarray_in_data(self):
        exporter = JsonExporter(self._tmpdir)
        data = {"arr": np.array([1, 2, 3])}
        path = exporter.export(data, "arr.json")
        with open(path, "r") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["arr"], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()