import os
import shutil
import subprocess
import sys
from pathlib import Path

# ======================== 配置区（请根据实际路径修改） ========================
# 源目录配置
BACK_SRC = r"E:\Soonwin_OA\soonwin-os-Python-Server"  # 后端源目录
FRONT_SRC = r"E:\Soonwin_OA\soonwin-oa-VUE-FrontEnd"  # 前端源目录
BASE_DIR = r"E:\Soonwin_OA"                           # OA根目录

# 迁移包目录配置
DEPLOY_ROOT = Path(os.path.expanduser("~")) / "Desktop" / "Soonwin_OA"
BACK_DEPLOY = DEPLOY_ROOT / "SoonwinOA_Backend"       # 迁移包内后端文件夹
FRONT_DEPLOY = DEPLOY_ROOT / "SoonwinOA_Frontend"     # 迁移包内前端文件夹

# 需要复制的后端根文件（新增run.py、wsgi.py）
BACKEND_ROOT_FILES = [
    "config.py",
    "extensions.py",
    "soonwin_oa.db",
    "requirements.txt",
    "run.py",          # 新增：缺失的run.py
    "wsgi.py"          # 新增：缺失的wsgi.py
]

# 需要复制的后端子文件夹
BACKEND_FOLDERS = [
    "app",
    "migrations",
    "instance",
    "other"
]

# 脚本同级目录需要复制的文件（启动文件，将放到迁移包根目录）
SCRIPT_ROOT_FILES = [
    "run_server.py",
    "启动服务器.bat"
]

# 额外部署文件（OA根目录下）
EXTRA_DEPLOY_FILES = [
    "Soonwin OA 系统 - Windows 生产环境部署指南.md",
    "启动服务器_生产环境_迁移版.bat"
]

# 后端排除的冗余文件/文件夹（仅排除后端的assets，前端不排除）
BACKEND_EXCLUDE_PATTERNS = [
    "venv",
    "__pycache__",
    "*.pyc",
    "*.log",
    "*.tmp",
    ".gitignore",
    ".git",
    "assets"  # 仅排除后端的assets
]

# 前端排除的冗余文件/文件夹（不排除assets）
FRONTEND_EXCLUDE_PATTERNS = [
    "venv",
    "__pycache__",
    "*.pyc",
    "*.log",
    "*.tmp",
    ".gitignore",
    ".git"
]
# ============================================================================

def print_separator():
    """打印分隔线"""
    print("=" * 50)

def clean_directory(dir_path: Path):
    """清空并重建目录"""
    if dir_path.exists():
        print(f"[清理] 清空目录: {dir_path}")
        shutil.rmtree(dir_path, ignore_errors=True)
    dir_path.mkdir(parents=True, exist_ok=True)
    print(f"[创建] 目录已创建: {dir_path}")

def generate_requirements_txt():
    """生成最新的requirements.txt（包含Python版本信息）"""
    req_file = Path(BACK_SRC) / "requirements.txt"

    # 获取用户确认
    confirm = input("\n是否生成最新的requirements.txt？(y/n，默认n): ").strip().lower()
    if confirm != "y":
        print("使用现有的requirements.txt文件。")
        return

    print("\n正在生成requirements.txt...")
    try:
        # 优先使用虚拟环境的Python
        python_exe = Path(BACK_SRC) / "venv" / "Scripts" / "python.exe"
        if not python_exe.exists():
            python_exe = sys.executable  # 使用系统Python

        # 生成requirements.txt
        with open(req_file, "w", encoding="utf-8") as f:
            # 写入Python版本
            version_output = subprocess.check_output(
                [python_exe, "--version"], stderr=subprocess.STDOUT, text=True
            )
            f.write(f"# Python Version: {version_output.strip()}\n\n")

            # 写入依赖列表
            freeze_output = subprocess.check_output(
                [python_exe, "-m", "pip", "freeze"], text=True
            )
            f.write(freeze_output)

        print("requirements.txt生成成功！")
    except Exception as e:
        print(f"[错误] 生成requirements.txt失败: {e}")

def copy_file(src: Path, dest: Path):
    """复制单个文件，带错误处理"""
    try:
        if src.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            print(f"[复制成功] {src.name} -> {dest.parent.name}")
            return True
        else:
            print(f"[跳过] 文件不存在: {src}")
            return False
    except Exception as e:
        print(f"[复制失败] {src.name}: {e}")
        return False

def copy_folder(src: Path, dest: Path, exclude_patterns: list = None):
    """复制文件夹，支持排除指定模式"""
    if exclude_patterns is None:
        exclude_patterns = []

    try:
        if src.exists():
            # 清空目标文件夹
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)

            # 复制文件夹
            shutil.copytree(
                src,
                dest,
                ignore=shutil.ignore_patterns(*exclude_patterns),
                dirs_exist_ok=True
            )
            print(f"[复制成功] {src.name} 文件夹 -> {dest.parent.name}")

            # 清理冗余文件
            clean_redundant_files(dest, exclude_patterns)
            return True
        else:
            print(f"[跳过] 文件夹不存在: {src}")
            return False
    except Exception as e:
        print(f"[复制失败] {src.name}: {e}")
        return False

