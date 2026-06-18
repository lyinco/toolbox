import cv2
import numpy as np
import argparse
import sys, os, shutil

def video_left2right(image, ratio=0.25, fps=30, zoom_duration=5, scan_duration=30,
                     codec = 'mp4v', output_video = 'output.mp4', frame_dir = None,
                     on_frame_callback=None):
    """
    模拟镜头推进到左侧并横向扫描图片，生成MP4视频
    Args:
        image:
        ratio: 扫描窗口宽度占图片宽度的比例（0~1），默认0.25
        fps: 频帧率，默认30
        zoom_duration: 推进阶段时长（秒），默认2
        scan_duration: 扫描阶段时长（秒），默认8
        codec: '视频编码器，默认mp4v' choices=['mp4v', 'avc1', 'x264'
        output_video: '输出mp4文件路径',
        frame_dir: '生成的每帧图片路径'

    Returns:
    """

    H, W = image.shape[:2]
    # 窗口尺寸：高度保持原图高度，宽度按比例缩小
    win_w = max(1, int(W * ratio))
    win_h = H
    # 如果窗口宽度大于原图宽度，则设为原图宽度（无扫描效果）
    if win_w >= W:
        print("警告：窗口宽度不小于原图宽度，将不进行缩放和扫描")
        win_w = W

    # 视频输出尺寸
    video_size = (win_w, win_h)
    print(f"视频尺寸: {video_size}，帧率: {fps}")

    # 准备视频写入器
    fourcc_map = {
        'mp4v': cv2.VideoWriter_fourcc(*'mp4v'),
        'avc1': cv2.VideoWriter_fourcc(*'avc1'),
        'x264': cv2.VideoWriter_fourcc(*'X264')
    }
    fourcc = fourcc_map.get(codec, cv2.VideoWriter_fourcc(*'mp4v'))
    out = cv2.VideoWriter(output_video, fourcc, fps, video_size)
    # 输出文件路径
    if frame_dir is None:
        frame_dir = os.path.dirname(os.path.abspath(__file__))
        frame_dir = os.path.join(frame_dir, 'tmp')
    if os.path.exists(frame_dir):
        shutil.rmtree(frame_dir)
    os.makedirs(frame_dir, exist_ok=True)

    if not out.isOpened():
        print("错误：无法创建视频文件，请检查编码器或路径权限")
        sys.exit(1)

    # ---- 阶段1：推进（从全图缩小到左窗口） ----
    zoom_frames = int(fps * zoom_duration)
    if zoom_frames < 1:
        zoom_frames = 1

    frame_idx = 0
    total_frames = zoom_frames + int(fps * scan_duration)
    for i in range(zoom_frames):
        t = i / (zoom_frames - 1) if zoom_frames > 1 else 1.0
        # 当前截取宽度：从 W 线性减小到 win_w
        cur_w = int(W - t * (W - win_w))
        # 截取区域：高度全取，宽度从左边开始
        roi = image[0:H, 0:cur_w]
        # 缩放到视频尺寸（推进时会有缩放，产生镜头推进效果）
        frame = cv2.resize(roi, video_size, interpolation=cv2.INTER_LANCZOS4)
        out.write(frame)
        print(f'add frame: frame_idx = {frame_idx}')
        if frame_dir is not None:
            frame_path = os.path.join(frame_dir, f'{frame_idx}.png')
            cv2.imwrite(frame_path, frame)
            # 调用回调（传入路径、索引、总数）
            if on_frame_callback:
                on_frame_callback(frame_path, frame_idx, total_frames)
            frame_idx+=1

    # ---- 阶段2：横向扫描（窗口尺寸固定，从左到右） ----
    scan_frames = int(fps * scan_duration)
    if scan_frames < 1:
        scan_frames = 1

    max_x = W - win_w
    for i in range(scan_frames):
        t = i / (scan_frames - 1) if scan_frames > 1 else 1.0
        x = int(t * max_x)
        frame = image[0:H, x:x + win_w]  # shape = (H, win_w, 3)
        # 确保帧尺寸与视频尺寸一致
        if frame.shape[1] != win_w or frame.shape[0] != H:
            raise ValueError(f"帧尺寸 {frame.shape} 错误，期望 ({H}, {win_w})")
        frame = np.ascontiguousarray(frame)
        out.write(frame)
        print(f'add frame: frame_idx = {frame_idx}')
        if frame_dir is not None:
            frame_path = os.path.join(frame_dir, f'{frame_idx}.png')
            cv2.imwrite(frame_path, frame)
            if on_frame_callback:
                on_frame_callback(frame_path, frame_idx, total_frames)
            frame_idx+=1

    out.release()
    print(f"视频已生成: {output_video}")



