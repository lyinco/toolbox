import cv2
import threading
import tkinter as tk
from tkinter import ttk, Listbox, MULTIPLE, Button, Label, Frame, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont

from video_clarify import scale_image_pil, affinite_image, cv2pillow, pillow2cv, clarify_image_flow

# ========== 全局数据结构 ==========
points_mouse = []
points_pixel = []          # 存储原始图像上的点坐标
image_path = ''            # 当前图片路径
img_original = None        # 原始图像 (PIL)
img_display = None         # 显示用的图像副本
img_processed = None       # 处理后的图像
scale_x = 1.0              # 显示缩放比例 X
scale_y = 1.0              # 显示缩放比例 Y
image_topx = 0             # 图像在 Canvas 中的左上角 X 偏移
image_topy = 0             # 图像在 Canvas 中的左上角 Y 偏移
error_message = ''         # 错误提示信息

# UI 控件引用
listbox = None
canvas = None
status_label = None        # 状态栏标签
error_label = None         # 错误信息标签

# 固定尺寸 (窗口禁止缩放，保证坐标映射正确)
canvas_width = 1000
canvas_height = 600
window_width = 1300
window_height = 700

# ========== 辅助函数：刷新主显示区 ==========
def refresh_main_display(new_image):
    """重新加载主显示区的图像，重置缩放和点集"""
    global img_original, scale_x, scale_y, image_topx, image_topy, points_pixel, points_mouse, canvas

    img_original = new_image.copy()
    points_pixel.clear()
    points_mouse.clear()
    update_listbox()

    # 计算缩放比例并显示
    org_width, org_height = img_original.size
    resized_image, resize_w, resize_h = scale_image_pil(img_original, canvas_width, canvas_height)
    scale_x = resize_w / org_width
    scale_y = resize_h / org_height
    display_photo = ImageTk.PhotoImage(resized_image)

    canvas.delete("all")
    canvas.update_idletasks()
    cx = canvas.winfo_width() // 2
    cy = canvas.winfo_height() // 2
    canvas.create_image(cx, cy, anchor=tk.CENTER, image=display_photo)
    canvas.config(scrollregion=(0, 0, resize_w, resize_h))
    canvas.image = display_photo

    image_topx = cx - resize_w // 2
    image_topy = cy - resize_h // 2

    update_status_message()

def update_status_message():
    """更新状态栏信息"""
    if status_label:
        status_label.config(text=f"当前点数: {len(points_pixel)}   |   图片: {image_path.split('/')[-1] if image_path else '无'}")

# ========== 鼠标与显示 ==========
def on_canvas_click(event):
    global canvas, img_display, points_mouse, points_pixel, image_topx, image_topy

    if event.num == 1:  # 左键添加点
        canvas_x = event.x - image_topx
        canvas_y = event.y - image_topy
        # 边界检查
        if canvas_x < 0 or canvas_y < 0 or canvas_x > canvas.winfo_width() or canvas_y > canvas.winfo_height():
            return
        original_x = int(canvas_x / scale_x)
        original_y = int(canvas_y / scale_y)

        points_mouse.append((canvas_x, canvas_y))
        points_pixel.append((original_x, original_y))
        update_display()
        update_listbox()
        update_status_message()
    elif event.num == 3:  # 右键（预留）
        pass

def update_display():
    """在图像上绘制所有点并刷新 Canvas"""
    global img_display, img_original, points_pixel, canvas

    if img_original is None:
        return

    # 在原始图像的副本上绘制
    draw_img = img_original.copy()
    draw = ImageDraw.Draw(draw_img)
    radius = 5
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()

    for (x, y) in points_pixel:
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill='red', outline='white')
        draw.text((x + 5, y - 5), f"({x},{y})", fill='yellow', font=font)

    # 缩放并显示
    tar_image, tar_width, tar_height = scale_image_pil(draw_img, canvas_width, canvas_height)
    display_photo = ImageTk.PhotoImage(tar_image)

    canvas.delete("all")
    canvas.update_idletasks()
    cx = canvas.winfo_width() // 2
    cy = canvas.winfo_height() // 2
    canvas.create_image(cx, cy, anchor=tk.CENTER, image=display_photo)
    canvas.config(scrollregion=(0, 0, tar_width, tar_height))
    canvas.image = display_photo

