import cv2
import threading
import tkinter as tk
from tkinter import ttk, Listbox, MULTIPLE, Button, Label, Frame, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont

from video_clarify import scale_image_pil, affinite_image, cv2pillow, pillow2cv, clarify_image_flow

# ========== 多语言文本库 ==========
TEXTS = {
    'zh': {
        'window_title': '📷 智能图像标注与校正工具',
        'control_title': '✨ 控制中心',
        'point_list_title': '📌 标记点列表',
        'open_image': '📂 打开图片',
        'delete_point': '🗑️ 删除选中点',
        'clear_all': '🧹 全部清除',
        'process_title': '⚙️ 图像处理',
        'skew_correct': '🔧 透视校正 (需4点)',
        'enhance': '✨ 图像清晰度增强',
        'save': '💾 保存图片',
        'update_main': '🖼️ 更新主图',
        'save_and_update': '📁 保存并更新',
        'status_ready': '就绪',
        'point_prefix': '点',
        'delete_confirm': '已删除 {} 个点',
        'clear_confirm': '所有点已清除',
        'error_4points': '请先选择四个点进行校正！',
        'error_no_image': '没有可保存的图像',
        'save_success': '已保存至: {}',
        'update_success': '已更新主图',
        'subwin_title_correct': '校正后的图像',
        'subwin_title_enhance': '增强后的图像',
        'lang_switch': '🌐 English',
    },
    'en': {
        'window_title': '📷 Smart Image Annotation & Correction',
        'control_title': '✨ Control Center',
        'point_list_title': '📌 Marked Points',
        'open_image': '📂 Open Image',
        'delete_point': '🗑️ Delete Selected',
        'clear_all': '🧹 Clear All',
        'process_title': '⚙️ Image Processing',
        'skew_correct': '🔧 4-Pt Correction', # Perspective Correction (4 pts)
        'enhance': '✨ Enhance Clarity',
        'save': '💾 Save Image',
        'update_main': '🖼️ Update Main',
        'save_and_update': '📁 Save & Update',
        'status_ready': 'Ready',
        'point_prefix': 'Point',
        'delete_confirm': 'Deleted {} point(s)',
        'clear_confirm': 'All points cleared',
        'error_4points': 'Please select exactly 4 points for correction!',
        'error_no_image': 'No image to save',
        'save_success': 'Saved to: {}',
        'update_success': 'Main image updated',
        'subwin_title_correct': 'Corrected Image',
        'subwin_title_enhance': 'Enhanced Image',
        'lang_switch': '🌐 中文',
    }
}

# ========== 全局数据结构 ==========
current_lang = 'en'          # 当前语言：'zh' 或 'en'
points_mouse = []
points_pixel = []            # 存储原始图像上的点坐标
image_path = ''              # 当前图片路径
img_original = None          # 原始图像 (PIL)
img_display = None           # 显示用的图像副本
img_processed = None         # 处理后的图像
scale_x = 1.0                # 显示缩放比例 X
scale_y = 1.0                # 显示缩放比例 Y
image_topx = 0               # 图像在 Canvas 中的左上角 X 偏移
image_topy = 0               # 图像在 Canvas 中的左上角 Y 偏移

# UI 控件引用（用于语言刷新）
root = None
listbox = None
canvas = None
status_label = None
title_label = None
point_list_label = None
open_btn = None
delete_btn = None
clear_btn = None
process_label = None
skew_btn = None
enhance_btn = None
lang_btn = None

# 固定尺寸 (窗口禁止缩放，保证坐标映射正确)
canvas_width = 1000
canvas_height = 600
window_width = 1300
window_height = 700

# ========== 辅助函数：刷新界面文字 ==========
def refresh_ui_language():
    """根据当前语言刷新所有静态控件的文本"""
    global root, title_label, point_list_label, open_btn, delete_btn, clear_btn
    global process_label, skew_btn, enhance_btn, lang_btn, status_label

    if root:
        root.title(TEXTS[current_lang]['window_title'])
    if title_label:
        title_label.config(text=TEXTS[current_lang]['control_title'])
    if point_list_label:
        point_list_label.config(text=TEXTS[current_lang]['point_list_title'])
    if open_btn:
        open_btn.config(text=TEXTS[current_lang]['open_image'])
    if delete_btn:
        delete_btn.config(text=TEXTS[current_lang]['delete_point'])
    if clear_btn:
        clear_btn.config(text=TEXTS[current_lang]['clear_all'])
    if process_label:
        process_label.config(text=TEXTS[current_lang]['process_title'])
    if skew_btn:
        skew_btn.config(text=TEXTS[current_lang]['skew_correct'])
    if enhance_btn:
        enhance_btn.config(text=TEXTS[current_lang]['enhance'])
    if lang_btn:
        lang_btn.config(text=TEXTS[current_lang]['lang_switch'])
    if status_label:
        status_label.config(text=TEXTS[current_lang]['status_ready'])
    # 刷新列表框中的点前缀（动态内容）
    update_listbox()