def main():
    parser = argparse.ArgumentParser(description='模拟镜头推进到左侧并横向扫描图片，生成MP4视频')
    parser.add_argument('--image_path', default= '11.png', help='输入图片路径')
    parser.add_argument('--output_video', default='zoom_output.mp4', help='输出MP4视频路径（如 output.mp4）')
    parser.add_argument('--ratio', type=float, default=0.25, help='扫描窗口宽度占图片宽度的比例（0~1），默认0.25')
    parser.add_argument('--fps', type=int, default=30, help='视频帧率，默认30')
    parser.add_argument('--zoom_duration', type=float, default=2.0, help='推进阶段时长（秒），默认2')
    parser.add_argument('--scan_duration', type=float, default=8.0, help='扫描阶段时长（秒），默认8')
    parser.add_argument('--codec', default='mp4v', choices=['mp4v', 'avc1', 'x264'], help='视频编码器，默认mp4v')
    args = parser.parse_args()

    # 读取图片
    img = cv2.imread(args.image_path)
    if img is None:
        print(f"错误：无法读取图片 {args.image_path}")
        sys.exit(1)

    H, W = img.shape[:2]
    # 窗口尺寸：高度保持原图高度，宽度按比例缩小
    win_w = max(1, int(W * args.ratio))
    win_h = H
    # 如果窗口宽度大于原图宽度，则设为原图宽度（无扫描效果）
    if win_w >= W:
        print("警告：窗口宽度不小于原图宽度，将不进行缩放和扫描")
        win_w = W

    # 视频输出尺寸
    video_size = (win_w, win_h)
    print(f"视频尺寸: {video_size}，帧率: {args.fps}")

    # 准备视频写入器
    fourcc_map = {
        'mp4v': cv2.VideoWriter_fourcc(*'mp4v'),
        'avc1': cv2.VideoWriter_fourcc(*'avc1'),
        'x264': cv2.VideoWriter_fourcc(*'X264')
    }
    fourcc = fourcc_map.get(args.codec, cv2.VideoWriter_fourcc(*'mp4v'))
    out = cv2.VideoWriter(args.output_video, fourcc, args.fps, video_size)

    if not out.isOpened():
        print("错误：无法创建视频文件，请检查编码器或路径权限")
        sys.exit(1)

    # ---- 阶段1：推进（从全图缩小到左窗口） ----
    zoom_frames = int(args.fps * args.zoom_duration)
    if zoom_frames < 1:
        zoom_frames = 1

    for i in range(zoom_frames):
        t = i / (zoom_frames - 1) if zoom_frames > 1 else 1.0
        # 当前截取宽度：从 W 线性减小到 win_w
        cur_w = int(W - t * (W - win_w))
        # 截取区域：高度全取，宽度从左边开始
        roi = img[0:H, 0:cur_w]
        # 缩放到视频尺寸（推进时会有缩放，产生镜头推进效果）
        frame = cv2.resize(roi, video_size, interpolation=cv2.INTER_LANCZOS4)
        out.write(frame)

    # ---- 阶段2：横向扫描（窗口尺寸固定，从左到右） ----
    scan_frames = int(args.fps * args.scan_duration)
    if scan_frames < 1:
        scan_frames = 1

    max_x = W - win_w
    for i in range(scan_frames):
        t = i / (scan_frames - 1) if scan_frames > 1 else 1.0
        x = int(t * max_x)
        frame = img[0:H, x:x + win_w]  # shape = (H, win_w, 3)
        # 确保帧尺寸与视频尺寸一致
        if frame.shape[1] != win_w or frame.shape[0] != H:
            raise ValueError(f"帧尺寸 {frame.shape} 错误，期望 ({H}, {win_w})")
        frame = np.ascontiguousarray(frame)
        out.write(frame)

    out.release()
    print(f"视频已生成: {args.output_video}")

if __name__ == '__main__':
    image_file = '11.png'
    image = cv2.imread(image_file)
    video_left2right(image)