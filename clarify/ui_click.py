import cv2
import threading
import tkinter as tk
from tkinter import Listbox, MULTIPLE, Button, Label, Frame, filedialog
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont

from video_clarify import scale_image_pil, affinite_image, cv2pillow, pillow2cv, clarify_image_flow

# ========== 全局数据结构 ==========
points_mouse = []
points_pixel = []  # 存储点的列表，每个元素是(x, y)
image_path = '' # 选中的图片路径
img_original = None  # 原始图像
img_display = None  # 显示用的图像副本
img_processed = None
scale_x = 1
scale_y = 1
image_topx = 0
image_topy = 0
window_name = "Image Annotation Tool"
error_message = ''

## UI控件
listbox = None
canvas = None
canvas_width = 1000
canvas_height = 600
window_width = 1300
window_height = 700


# ========== OpenCV 鼠标回调函数 ==========

def on_canvas_click(event):
    global canvas, img_display, points_mouse, points_pixel, image_topx, image_topy

    if event.num == 1:  # 左键
        canvas_x = event.x - image_topx
        canvas_y = event.y - image_topy
        # 将显示坐标映射回原始图片坐标
        original_x = int(canvas_x / scale_x)
        original_y = int(canvas_y / scale_y)

        print(f'selected point: {canvas_x, canvas_y} {original_x, original_y}, {scale_x, scale_y}')

        points_mouse.append((canvas_x, canvas_y))
        points_pixel.append((original_x, original_y))
        # 刷新显示
        update_display()
        # 刷新右侧列表框
        update_listbox()

    elif event.num == 3:  # 右键
        print(f"右键点击: ({event.x}, {event.y})")
    else:
        print('other press')


def update_display():
    """在图像上绘制所有红色的圆圈，并显示"""
    global img_display, img_original, points_pixel, canvas_width, canvas_height
    if img_original is None:
        return

    org_image = img_original.copy()
    draw = ImageDraw.Draw(org_image)
    radius = 5
    font = ImageFont.load_default()
    fill_color = (255, 0, 0)  # RGB 红色
    for (x, y) in points_pixel:
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill='red',
            outline=None
        )
        text = f'({x}, {y})'
        draw.text((x + 5, y - 5), text, fill=fill_color, font=font)

    tar_image, tar_width, tar_height = scale_image_pil(org_image, canvas_width, canvas_height)

    display_photo = ImageTk.PhotoImage(tar_image)

    canvas.delete("all")
    canvas.update_idletasks()
    cx = canvas.winfo_width() // 2
    cy = canvas.winfo_height() // 2
    canvas.create_image(cx, cy, anchor=tk.CENTER, image=display_photo)
    canvas.config(scrollregion=(0, 0, tar_width, tar_height ))  # 可选：支持滚动区域
    canvas.image = display_photo


# ========== Tkinter GUI 部分 ==========
def select_image():
    global canvas, image_path, img_original, scale_y, scale_x, points_mouse, points_pixel, image_topx, image_topy
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
    if file_path:
        image_path = file_path
        img_original = Image.open(file_path)
        org_width, org_height = img_original.size

        # 注意：初次调用时 Canvas 可能还未完成布局，需要强制更新一下
        canvas.update_idletasks()
        resized_image, resize_w, resize_h = scale_image_pil(img_original, canvas_width, canvas_height)
        scale_x = resize_w / org_width
        scale_y = resize_h / org_height
        display_photo = ImageTk.PhotoImage(resized_image)

        # 清空 Canvas 之前的内容，并显示新图片
        canvas.delete("all")
        canvas.update_idletasks()
        cx = canvas.winfo_width() // 2
        cy = canvas.winfo_height() // 2

        canvas.create_image(cx, cy, anchor=tk.CENTER, image=display_photo)
        canvas.config(scrollregion=(0, 0, resize_w, resize_h))  # 可选：支持滚动区域
        canvas.image = display_photo

        image_topx = cx - resize_w // 2
        image_topy = cy - resize_h // 2

        # 清空之前的点集
        points_mouse.clear()
        points_pixel.clear()


def update_listbox():
    """刷新右侧列表框，显示所有点的坐标"""
    global listbox
    listbox.delete(0, tk.END)
    for i, (x, y) in enumerate(points_pixel):
        listbox.insert(tk.END, f"点 {i + 1}: ({x}, {y})")


def delete_selected_points():
    """删除列表中选中的点"""
    global points_pixel, listbox
    selected_indices = listbox.curselection()
    # 从后往前删除，避免索引错乱
    for idx in reversed(selected_indices):
        if idx < len(points_pixel):
            points_pixel.pop(idx)
    update_listbox()
    update_display()


def clear_all_points():
    """一键清除所有点"""
    points_mouse.clear()
    points_pixel.clear()
    update_listbox()
    update_display()


def save_image(save_and_update = 1):
    """
    保存处理后的图片
    save_and_update = 1, 保存图片到文件
    save_and_update = 2  仅更新主页图片
    save_and_update = 3 同时保存、更新主页图片
    """
    global img_processed, img_original

    if save_and_update == 2 or save_and_update == 3:
        img_original = img_processed
        clear_all_points()
        update_display()

    if save_and_update == 1 or save_and_update == 3:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".bmp",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if file_path:
            img_processed.save(file_path)