# ========== 右侧控制逻辑 ==========
def select_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
    if file_path:
        global image_path
        image_path = file_path
        img = Image.open(file_path)
        refresh_main_display(img)

def update_listbox():
    """刷新右侧点列表"""
    global listbox
    listbox.delete(0, tk.END)
    for i, (x, y) in enumerate(points_pixel):
        listbox.insert(tk.END, f"点 {i+1}: ({x}, {y})")

def delete_selected_points():
    global points_pixel, listbox
    selected = listbox.curselection()
    for idx in reversed(selected):
        if idx < len(points_pixel):
            points_pixel.pop(idx)
    update_listbox()
    update_display()
    update_status_message()
    show_temporary_message(f"已删除 {len(selected)} 个点")

def clear_all_points():
    points_pixel.clear()
    points_mouse.clear()
    update_listbox()
    update_display()
    update_status_message()
    show_temporary_message("所有点已清除")

def skew_correction():
    global img_processed, img_original, points_pixel, error_message
    if len(points_pixel) != 4:
        messagebox.showerror("错误", "请先选择四个点进行校正！")
        return

    img_cv = pillow2cv(img_original)
    skew_cv, w, h = affinite_image(img_cv, points_pixel[0], points_pixel[1], points_pixel[2], points_pixel[3])
    img_processed = cv2pillow(skew_cv)
    open_sub_win(img_processed, "校正后的图像")

def enhance_clarify():
    global img_original, img_processed
    img_cv = pillow2cv(img_original)
    enhanced_cv = clarify_image_flow(img_cv)
    img_processed = cv2pillow(enhanced_cv)
    open_sub_win(img_processed, "增强后的图像")

def save_image(save_mode=1, preview_image=None):
    """
    save_mode: 1=仅保存文件, 2=仅更新主图, 3=保存并更新
    preview_image: 如果传入则保存此图像，否则保存 img_processed
    """
    global img_original, img_processed
    target_img = preview_image if preview_image else img_processed
    if target_img is None:
        messagebox.showwarning("警告", "没有可保存的图像")
        return

    if save_mode == 2 or save_mode == 3:
        refresh_main_display(target_img)
        show_temporary_message("已更新主图")

    if save_mode == 1 or save_mode == 3:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG 文件", "*.png"), ("JPEG 文件", "*.jpg"), ("所有文件", "*.*")]
        )
        if file_path:
            target_img.save(file_path)
            show_temporary_message(f"已保存至: {file_path}")

def show_temporary_message(msg, duration=2000):
    """在状态栏短暂显示消息，2秒后恢复"""
    if status_label:
        old_text = status_label.cget("text")
        status_label.config(text=msg)
        root.after(duration, lambda: status_label.config(text=old_text))

def open_sub_win(image_pil, title="处理结果"):
    """弹出子窗口预览并保存/更新主图"""
    sub = tk.Toplevel()
    sub.title(title)
    sub.geometry(f"{canvas_width}x{canvas_height+80}")
    sub.resizable(False, False)
    sub.configure(bg='#f0f0f0')

    # 显示图像
    display_img, w, h = scale_image_pil(image_pil, canvas_width, canvas_height)
    photo = ImageTk.PhotoImage(display_img)
    img_canvas = tk.Canvas(sub, width=canvas_width, height=canvas_height, bg='#e0e0e0', highlightthickness=0)
    img_canvas.pack(pady=10)
    img_canvas.create_image(canvas_width//2, canvas_height//2, anchor=tk.CENTER, image=photo)
    img_canvas.image = photo

    # 按钮栏
    btn_frame = tk.Frame(sub, bg='#f0f0f0')
    btn_frame.pack(pady=10)
    style = {'font': ('微软雅黑', 10), 'width': 18, 'padx': 5, 'pady': 3}
    tk.Button(btn_frame, text="💾 保存图片", command=lambda: save_image(1, image_pil), **style).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="🖼️ 更新主图", command=lambda: save_image(2, image_pil), **style).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="📁 保存并更新", command=lambda: save_image(3, image_pil), **style).pack(side=tk.LEFT, padx=5)

