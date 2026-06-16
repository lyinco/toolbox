"""
将图片变清晰 -- 放大2倍
"""

import cv2
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
import torch
import numpy as np
from PIL import Image


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


def clarify_image(image, output_path=None, weights_path='models/RealESRGAN_x4plus.pth'):
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


def split_and_clarify_image(image_path, output_images_path, weights_path='F:/AI_MODELS/realesr/RealESRGAN_x4plus.pth'):
    
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    video_w = 1920
    video_h = 1080

    fps = 30
    duration = 30

    frames = fps * duration

    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # writer = cv2.VideoWriter(
    #     "scan.mp4",
    #     fourcc,
    #     fps,
    #     (video_w, video_h)
    # )

    for i in range(frames):

        # t = i / (frames - 1)
        # t = i/(frames-1)
        # t = 0.5 - 0.5*np.cos(np.pi*t)
        t= i/(frames-1)

        scale = 1.0 + 0.5*t

        crop_w = int(video_w / scale)
        crop_h = int(video_h / scale)
        x = int(
            t*(w-crop_w)
        )
        y = (h-crop_h)//2
        crop = img[
            y:y+crop_h,
            x:x+crop_w
        ]
        frame = cv2.resize(
            crop,
            (video_w,video_h)
        )

        print(f'x={x} y={y} t={t:.4f}')

        # crop = img[
        #     0:video_h,
        #     x:x+video_w
        # ]

        cv2.imshow("frame", frame)
        cv2.waitKey(500)

        # writer.write(crop)

    # writer.release()

    print("视频处理完成")


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


