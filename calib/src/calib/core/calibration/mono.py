"""单目相机标定求解器。"""

from typing import Optional

import cv2
import numpy as np
from dataclasses import dataclass, field

from calib.core.calibration.base import CalibratorBase
from calib.core.pattern.base import CalibPatternBase


@dataclass
class MonoCalibResult:
    """单目标定结果。"""

    camera_matrix: np.ndarray           # (3,3)
    dist_coeffs: np.ndarray             # (k1,k2,p1,p2[,k3...])
    rvecs: list[np.ndarray]             # 每张图的外参旋转向量
    tvecs: list[np.ndarray]             # 每张图的外参平移向量
    per_view_errors: list[float]        # 每张图的重投影误差 (px)
    mean_error: float                   # 整体平均重投影误差 (px)
    image_size: tuple[int, int]         # (width, height)
    num_images: int                     # 最终用于标定的图片数
    success: bool = True
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "camera_matrix": self.camera_matrix.tolist(),
            "dist_coeffs": self.dist_coeffs.tolist(),
            "image_size": list(self.image_size),
            "num_images": self.num_images,
            "mean_reprojection_error": self.mean_error,
            "per_view_errors": self.per_view_errors,
        }


class MonoCalibrator(CalibratorBase):
    """单目标定求解器，封装 cv2.calibrateCamera。"""

    def __init__(
        self,
        fix_principal_point: bool = False,
        fix_aspect_ratio: bool = True,
        zero_tangent_dist: bool = False,
        max_iter: int = 30,
        eps: float = 1e-6,
    ):
        self._flags = 0
        if fix_principal_point:
            self._flags |= cv2.CALIB_FIX_PRINCIPAL_POINT
        if fix_aspect_ratio:
            self._flags |= cv2.CALIB_FIX_ASPECT_RATIO
        if zero_tangent_dist:
            self._flags |= cv2.CALIB_ZERO_TANGENT_DIST
        self._criteria = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, max_iter, eps)

    def calibrate(
        self,
        images: list[np.ndarray],
        pattern: CalibPatternBase,
    ) -> MonoCalibResult:
        """执行标定（自动检测角点）。

        Args:
            images: 采集的 BGR 图像列表。
            pattern: 标定板对象。

        Returns:
            MonoCalibResult
        """
        h, w = images[0].shape[:2]
        objp = pattern.object_points()
        obj_points: list[np.ndarray] = []
        img_points: list[np.ndarray] = []

        for img in images:
            corners, _ = pattern.detect(img)
            if corners is not None:
                obj_points.append(objp.astype(np.float32))
                img_points.append(corners.astype(np.float32).reshape(-1, 2))

        return self._solve(obj_points, img_points, (w, h))

    def calibrate_from_points(
        self,
        obj_points: list[np.ndarray],
        img_points: list[np.ndarray],
        image_size: tuple[int, int],
    ) -> MonoCalibResult:
        """直接使用已检测的角点执行标定（跳过 detect 步骤，用于测试和手动选点场景）。

        Args:
            obj_points: 世界坐标点列表，每个 (N,3)。
            img_points: 图像坐标点列表，每个 (N,2)。
            image_size: (width, height)。

        Returns:
            MonoCalibResult
        """
        return self._solve(obj_points, img_points, image_size)

    def _solve(
        self,
        obj_points: list[np.ndarray],
        img_points: list[np.ndarray],
        image_size: tuple[int, int],
    ) -> MonoCalibResult:
        w, h = image_size

        if len(obj_points) < 3:
            return MonoCalibResult(
                success=False,
                message=f"有效图片不足: {len(obj_points)} 张 (至少 3 张)",
                camera_matrix=np.eye(3),
                dist_coeffs=np.zeros(5),
                rvecs=[], tvecs=[], per_view_errors=[],
                mean_error=float("inf"), image_size=(w, h),
                num_images=len(obj_points),
            )

        init_k = cv2.initCameraMatrix2D(obj_points, img_points, (w, h), 0.0)

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            obj_points, img_points, (w, h),
            init_k, None,
            flags=self._flags,
            criteria=self._criteria,
        )

        per_view = []
        for i in range(len(obj_points)):
            projected, _ = cv2.projectPoints(obj_points[i], rvecs[i], tvecs[i], mtx, dist)
            err = np.linalg.norm(img_points[i] - projected.reshape(-1, 2), axis=1).mean()
            per_view.append(round(float(err), 4))

        mean_err = float(np.mean(per_view)) if per_view else float("inf")

        return MonoCalibResult(
            camera_matrix=mtx,
            dist_coeffs=dist.flatten(),
            rvecs=rvecs,
            tvecs=tvecs,
            per_view_errors=per_view,
            mean_error=round(mean_err, 4),
            image_size=(w, h),
            num_images=len(obj_points),
            success=ret is not None,
            message=f"标定完成，平均重投影误差 {mean_err:.4f} px",
        )