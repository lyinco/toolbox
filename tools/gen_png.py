import os
from PIL import Image, ImageDraw


def create_gradient_button(filename, width, height, start_color, end_color):
    """
    生成带有上边缘高光和水平渐变的高级科技感按钮
    """
    # 1. 创建基础渐变图层
    base_img = Image.new("RGB", (width, height))

    # 2. 绘制水平方向丝滑渐变
    for x in range(width):
        # 计算当前列的颜色比例
        r = int(start_color[0] + (end_color[0] - start_color[0]) * (x / width))
        g = int(start_color[1] + (end_color[1] - start_color[1]) * (x / width))
        b = int(start_color[2] + (end_color[2] - start_color[2]) * (x / width))

        # 3. 施加垂直方向的“微光立体照明”叠加 (越往上越亮，模拟上方打光)
        for y in range(height):
            # 顶部增加高光，底部增加微弱暗影
            factor = 1.12 - (y / height) * 0.22

            nr = max(0, min(255, int(r * factor)))
            ng = max(0, min(255, int(g * factor)))
            nb = max(0, min(255, int(b * factor)))

            base_img.putpixel((x, y), (nr, ng, nb))

    # 4. 绘制精致的顶边1像素极细高光线
    draw = ImageDraw.Draw(base_img)
    # 高光色为起始色的淡化版
    highlight_color = (
        min(255, int(start_color[0] * 1.25)),
        min(255, int(start_color[1] * 1.25)),
        min(255, int(start_color[2] * 1.25))
    )
    draw.line([(0, 0), (width, 0)], fill=highlight_color, width=1)

    # 5. 保存图片
    base_img.save(filename, "PNG")
    print(f"成功生成高级光影按钮: {os.path.abspath(filename)}")


def create_background_gradient(filename, width, height, top_left_color, bottom_right_color):
    """
    生成一个平滑的、对角线方向的高级雾蓝渐变背景
    """
    # 创建基础画布
    bg_img = Image.new("RGB", (width, height))

    # 解析起始和结束颜色通道
    r1, g1, b1 = top_left_color
    r2, g2, b2 = bottom_right_color

    # 对角线渐变算法：根据像素在对角线方向上的投影计算颜色
    max_dist = width + height

    for y in range(height):
        for x in range(width):
            # 计算当前像素点在对角线上的相对位置比例 (0.0 到 1.0)
            ratio = (x + y) / max_dist

            # 线性插值混合颜色
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)

            bg_img.putpixel((x, y), (r, g, b))

    bg_img.save(filename, "PNG")
    print(f"成功生成高级全局背景图: {os.path.abspath(filename)}")


if __name__ == "__main__":
    # 按钮标准尺寸 (对应 UI 代码中的空间)
    BTN_WIDTH = 160
    BTN_HEIGHT = 32

    # ====== 1. 生成常规按钮 (深邃极光蓝渐变) ======
    # 极光蓝 (#3A7BD5) 渐变到 科技深蓝 (#3A6073)
    create_gradient_button(
        filename="btn_blue.png",
        width=BTN_WIDTH,
        height=BTN_HEIGHT,
        start_color=(58, 123, 213),
        end_color=(58, 96, 115)
    )

    # ====== 2. 生成核心算法按钮 (明亮智能青蓝渐变) ======
    # 智能青 (#00C6FF) 渐变到 霓虹蓝 (#0072FF)
    create_gradient_button(
        filename="btn_cyan.png",
        width=BTN_WIDTH,
        height=BTN_HEIGHT,
        start_color=(0, 198, 255),
        end_color=(0, 114, 255)
    )

    WINDOW_WIDTH = 1020
    WINDOW_HEIGHT = 680
    # 冰晶白 (#F4F7FB) 渐变到 悬浮浅蓝 (#E1E9F5)
    create_background_gradient(
        filename="bg_gradient.png",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        top_left_color=(244, 247, 251),
        bottom_right_color=(225, 233, 245)
    )