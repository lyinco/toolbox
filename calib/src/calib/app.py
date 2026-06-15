"""应用启动逻辑。"""

import sys
sys.path.insert(0, '/Users/lingcai/Documents/git_src/toolbox/calib/src')

from PySide6.QtWidgets import QApplication

from calib import default_output_dir, package_root
from calib.config import AppConfig
from calib.ui import MainWindow


def main() -> None:
    print("1. 开始加载配置...")
    try:
        config_path = package_root() / "config" / "defaults.yaml"
        print(f"   配置文件路径: {config_path}")
        print(f"   文件是否存在: {config_path.exists()}")
        
        config = AppConfig.load(config_path)
        print("2. 配置加载成功")
    except Exception as e:
        print(f"配置加载失败: {e}")
        traceback.print_exc()
        sys.exit(1)

    print("3. 处理输出目录...")
    try:
        out_dir = default_output_dir()
        if config.export.output_dir:
            out_dir = Path(config.export.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"   输出目录: {out_dir}")
    except Exception as e:
        print(f"目录创建失败: {e}")
        traceback.print_exc()

    print("4. 创建 QApplication...")
    app = QApplication(sys.argv)

    print("5. 创建主窗口...")
    try:
        window = MainWindow(config)
        print("6. 主窗口创建成功")
    except Exception as e:
        print(f"主窗口创建失败: {e}")
        traceback.print_exc()
        sys.exit(1)

    print("7. 显示窗口...")
    window.show()
    print("8. 窗口显示命令已执行")

    print("9. 进入事件循环...")
    sys.exit(app.exec())
    print("10. 程序结束")  # 这行不会执行

if __name__ == "__main__":
    main()