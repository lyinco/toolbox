#!/usr/bin/env python3
"""
模拟镜头推进（Zoom In）效果
输入一张图片，输出逐步放大的帧（视频或图片序列）
使用方法：
    python zoom_in.py --input image.jpg --output output.mp4 --zoom 2.0 --frames 30
"""

import cv2

def push_and_move(image, zoom = 2, frames = 250, fps = 30, out_mp4 = 'zoom_output.mp4'):
    """
    模拟镜头推进效果
    Args:
        image:输入图片路径
        zoom:最终放大倍数（相对于原始尺寸），默认2.0
        frames:总帧数
        fps:输出视频的帧率，默认30
        size:输出视频尺寸（宽x高），如1280x720，不指定则使用原始尺寸
        out_mp4: 输出视频文件路径（或图片序列文件夹）
    Returns:
    """

    h, w = image.shape[:2]
    # 确定输出尺寸
    out_w, out_h = w, h

    # 准备视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    if not out_mp4.endswith(('.mp4', '.avi')):
        out_mp4 += '.mp4'
    video_writer = cv2.VideoWriter(out_mp4, fourcc, fps, (out_w, out_h))

    # 生成帧
    for i in range(frames):
        # 计算当前缩放比例：从1.0线性变化到zoom
        t = i / (frames - 1) if frames > 1 else 1.0
        # scale = 1.0 + (zoom - 1.0) * t  # 线性缩放
        # 或者使用缓动函数（例如指数）让效果更平滑，可改用：
        scale = zoom ** t  # 指数缩放

        # 根据缩放比例计算裁剪区域（保持中心）
        # 裁剪尺寸 = 原始尺寸 / scale
        crop_w = int(w / scale)
        crop_h = int(h / scale)
        # 确保裁剪尺寸至少为1
        crop_w = max(1, crop_w)
        crop_h = max(1, crop_h)

        # 计算裁剪起点（中心对齐）
        start_x = (w - crop_w) // 2
        start_y = (h - crop_h) // 2

        # 裁剪
        cropped = image[start_y:start_y + crop_h, start_x:start_x + crop_w]

        # 缩放到目标尺寸
        frame = cv2.resize(cropped, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
        # 写入视频
        if video_writer:
            video_writer.write(frame)

        # 打印进度
        print(f"生成帧 {i + 1}/{frames}", end='\r')

    print("\n完成！")
    if video_writer:
        video_writer.release()
        print(f"视频已保存至: {out_mp4}")


if __name__ == "__main__":
    image_file = '树下诞生-A.JPG'
    image = cv2.imread(image_file)
    push_and_move(image)