def clean_redundant_files(dir_path: Path, exclude_patterns: list = None):
    """清理冗余文件（__pycache__、.pyc等）"""
    if exclude_patterns is None:
        exclude_patterns = []

    try:
        # 清理__pycache__文件夹
        for cache_dir in dir_path.rglob("__pycache__"):
            if cache_dir.is_dir():
                shutil.rmtree(cache_dir, ignore_errors=True)

        # 清理指定后缀的冗余文件
        for ext in ["*.pyc", "*.log", "*.tmp"]:
            if ext not in exclude_patterns:
                for file in dir_path.rglob(ext):
                    if file.is_file():
                        file.unlink(missing_ok=True)

        print(f"[清理完成] {dir_path.name} 文件夹冗余文件已清理")
    except Exception as e:
        print(f"[清理失败] {dir_path.name}: {e}")

def main():
    """主执行函数"""
    # 设置控制台编码为UTF-8
    if sys.platform == "win32":
        os.system("chcp 65001 > nul")

    print_separator()
    print("          OA后端/前端迁移文件同步脚本 (Python版)")
    print_separator()

    # 1. 生成requirements.txt
    generate_requirements_txt()

    # 2. 前置检查
    print_separator()
    print("开始同步迁移文件...")
    print(f"后端源目录: {BACK_SRC}")
    print(f"前端源目录: {FRONT_SRC}")
    print(f"迁移包目录: {DEPLOY_ROOT}")
    print_separator()

    # 检查后端源目录是否存在
    if not Path(BACK_SRC).exists():
        print(f"[错误] 后端源目录不存在: {BACK_SRC}")
        input("按回车键退出...")
        sys.exit(1)

    # 3. 清空并重建迁移目录
    clean_directory(DEPLOY_ROOT)
    clean_directory(BACK_DEPLOY)
    clean_directory(FRONT_DEPLOY)

    # 4. 复制脚本同级的启动文件到迁移包根目录（关键修复）
    print("\n" + "=" * 30)
    print("复制启动文件到迁移包根目录")
    print("=" * 30)
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    for filename in SCRIPT_ROOT_FILES:
        src_file = script_dir / filename
        dest_file = DEPLOY_ROOT / filename  # 放到根目录，而非后端文件夹
        copy_file(src_file, dest_file)

    # 5. 复制后端根目录核心文件（新增run.py、wsgi.py）
    print("\n" + "=" * 30)
    print("复制后端根目录核心文件")
    print("=" * 30)
    back_src_path = Path(BACK_SRC)
    for filename in BACKEND_ROOT_FILES:
        src_file = back_src_path / filename
        dest_file = BACK_DEPLOY / filename
        copy_file(src_file, dest_file)

    # 6. 复制后端子文件夹（排除后端assets）
    print("\n" + "=" * 30)
    print("复制后端子文件夹")
    print("=" * 30)
    for folder_name in BACKEND_FOLDERS:
        src_folder = back_src_path / folder_name
        dest_folder = BACK_DEPLOY / folder_name
        copy_folder(src_folder, dest_folder, BACKEND_EXCLUDE_PATTERNS)

    # 7. 复制额外部署文件（OA根目录下）
    print("\n" + "=" * 30)
    print("复制额外部署文件")
    print("=" * 30)
    base_dir_path = Path(BASE_DIR)
    for filename in EXTRA_DEPLOY_FILES:
        src_file = base_dir_path / filename
        dest_file = DEPLOY_ROOT / filename
        copy_file(src_file, dest_file)

    # 8. 复制前端dist目录（不排除前端assets）
    print("\n" + "=" * 30)
    print("复制前端dist目录（保留assets）")
    print("=" * 30)
    front_dist_src = Path(FRONT_SRC) / "dist"
    if front_dist_src.exists():
        copy_folder(front_dist_src, FRONT_DEPLOY, FRONTEND_EXCLUDE_PATTERNS)
    else:
        print(f"[警告] 前端dist目录不存在: {front_dist_src}")

    # 9. 最终清理冗余文件
    print("\n" + "=" * 30)
    print("最终清理冗余文件")
    print("=" * 30)
    clean_redundant_files(BACK_DEPLOY, BACKEND_EXCLUDE_PATTERNS)
    clean_redundant_files(FRONT_DEPLOY, FRONTEND_EXCLUDE_PATTERNS)

    # 完成提示
    print_separator()
    print("[成功] 迁移文件同步完成！")
    print(f"迁移包根目录: {DEPLOY_ROOT}")
    print(f"后端文件目录: {BACK_DEPLOY}")
    print(f"前端文件目录: {FRONT_DEPLOY}")
    print(f"启动文件位置: {DEPLOY_ROOT} (run_server.py、启动服务器.bat)")
    print_separator()
    input("按回车键退出...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[取消] 用户中断了操作")
    except Exception as e:
        print(f"\n\n[错误] 脚本执行失败: {e}")
        input("按回车键退出...")