"""ChArUco 标定板检测。"""

import sys
# sys.path.insert(0, '/Users/lingcai/Documents/git_src/toolbox/calib/src')
from typing import Optional, Tuple

import cv2
import numpy as np

from .aruco_dictionaries import DEFAULT_ARUCO_DICTIONARY_NAME, dictionary_id_from_name
from .base import CalibPatternBase



class ChArUcoPattern(CalibPatternBase):
    """ChArUco 板：detect 返回 ChArUco 角点 (N,1,2) 与角点 ID (N,)。"""

    def __init__(
        self,
        rows: int,
        cols: int,
        square_size_mm: float,
        marker_length_mm: Optional[float] = None,
        dictionary_id: Optional[int] = None,
    ):
        if rows < 2 or cols < 2:
            raise ValueError(f"ChArUco 内角点行列至少为 2，当前 rows={rows}, cols={cols}")
        if square_size_mm <= 0:
            raise ValueError(f"square_size_mm 必须 > 0，当前为 {square_size_mm}")
        
        if marker_length_mm is None:
            raise ValueError(f"marker_length_mm 必须指定")

        self._rows = rows
        self._cols = cols
        self._square_size = float(square_size_mm)
        self._marker_length = float(marker_length_mm)

        did = dictionary_id
        if did is None:
            did = dictionary_id_from_name(DEFAULT_ARUCO_DICTIONARY_NAME)
        if not (0 < self._marker_length < self._square_size):
            raise ValueError(
                f"marker_length_mm 须满足 0 < marker < square_size，"
                f"当前 marker={self._marker_length}, square={self._square_size}"
            )

        self._dictionary = cv2.aruco.getPredefinedDictionary(did)
        self._detector_params = cv2.aruco.DetectorParameters()
        self._mkdetector = cv2.aruco.ArucoDetector(self._dictionary, self._detector_params)
        

        self._charuco_params = cv2.aruco.CharucoParameters()
        # size = 方格数 (squaresX, squaresY)；内角点数为 (cols, rows) 时方格数为 (cols+1, rows+1)
        self._board = cv2.aruco.CharucoBoard(
            size=(self._cols + 1, self._rows + 1),
            squareLength=self._square_size,
            markerLength=self._marker_length,
            dictionary=self._dictionary,
        ) 
        self._bddetector = cv2.aruco.CharucoDetector(
            self._board,
            # charucoParams=self._charuco_params,
            # detectorParams=self._detector_params,
        )

    @property
    def pattern_name(self) -> str:
        return "charuco"

    def pattern_size(self) -> Tuple[int, int]:
        """内角点数量 (cols, rows)。"""
        return (self._cols, self._rows)
    
    def detect(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """优先返回 ChArUco 角点，若无则返回 ArUco 角点。"""
        charuco_corners, charuco_ids = self.detect_charuco(image)
        if charuco_corners is not None and charuco_ids is not None:
            return charuco_corners, charuco_ids
        return None, None
        # return self.detect_marker(image)

    def detect_marker(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
            marker_corners, marker_ids, rejected = self._mkdetector.detectMarkers(image)
            print('marker : corners:', marker_corners)
            print('marker : ids:', marker_ids)
            if marker_ids is None or len(marker_ids) == 0:
                return None, None
            return marker_corners, marker_ids.flatten()
    

    def detect_charuco(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]] :

        charuco_corners, charuco_ids, marker_corners, marker_ids  = self._bddetector.detectBoard(image)
        print('marker : corners:', marker_corners)
        if charuco_corners is None or charuco_ids is None:
            return None, None
        return charuco_corners.astype(np.float32), charuco_ids.flatten()

    def object_points(self) -> np.ndarray:
        raise NotImplementedError("ChArUco object_points 将在后续扩展中实现")


    def draw_markers(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        img_draw = image.copy()
        if corners is not None and len(corners) > 0:
            cv2.aruco.drawDetectedMarkers(img_draw, corners)
        return img_draw

    def draw(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        img_draw = image.copy()
        if corners is not None and len(corners) > 0:
            cv2.aruco.drawDetectedMarkers(img_draw, corners)
            # cv2.aruco.drawDetectedCornersCharuco(img_draw, corners)
        return img_draw

    @property
    def square_size_mm(self) -> float:
        return self._square_size
    


if __name__ == "__main__" :
    
    # 简单测试
    dict = cv2.aruco.getPredefinedDictionary(0)
    print('dictionary 0 :', dict)

    pattern = ChArUcoPattern(rows=8, cols=11, square_size_mm=20, marker_length_mm=15, dictionary_id=0)
    print()
    img = cv2.imread('/Users/lingcai/Documents/git_src/toolbox/calib/data/charuco.jpg')
    print(f'image size : {img.shape}')
    corners, ids = pattern.detect(img)
    print("检测到的角点:", corners)
    print("检测到的角点 ID:", ids)
    img_draw = pattern.draw(img, corners)
    cv2.imshow("ChArUco Detection", img_draw)
    cv2.waitKey(0)
