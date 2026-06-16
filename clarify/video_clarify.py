"""
将图片变清晰 -- 放大2倍
"""

import sys, os
import cv2
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
import torch
import numpy as np
from PIL import Image

def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和 PyInstaller 打包后的 exe"""
    try:
        # PyInstaller 会将资源解压到临时目录，路径存储在 sys._MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境中，使用当前工作目录（项目根目录）
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def pillow2cv(image_pil):
    opencv_img = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    return opencv_img

def cv2pillow(image_cv):
    pil_img = Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))
    return pil_img


def scale_image_cv2(image, canv_width, canv_height):
    width, height = image.shape[:2]
    scale_x = canv_width / width
    scale_y = canv_height / height

    scale = min(scale_x, scale_y)
    tar_width = int(scale * width)
    tar_height = int(scale * height)
    tar_image = cv2.resize(image, (tar_width, tar_height))
    return tar_image, tar_width, tar_height

def scale_image_pil(image_pil, canv_width, canv_height):
    """
    PIL 图片进行缩放
    """
    width, height = image_pil.size
    scale_x = canv_width / width
    scale_y = canv_height / height

    scale = min(scale_x, scale_y)
    tar_width = int(scale * width)
    tar_height = int(scale * height)

    tar_image = image_pil.resize((tar_width, tar_height), Image.Resampling.LANCZOS)
    return tar_image, tar_width, tar_height


def affinite_image(image, p1, p2, p3, p4):
    """
    p1, p2, p3, p4 从左上顺时针开始
    """
    width = max(
        np.linalg.norm(np.array(p2) - np.array(p1)),
        np.linalg.norm(np.array(p3) - np.array(p4))
    )
    width = int(width)

    height = max(
        np.linalg.norm(np.array(p4) - np.array(p1)),
        np.linalg.norm(np.array(p3) - np.array(p2))
    )
    height = int(height)

    dst_pts = np.float32([
        [0, 0],
        [width, 0],
        [width, height],
        [0, height]
    ])

    src_pts = np.float32([p1, p2, p3, p4])
    # 计算透视矩阵
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    # 透视变换
    result = cv2.warpPerspective(image, M, (width, height))
    return result, width, height


def clahe_image(image):
    """
    CLAHE（提升局部对比度） 后 轻微去噪
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8)
    )
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    img_clahe = cv2.cvtColor(
        lab,
        cv2.COLOR_LAB2BGR
    )

    img_denoise = cv2.bilateralFilter(
        img_clahe,
        d=7,
        sigmaColor=50,
        sigmaSpace=50
    )
    return img_denoise


def unsharp_mask(image):
    blur = cv2.GaussianBlur(image, (0, 0), 5)
    highpass = cv2.subtract(image, blur)
    result = cv2.addWeighted(
        image,
        1.0,
        highpass,
        2.0,
        0
    )
    return result


def clarify_image_flow(image):
    # img_denoise = clahe_image(image)
    rsr_image = clarify_image(image)
    final = unsharp_mask(rsr_image)
    return final


def clarify_image(image, output_path=None, weights_path=resource_path('models/RealESRGAN_x4plus.pth')):
    """
    将图片清晰放大4倍
    """
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model = RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=23,
        num_grow_ch=32,
        scale=4
    )

    upsampler = RealESRGANer(
        scale=4,
        model_path=weights_path,
        model=model,
        tile=512,
        tile_pad=32,
        pre_pad=0,
         half=True,          # RTX4060支持FP16
        device=device
    )

    output, _ = upsampler.enhance(
        image,
        outscale=4
    )

    if output_path:
        cv2.imwrite(output_path, output)
    return output


if __name__ == "__main__":

    # input_image_path = 'F:/ftp/images/20260614110327.jpg'  # 替换为你的输入图片路径
    # output_image_path = 'F:/ftp/images/20260614110327-clarified.jpg'   # 替换为你想要保存的输出图片路径
    # image= cv2.imread(input_image_path)
    # clarify_image(image, output_image_path)

    # image_path = '树下诞生-A.JPG'
    # p1 = [241, 1529]
    # p2 = [3677, 1425]
    # p3 = [3877, 2257]
    # p4 = [0, 2225]
    # image = cv2.imread(image_path)
    # affinite_image(image, p1, p2, p3, p4)

    image_path = 'tt.png'
    image = cv2.imread(image_path)
    clarify_image(image, "upscale.png")


