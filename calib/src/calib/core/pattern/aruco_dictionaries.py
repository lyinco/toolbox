"""ArUco 字典：UI 显示名与 OpenCV 常量映射。"""

import cv2

# (界面显示名, cv2.aruco 常量)
ARUCO_DICTIONARY_CHOICES: list[tuple[str, int]] = [
    ("DICT_4X4_50", cv2.aruco.DICT_4X4_50),
    ("DICT_4X4_100", cv2.aruco.DICT_4X4_100),
    ("DICT_4X4_250", cv2.aruco.DICT_4X4_250),
    ("DICT_4X4_1000", cv2.aruco.DICT_4X4_1000),
    ("DICT_5X5_50", cv2.aruco.DICT_5X5_50),
    ("DICT_5X5_100", cv2.aruco.DICT_5X5_100),
    ("DICT_6X6_50", cv2.aruco.DICT_6X6_50),
    ("DICT_6X6_250", cv2.aruco.DICT_6X6_250),
    ("DICT_7X7_250", cv2.aruco.DICT_7X7_250),
]

DEFAULT_ARUCO_DICTIONARY_NAME = "DICT_4X4_50"


def dictionary_id_from_name(name: str) -> int:
    for label, did in ARUCO_DICTIONARY_CHOICES:
        if label == name:
            return did
    raise ValueError(f"未知 ArUco 字典: {name}")


def dictionary_name_from_id(dictionary_id: int) -> str:
    for label, did in ARUCO_DICTIONARY_CHOICES:
        if did == dictionary_id:
            return label
    return DEFAULT_ARUCO_DICTIONARY_NAME
