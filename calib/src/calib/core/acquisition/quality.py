"""图像质量评估工具。"""

import cv2
import numpy as np


def blur_score(image: np.ndarray) -> float:
    """拉普拉斯方差模糊评分，越高越清晰。"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def is_overexposed(image: np.ndarray, threshold: float = 250, ratio: float = 0.05) -> bool:
    """检查是否过曝。"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return (gray > threshold).mean() > ratio


def is_underexposed(image: np.ndarray, threshold: float = 30, ratio: float = 0.2) -> bool:
    """检查是否欠曝。"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return (gray < threshold).mean() > ratio