def skew_correction():

    global img_processed, img_original, points_pixel, error_message

    img_processed = img_original
    image_cv2 = pillow2cv(img_processed)
    if len(points_pixel) !=4:
        error_message = '请选择选四个点！！！'
        return

    skew_image_cv2, width, height = affinite_image(image_cv2, points_pixel[0], points_pixel[1], points_pixel[2], points_pixel[3])
    img_processed = cv2pillow(skew_image_cv2)
    open_sub_win(img_processed)


def enhance_clarify():
    global img_original, img_processed
    img_processed = img_original
    image_cv2 = pillow2cv(img_processed)

    image_enhance_cv = clarify_image_flow(image_cv2)
    image_enhance_pil = cv2pillow(image_enhance_cv)
    img_processed = image_enhance_pil
    open_sub_win(img_processed)


def open_sub_win(image_pil):

    global canvas_width, canvas_height, window_width, window_height

    display_image, resize_width, resize_height = scale_image_pil(image_pil, canvas_width, canvas_height)

    new_win = tk.Toplevel()
    new_win.title('校正后的图像')
    win_width = canvas_width
    win_height = canvas_height + 100
    screen_width = new_win.winfo_screenwidth()
    screen_height = new_win.winfo_screenheight()
    print(f'screen_width, screen_width = {screen_width, screen_height}')
    win_x = (screen_width - win_width) // 2  # 重命名为 win_x
    win_y = (screen_height - win_height) // 2  # 重命名为 win_y
    new_win.geometry(f"{win_width}x{win_height}+{win_x}+{win_y}")

    print(f'new win geometry = {win_width}x{win_height}+{win_x}+{win_y}')
    frame = tk.Frame(new_win)
    frame.pack(fill=tk.BOTH, expand=True)
    canvas = tk.Canvas(frame,
                       width=canvas_width,
                       height=canvas_height)
    canvas.pack(fill=tk.BOTH, expand=True)  # 添加这一行

    ## 添加保存按钮
    # 按钮框架靠下（保持不变）
    button_frame = tk.Frame(new_win)
    button_frame.pack(side=tk.BOTTOM, pady=10)
    btn_save1 = tk.Button(button_frame, text="保存图片", command=lambda: save_image(1))
    btn_save1.pack(side=tk.LEFT, padx=5)
    btn_save2 = tk.Button(button_frame, text="更新主图片", command=lambda: save_image(2))
    btn_save2.pack(side=tk.LEFT, padx=5)
    btn_save3 = tk.Button(button_frame, text="保存图片并更新主图片", command=lambda: save_image(3))
    btn_save3.pack(side=tk.LEFT, padx=5)


    # 显示图像 - 修正部分
    canvas.delete("all")
    canvas.update_idletasks()  # 确保尺寸已计算
    cx = canvas_width // 2
    cy = (canvas_height + 100) // 2
    print(f'cx, cy = {cx, cy}')
    photo = ImageTk.PhotoImage(display_image)
    canvas.create_image(cx, cy, anchor=tk.CENTER, image=photo)
    canvas.config(scrollregion=(0, 0, resize_width, resize_height))  # 只需一次
    canvas.image = photo



def ui_init():
    global listbox, canvas, canvas_width, canvas_height, window_width, window_height

    # 创建Tkinter主窗口（右侧控制面板）
    root = tk.Tk()
    # 获取屏幕尺寸
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.title("点坐标管理面板")
    window_width = window_width # 1300
    window_height = window_height # 700
    # 计算窗口位置，使其居中
    x_pos = (screen_width - window_width) // 2
    y_pos = (screen_height - window_height) // 2
    # 设置窗口几何形状：宽度x高度 + x偏移 + y偏移
    root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")

    # 界面布局
    # 创建一个 Canvas 组件，作为图片框
    canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg='gray')
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    canvas.bind("<Button-1>", on_canvas_click)

    # 右侧控制面板（暂时放一个按钮，你可以继续添加列表等）
    right_frame = tk.Frame(root, width=200, height=500, bg='#f0f0f0')
    right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)

    listbox = Listbox(right_frame, height=13, selectmode=MULTIPLE, font=("Arial", 10))
    listbox.pack(fill=tk.BOTH, expand=False, pady=5, anchor='w')
    Button(right_frame, text="打开图片", command=select_image, bg="green", fg="white").pack(pady=5, anchor='w')
    Button(right_frame, text="删除选中点", command=delete_selected_points, bg="red", fg="white").pack(pady=5, anchor='w')
    Button(right_frame, text="全部清除", command=clear_all_points).pack(pady=5, anchor='w')
    Button(right_frame, text="图片校正", command=skew_correction).pack(pady=5, anchor='w')
    Button(right_frame, text="图片增强", command=enhance_clarify).pack(pady=5, anchor='w')

    root.mainloop()



# ========== 主程序 ==========
if __name__ == "__main__":
    ui_init()