# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

# 1. 自动定位当前环境的 site-packages 路径
site_packages_dir = r"F:\CONDA_ENVS\envs\realesrgan\Lib\site-packages"


a = Analysis(
    ['ui_click.py'], # 你的主程序脚本
    pathex=['F:/git_src/toolbox/clarify'],
    binaries=[],
    datas=[
        ('icons', 'icons'),
        ('models', 'models'),
        (os.path.join(site_packages_dir, 'basicsr', 'losses'), os.path.join('basicsr', 'losses')),  # 复制整个 basicsr
        (os.path.join(site_packages_dir, 'basicsr', 'archs'), os.path.join('basicsr', 'archs')),
        (os.path.join(site_packages_dir, 'basicsr', 'data'), os.path.join('basicsr', 'data')),
        (os.path.join(site_packages_dir, 'basicsr', 'models'), os.path.join('basicsr', 'models')),
        (os.path.join(site_packages_dir, 'realesrgan', 'archs'), os.path.join( 'realesrgan', 'archs')),
        (os.path.join(site_packages_dir, 'realesrgan', 'data'), os.path.join( 'realesrgan', 'data')),
        (os.path.join(site_packages_dir, 'realesrgan', 'models'), os.path.join( 'realesrgan', 'models')),
    ],
    hiddenimports=[
        'cv2',
        'scipy',
        'torch',
        'torchvision',
        'numpy',
        'PIL',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'realesrgan',
        'realesrgan.archs',
        'realesrgan.models',
        'basicsr',
        'basicsr.archs',
        'basicsr.models',
        'basicsr.ops',        # 显式添加 ops 模块
        'basicsr.ops.fused_act',  # 具体子模块
        'basicsr.ops.upfirdn2d',
        # 可能还需要其他 ops 子模块
        'torchvision.transforms.functional',
        'torchvision.transforms.functional_tensor',
        'torchvision.transforms.functional_pil',
    ] + collect_submodules('basicsr'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5', 'PySide6', 'matplotlib',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# 注意：为了让 --noconsole 生效，这里的 console 必须为 False
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True, # 开启目录模式的关键：排除二进制文件不打入单文件
    name='ui_click',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # 【核心】False 代表隐藏控制台黑窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# COLLECT 模块是 --onedir (目录模式) 的核心。它会创建一个文件夹
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ui_click', # 最终生成的文件夹名称
)