def toggle_language():
    """切换中英文并刷新界面"""
    global current_lang
    current_lang = 'en' if current_lang == 'zh' else 'zh'
    refresh_ui_language()
    # 同时更新状态栏为就绪消息
    if status_label:
        status_label.config(text=TEXTS[current_lang]['status_ready'])

def show_temporary_message(msg_key, *args, duration=2000):
    """在状态栏显示临时消息（支持语言字典）
       msg_key: TEXTS 中的键名，如 'delete_confirm'
       args: 格式化参数
    """
    if status_label:
        msg = TEXTS[current_lang].get(msg_key, '').format(*args)
        old_text = status_label.cget("text")
        status_label.config(text=msg)
        root.after(duration, lambda: status_label.config(text=old_text))

# ========== 鼠标与显示 ==========
def on_canvas_click(event):
    global canvas, points_mouse, points_pixel, image_topx, image_topy

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

def update_status_message():
    """更新状态栏显示当前点数"""
    if status_label:
        status_label.config(text=f"{TEXTS[current_lang]['point_prefix']}: {len(points_pixel)}   |   {image_path.split('/')[-1] if image_path else TEXTS[current_lang]['status_ready']}")

# ========== 右侧控制逻辑 ==========
def select_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
    if file_path:
        global image_path, img_original
        image_path = file_path
        img = Image.open(file_path)
        refresh_main_display(img)

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

def update_listbox():
    """刷新右侧点列表（使用当前语言的“点”前缀）"""
    global listbox
    if listbox:
        listbox.delete(0, tk.END)
        prefix = TEXTS[current_lang]['point_prefix']
        for i, (x, y) in enumerate(points_pixel):
            listbox.insert(tk.END, f"{prefix} {i+1}: ({x}, {y})")

def delete_selected_points():
    selected = listbox.curselection()
    if not selected:
        return
    for idx in reversed(selected):
        if idx < len(points_pixel):
            points_pixel.pop(idx)
    update_listbox()
    update_display()
    update_status_message()
    show_temporary_message('delete_confirm', len(selected))

def clear_all_points():
    points_pixel.clear()
    points_mouse.clear()
    update_listbox()
    update_display()
    update_status_message()
    show_temporary_message('clear_confirm')

def skew_correction():
    if len(points_pixel) != 4:
        messagebox.showerror(TEXTS[current_lang]['window_title'], TEXTS[current_lang]['error_4points'])
        return

    img_cv = pillow2cv(img_original)
    skew_cv, w, h = affinite_image(img_cv, points_pixel[0], points_pixel[1], points_pixel[2], points_pixel[3])
    img_processed = cv2pillow(skew_cv)
    open_sub_win(img_processed, TEXTS[current_lang]['subwin_title_correct'])

def enhance_clarify():
    img_cv = pillow2cv(img_original)
    enhanced_cv = clarify_image_flow(img_cv)
    img_processed = cv2pillow(enhanced_cv)
    open_sub_win(img_processed, TEXTS[current_lang]['subwin_title_enhance'])

def save_image(save_mode=1, preview_image=None):
    """
    save_mode: 1=仅保存文件, 2=仅更新主图, 3=保存并更新
    preview_image: 如果传入则保存此图像，否则保存 img_processed
    """
    target_img = preview_image if preview_image else img_processed
    if target_img is None:
        messagebox.showwarning(TEXTS[current_lang]['window_title'], TEXTS[current_lang]['error_no_image'])
        return

    if save_mode == 2 or save_mode == 3:
        refresh_main_display(target_img)
        show_temporary_message('update_success')

    if save_mode == 1 or save_mode == 3:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if file_path:
            target_img.save(file_path)
            show_temporary_message('save_success', file_path)


