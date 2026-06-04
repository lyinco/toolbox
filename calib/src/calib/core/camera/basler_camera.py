"""Basler Pylon 相机实现。"""

from typing import Optional

import numpy as np

from .interface import CameraInterface

try:
    from pypylon import pylon
    PYLON_AVAILABLE = True
except ImportError:
    PYLON_AVAILABLE = False
    raise Exception("ERROR: PYLON UNAVAILABLE")


class BaslerCamera(CameraInterface):
    """Basler USB3/GigE 相机，基于 pypylon。"""

    def __init__(self):
        self._camera: Optional[pylon.InstantCamera] = None
        self._converter: Optional[pylon.ImageFormatConverter] = None

    @property
    def brand(self) -> str:
        return "basler"

    def open(self, config: dict) -> bool:
        if not PYLON_AVAILABLE:
            raise RuntimeError("pypylon 未安装，请执行: pip install pypylon")

        try:
            tl_factory = pylon.TlFactory.GetInstance()
            devices = tl_factory.EnumerateDevices()
            if not devices:
                raise RuntimeError("未检测到 Basler 相机")

            # config 中可指定 serial_number / device_index
            serial = config.get("serial_number")
            index = config.get("device_index", 0)

            if serial:
                device = next((d for d in devices if d.GetSerialNumber() == serial), None)
                if device is None:
                    raise RuntimeError(f"未找到序列号={serial}的相机")
                self._camera = pylon.InstantCamera(tl_factory.CreateDevice(device))
            else:
                self._camera = pylon.InstantCamera(
                    tl_factory.CreateDevice(devices[min(index, len(devices) - 1)])
                )

            self._camera.Open()

            # 应用用户配置
            exposure = config.get("exposure_us")
            gain = config.get("gain_db")
            if exposure is not None:
                self.set_exposure(exposure)
            if gain is not None:
                self.set_gain(gain)

            # 格式转换器：一律转 BGR8
            self._converter = pylon.ImageFormatConverter()
            self._converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            self._converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

            return True

        except Exception as e:
            self.close()
            raise RuntimeError(f"Basler 相机打开失败: {e}")

    def close(self) -> None:
        if self._camera is not None:
            try:
                if self._camera.IsOpen():
                    self._camera.Close()
            except Exception:
                pass
            self._camera = None
        self._converter = None

    def is_open(self) -> bool:
        return self._camera is not None and self._camera.IsOpen()

    def grab(self) -> Optional[np.ndarray]:
        if not self.is_open():
            return None
        try:
            result = self._camera.GrabOne(2000)  # 2s 超时
            if result is None or not result.GrabSucceeded():
                return None
            converted = self._converter.Convert(result)
            arr = converted.Array
            return arr.copy()
        except Exception:
            return None

    def set_exposure(self, value_us: float) -> None:
        if self.is_open():
            self._camera.ExposureTime.SetValue(value_us)

    def set_gain(self, value_db: float) -> None:
        if self.is_open():
            self._camera.Gain.SetValue(value_db)

    def get_resolution(self) -> tuple[int, int]:
        if self.is_open():
            w = self._camera.Width.GetValue()
            h = self._camera.Height.GetValue()
            return int(w), int(h)
        return 0, 0

    def set_roi(self, x: int, y: int, w: int, h: int) -> None:
        if self.is_open():
            self._camera.OffsetX.SetValue(x)
            self._camera.OffsetY.SetValue(y)
            self._camera.Width.SetValue(w)
            self._camera.Height.SetValue(h)