# ========== 界面初始化 ==========
def ui_init():
    global listbox, canvas, status_label, error_label, root

    root = tk.Tk()
    root.title("📷 智能图像标注与校正工具")
    root.geometry(f"{window_width}x{window_height}")
    root.resizable(False, False)
    root.configure(bg='#2c3e50')

    # ========== 左侧图像区域 ==========
    left_frame = tk.Frame(root, bg='#34495e', relief=tk.GROOVE, bd=2)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    canvas = tk.Canvas(left_frame, width=canvas_width, height=canvas_height, bg='#2c3e50', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    canvas.bind("<Button-1>", on_canvas_click)

    # ========== 右侧控制面板 ==========
    right_frame = tk.Frame(root, bg='#ecf0f1', width=280)
    right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
    right_frame.pack_propagate(False)

    # 标题
    title_label = tk.Label(right_frame, text="✨ 控制中心", font=('微软雅黑', 14, 'bold'), bg='#ecf0f1', fg='#2c3e50')
    title_label.pack(pady=(10, 5))

    # 点列表管理
    list_frame = tk.LabelFrame(right_frame, text="📌 标记点列表", font=('微软雅黑', 10), bg='#ecf0f1', fg='#2c3e50')
    list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    listbox = Listbox(list_frame, height=12, font=('Consolas', 10), selectbackground='#3498db',
                      selectforeground='white', bg='white', fg='#2c3e50', relief=tk.FLAT)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)

    # 按钮样式
    btn_style = {'font': ('微软雅黑', 9), 'width': 20, 'pady': 4, 'relief': tk.RAISED, 'bd': 1}
    btn_frame1 = tk.Frame(right_frame, bg='#ecf0f1')
    btn_frame1.pack(pady=5)

    tk.Button(btn_frame1, text="📂 打开图片", command=select_image, bg='#3498db', fg='white', **btn_style).pack(pady=2)
    tk.Button(btn_frame1, text="🗑️ 删除选中点", command=delete_selected_points, bg='#e74c3c', fg='white', **btn_style).pack(pady=2)
    tk.Button(btn_frame1, text="🧹 全部清除", command=clear_all_points, bg='#95a5a6', fg='white', **btn_style).pack(pady=2)

    # 校正与增强分组
    proc_frame = tk.LabelFrame(right_frame, text="⚙️ 图像处理", font=('微软雅黑', 10), bg='#ecf0f1', fg='#2c3e50')
    proc_frame.pack(fill=tk.X, padx=10, pady=10)

    tk.Button(proc_frame, text="🔧 透视校正 (需4点)", command=skew_correction, bg='#9b59b6', fg='white', **btn_style).pack(pady=5, padx=5)
    tk.Button(proc_frame, text="✨ 图像清晰度增强", command=enhance_clarify, bg='#1abc9c', fg='white', **btn_style).pack(pady=5, padx=5)

    # 状态栏
    status_frame = tk.Frame(right_frame, bg='#ecf0f1', height=40)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
    status_label = tk.Label(status_frame, text="就绪", font=('微软雅黑', 9), bg='#ecf0f1', fg='#7f8c8d')
    status_label.pack()

    root.mainloop()

# ========== 主程序 ==========
if __name__ == "__main__":
    ui_init()