def open_sub_win(image_pil, title):
    """弹出子窗口预览并保存/更新主图（美化版）"""
    sub = tk.Toplevel()
    sub.title(title)
    # 窗口大小：高度增加一些额外空间用于按钮和边距
    win_width = canvas_width
    win_height = canvas_height + 120
    sub.geometry(f"{win_width}x{win_height}")
    sub.resizable(False, False)
    sub.configure(bg='#f5f5f5')  # 柔和的背景色

    # 窗口居中（相对于主窗口）
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_w = root.winfo_width()
    root_h = root.winfo_height()
    x = root_x + (root_w - win_width) // 2
    y = root_y + (root_h - win_height) // 2
    sub.geometry(f"+{x}+{y}")

    # 显示图像（添加浅边框）
    display_img, w, h = scale_image_pil(image_pil, canvas_width, canvas_height)
    photo = ImageTk.PhotoImage(display_img)
    img_canvas = tk.Canvas(sub, width=canvas_width, height=canvas_height,
                           bg='#ffffff', highlightthickness=1, highlightbackground='#cccccc')
    img_canvas.pack(pady=15, padx=15)
    img_canvas.create_image(canvas_width//2, canvas_height//2, anchor=tk.CENTER, image=photo)
    img_canvas.image = photo

    # 按钮栏框架（增加阴影效果通过边框模拟）
    btn_frame = tk.Frame(sub, bg='#f5f5f5')
    btn_frame.pack(pady=10)

    # 按钮样式（加大加粗字体，不同功能不同颜色）
    btn_style_base = {'font': ('微软雅黑', 10, 'bold'), 'width': 16, 'pady': 6,
                      'relief': tk.RAISED, 'bd': 2, 'cursor': 'hand2'}

    # 保存按钮（绿色）
    btn_save = tk.Button(btn_frame, text=TEXTS[current_lang]['save'],
                         bg='#27ae60', fg='white',
                         activebackground='#2ecc71', activeforeground='white',
                         command=lambda: save_image(1, image_pil), **btn_style_base)
    btn_save.pack(side=tk.LEFT, padx=8)

    # 更新主图按钮（蓝色）
    btn_update = tk.Button(btn_frame, text=TEXTS[current_lang]['update_main'],
                           bg='#2980b9', fg='white',
                           activebackground='#3498db', activeforeground='white',
                           command=lambda: save_image(2, image_pil), **btn_style_base)
    btn_update.pack(side=tk.LEFT, padx=8)

    # 保存并更新按钮（橙色）
    btn_both = tk.Button(btn_frame, text=TEXTS[current_lang]['save_and_update'],
                         bg='#e67e22', fg='white',
                         activebackground='#f39c12', activeforeground='white',
                         command=lambda: save_image(3, image_pil), **btn_style_base)
    btn_both.pack(side=tk.LEFT, padx=8)

    # 可选：添加一个简单的分隔线（视觉效果）
    separator = tk.Frame(sub, height=2, bg='#cccccc')
    separator.pack(fill=tk.X, padx=20, pady=(0, 10))

    # 绑定键盘 ESC 键关闭窗口
    def close_win(event=None):
        sub.destroy()
    sub.bind('<Escape>', close_win)


# ========== 界面初始化 ==========
def ui_init():
    global root, listbox, canvas, status_label, title_label, point_list_label
    global open_btn, delete_btn, clear_btn, process_label, skew_btn, enhance_btn, lang_btn

    root = tk.Tk()
    root.title(TEXTS[current_lang]['window_title'])
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
    title_label = tk.Label(right_frame, text=TEXTS[current_lang]['control_title'], font=('微软雅黑', 14, 'bold'), bg='#ecf0f1', fg='#2c3e50')
    title_label.pack(pady=(10, 5))

    # 语言切换按钮
    lang_btn = tk.Button(right_frame, text=TEXTS[current_lang]['lang_switch'], font=('微软雅黑', 9), width=10, command=toggle_language)
    lang_btn.pack(pady=(0,5))

    # 点列表管理
    list_frame = tk.LabelFrame(right_frame, text=TEXTS[current_lang]['point_list_title'], font=('微软雅黑', 10), bg='#ecf0f1', fg='#2c3e50')
    list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    point_list_label = list_frame


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

    open_btn = tk.Button(btn_frame1, text=TEXTS[current_lang]['open_image'], command=select_image, bg='#3498db', fg='white', **btn_style)
    open_btn.pack(pady=2)
    delete_btn = tk.Button(btn_frame1, text=TEXTS[current_lang]['delete_point'], command=delete_selected_points, bg='#e74c3c', fg='white', **btn_style)
    delete_btn.pack(pady=2)
    clear_btn = tk.Button(btn_frame1, text=TEXTS[current_lang]['clear_all'], command=clear_all_points, bg='#95a5a6', fg='white', **btn_style)
    clear_btn.pack(pady=2)

    # 校正与增强分组
    proc_frame = tk.LabelFrame(right_frame, text=TEXTS[current_lang]['process_title'], font=('微软雅黑', 10), bg='#ecf0f1', fg='#2c3e50')
    proc_frame.pack(fill=tk.X, padx=10, pady=10)
    process_label = proc_frame

    skew_btn = tk.Button(proc_frame, text=TEXTS[current_lang]['skew_correct'], command=skew_correction, bg='#9b59b6', fg='white', **btn_style)
    skew_btn.pack(pady=5, padx=5)
    enhance_btn = tk.Button(proc_frame, text=TEXTS[current_lang]['enhance'], command=enhance_clarify, bg='#1abc9c', fg='white', **btn_style)
    enhance_btn.pack(pady=5, padx=5)

    # 状态栏
    status_frame = tk.Frame(right_frame, bg='#ecf0f1', height=40)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
    status_label = tk.Label(status_frame, text=TEXTS[current_lang]['status_ready'], font=('微软雅黑', 9), bg='#ecf0f1', fg='#7f8c8d')
    status_label.pack()

    root.mainloop()

# ========== 主程序 ==========
if __name__ == "__main__":
    ui_init()