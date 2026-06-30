import os
import shutil
import subprocess
import sys
import sqlite3
from pathlib import Path
from typing import List, Tuple

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
    # "soonwin_oa.db",
    "soonwin_oa_dev.db",
    "requirements.txt",
    "run.py",               # Flask 入口
    "wsgi.py",              # WSGI 入口
    "restart_services.py",  # 独立重启脚本（备份/同步/启停）
]

# 需要复制的后端子文件夹
BACKEND_FOLDERS = [
    "app",
    "migrations",
    "other"
]

# 【简化/修复】直接指定需要复制的后端assets子目录（精准到TemplateImg）
BACKEND_ASSETS_COPY = "TemplateImg"  # 仅复制assets下的TemplateImg目录

# 脚本同级目录需要复制的文件（启动文件，将放到迁移包根目录）
SCRIPT_ROOT_FILES = [
    "run_server.py",
    "启动服务器.bat",
    "startPythonServe.bat"
]

# 额外部署文件（OA根目录下）
EXTRA_DEPLOY_FILES = [
    "Soonwin OA 系统 - Windows 生产环境部署指南.md",
]

# 后端排除的冗余文件/文件夹【保持】：保留assets整体排除（核心！）
BACKEND_EXCLUDE_PATTERNS = [
    "venv",
    "__pycache__",
    "*.pyc",
    "*.log",
    "*.tmp",
    ".gitignore",
    ".git",
    "assets"  # 【保持】整体排除assets，后续单独复制指定子目录
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

# 关键分析代码复制配置
ANALYSIS_CODE_ROOT = Path(os.path.expanduser("~")) / "Desktop" / "OA_关键分析代码"
# 后端关键代码目录/文件（Flask核心）
BACKEND_ANALYSIS_FILES = [
    "app/__init__.py",
    "app/models",
    "app/routes",
    "app/utils",
    "config.py",
    "extensions.py",
    "run.py",
    "wsgi.py"
]
# 前端关键代码目录/文件（Vue核心）
FRONTEND_ANALYSIS_FILES = [
    "src/api",
    "src/components",
    "src/views",
    "src/utils/request.ts",
    "src/types",
    "vite.config.ts",
    "package.json",
    "tsconfig.json"
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
    confirm = input("\n是否生成requirements.txt？(y/N，直接回车不生成): ").strip().lower()
    if confirm not in ['y', 'Y']:
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


def _resolve_yarn_cmd(front_src_path: Path) -> str | None:
    """查找可用的 yarn 可执行文件路径。"""
    if shutil.which("yarn"):
        return "yarn"
    # Windows 下常见路径：项目本地 node_modules/.bin/yarn.cmd
    candidates = [
        front_src_path / "node_modules" / ".bin" / "yarn.cmd",
        front_src_path / "node_modules" / ".bin" / "yarn",
        front_src_path / "node_modules" / ".bin" / "yarn.ps1",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def build_frontend_static():
    """询问用户是否执行前端 `yarn build:prod` 生成最新静态文件。

    输入 y / Y / 1 才会执行；直接回车或其它字符都不生成，使用现有 dist。
    """
    print_separator()
    print("          前端静态文件生成（yarn build:prod）")
    print_separator()
    confirm = input(
        "\n是否执行前端 yarn build:prod 生成最新静态文件？\n"
        "（输入 y / Y / 1 执行；直接回车或其它字符跳过，使用现有 dist）: "
    ).strip()
    if confirm not in ("y", "Y", "1"):
        print("[跳过] 不生成前端静态文件，将使用现有的 dist 目录。")
        return False

    front_src_path = Path(FRONT_SRC)
    if not front_src_path.exists():
        print(f"[错误] 前端源目录不存在: {front_src_path}")
        return False

    yarn_cmd = _resolve_yarn_cmd(front_src_path)
    if yarn_cmd is None:
        print("[错误] 未找到 yarn 命令，请先安装（npm install -g yarn）或在项目 node_modules 中放置。")
        return False

    print(f"\n[执行] 工作目录: {front_src_path}")
    print(f"[执行] 命令: {yarn_cmd} build:prod")
    try:
        # 不加 check=True 让我们能拿到 returncode 自行判断
        result = subprocess.run(
            [yarn_cmd, "build:prod"],
            cwd=str(front_src_path),
            check=False,
        )
        if result.returncode != 0:
            print(f"[错误] yarn build:prod 执行失败，退出码: {result.returncode}")
            return False

        dist_path = front_src_path / "dist"
        if not dist_path.exists():
            print(f"[错误] 预期生成 dist 目录但未找到: {dist_path}")
            return False
        print(f"[成功] 前端静态文件已生成: {dist_path}")
        return True
    except FileNotFoundError as e:
        print(f"[错误] 启动 yarn 失败: {e}")
        return False
    except Exception as e:
        print(f"[错误] 执行 yarn build:prod 失败: {e}")
        return False

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
            # 清空目标文件夹（避免旧文件残留）
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
            # 递归复制文件夹，保留所有子文件/子目录，支持排除规则
            shutil.copytree(
                src,
                dest,
                ignore=shutil.ignore_patterns(*exclude_patterns),
                dirs_exist_ok=True
            )
            print(f"[复制成功] 文件夹: {src} -> {dest}")
            # 清理冗余文件
            clean_redundant_files(dest, exclude_patterns)
            return True
        else:
            print(f"[跳过] 文件夹不存在: {src}")
            return False
    except Exception as e:
        print(f"[复制失败] 文件夹 {src.name}: {str(e)[:100]}")  # 截断错误信息，更整洁
        return False

def clean_redundant_files(dir_path: Path, exclude_patterns: list = None):
    """清理冗余文件（__pycache__、.pyc等）"""
    if exclude_patterns is None:
        exclude_patterns = []
    if not dir_path.exists():
        return

    try:
        # 清理__pycache__文件夹
        for cache_dir in dir_path.rglob("__pycache__"):
            if cache_dir.is_dir():
                shutil.rmtree(cache_dir, ignore_errors=True)
        # 清理指定后缀的冗余文件
        for ext in ["*.pyc", "*.pyo", "*.pyd", "*.log", "*.tmp", "*.swp"]:
            if ext not in exclude_patterns:
                for file in dir_path.rglob(ext):
                    if file.is_file():
                        file.unlink(missing_ok=True)
        print(f"[清理完成] 冗余文件: {dir_path.name}")
    except Exception as e:
        print(f"[清理失败] {dir_path.name}: {str(e)[:80]}")


# 【修复/核心】单独复制assets下的TemplateImg目录（含所有图片/子文件）
def copy_assets_template_img():
    """单独复制后端assets/TemplateImg目录，确保所有图片文件被复制"""
    # 源路径：后端assets/TemplateImg（精准到具体目录）
    src_template = Path(BACK_SRC) / "assets" / BACKEND_ASSETS_COPY
    # 目标路径：迁移包后端/assets/TemplateImg（保持原目录结构）
    dest_template = Path(BACK_DEPLOY) / "assets" / BACKEND_ASSETS_COPY

    if not src_template.exists():
        print(f"[警告] TemplateImg目录不存在: {src_template}")
        return False
    # 复制TemplateImg目录（无排除规则，保留所有文件：图片、文件夹、子文件等）
    return copy_folder(src_template, dest_template, [])  # 空排除规则=复制所有内容

def copy_analysis_code():
    """复制前端Vue、后端Python-Flask关键分析代码到桌面"""
    print_separator()
    print("          开始复制OA关键分析代码到桌面")
    print_separator()

    # 初始化目标目录
    clean_directory(ANALYSIS_CODE_ROOT)
    back_analysis_dir = ANALYSIS_CODE_ROOT / "后端Flask代码"
    front_analysis_dir = ANALYSIS_CODE_ROOT / "前端Vue代码"
    back_analysis_dir.mkdir(parents=True, exist_ok=True)
    front_analysis_dir.mkdir(parents=True, exist_ok=True)

    # 复制后端关键代码
    print("\n[复制后端关键分析代码]")
    back_src_path = Path(BACK_SRC)
    for item in BACKEND_ANALYSIS_FILES:
        src_item = back_src_path / item
        dest_item = back_analysis_dir / item
        if src_item.is_file():
            copy_file(src_item, dest_item)
        elif src_item.is_dir():
            copy_folder(src_item, dest_item, BACKEND_EXCLUDE_PATTERNS)

    # 复制前端关键代码
    print("\n[复制前端关键分析代码]")
    front_src_path = Path(FRONT_SRC)
    for item in FRONTEND_ANALYSIS_FILES:
        src_item = front_src_path / item
        dest_item = front_analysis_dir / item
        if src_item.is_file():
            copy_file(src_item, dest_item)
        elif src_item.is_dir():
            copy_folder(src_item, dest_item, FRONTEND_EXCLUDE_PATTERNS)

    print(f"\n[成功] 关键分析代码已复制到: {ANALYSIS_CODE_ROOT}")
    print(f"  - 后端Flask代码: {back_analysis_dir}")
    print(f"  - 前端Vue代码: {front_analysis_dir}")

def full_deploy_sync():
    """完整的迁移包同步功能（原脚本核心逻辑）"""
    # 1. 生成最新requirements.txt（可选）
    generate_requirements_txt()

    # 1.5 询问是否执行前端 yarn build:prod 生成最新静态文件
    #     输入 y / Y / 1 才会执行；直接回车或其它字符不生成
    build_frontend_static()

    # 2. 前置检查
    print_separator()
    print("开始同步迁移文件...")
    print(f"后端源目录: {BACK_SRC}")
    print(f"前端源目录: {FRONT_SRC}")
    print(f"迁移包目录: {DEPLOY_ROOT}")
    print_separator()

    # 检查核心目录是否存在
    if not Path(BACK_SRC).exists():
        print(f"[错误] 后端源目录不存在: {BACK_SRC}")
        input("按回车键退出...")
        sys.exit(1)
    if not Path(FRONT_SRC).exists():
        print(f"[警告] 前端源目录不存在: {FRONT_SRC}")

    # 3. 清空并重建迁移目录（确保干净）
    clean_directory(DEPLOY_ROOT)
    clean_directory(BACK_DEPLOY)
    clean_directory(FRONT_DEPLOY)

    # 4. 复制脚本同级的启动文件到迁移包根目录
    print("\n" + "=" * 30)
    print("复制启动文件到迁移包根目录")
    print("=" * 30)
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    for filename in SCRIPT_ROOT_FILES:
        copy_file(script_dir / filename, DEPLOY_ROOT / filename)

    # 5. 复制后端根目录核心文件
    print("\n" + "=" * 30)
    print("复制后端根目录核心文件")
    print("=" * 30)
    back_src_path = Path(BACK_SRC)

    for filename in BACKEND_ROOT_FILES:
        copy_file(back_src_path / filename, BACK_DEPLOY / filename)

    # 6. 复制后端子文件夹（应用排除规则，含整体排除assets）
    print("\n" + "=" * 30)
    print("复制后端子文件夹")
    print("=" * 30)
    for folder_name in BACKEND_FOLDERS:
        copy_folder(back_src_path / folder_name, BACK_DEPLOY / folder_name, BACKEND_EXCLUDE_PATTERNS)

    # 7. 【核心修复】单独复制assets/TemplateImg目录（含所有图片文件）
    print("\n" + "=" * 30)
    print("复制后端assets/TemplateImg（含所有图片）")
    print("=" * 30)
    copy_assets_template_img()

    # 8. 复制额外部署文件（OA根目录下的说明/启动文件）
    print("\n" + "=" * 30)
    print("复制额外部署文件")
    print("=" * 30)
    base_dir_path = Path(BASE_DIR)
    for filename in EXTRA_DEPLOY_FILES:
        copy_file(base_dir_path / filename, DEPLOY_ROOT / filename)

    # 9. 复制前端dist目录（保留前端assets，不排除）
    print("\n" + "=" * 30)
    print("复制前端dist目录（保留assets）")
    print("=" * 30)
    front_dist_src = Path(FRONT_SRC) / "dist"
    if front_dist_src.exists():
        copy_folder(front_dist_src, FRONT_DEPLOY, FRONTEND_EXCLUDE_PATTERNS)
    else:
        print(f"[警告] 前端dist目录不存在: {front_dist_src}")

    # 10. 最终全局清理冗余文件
    print("\n" + "=" * 30)
    print("最终清理所有冗余文件")
    print("=" * 30)
    clean_redundant_files(BACK_DEPLOY, BACKEND_EXCLUDE_PATTERNS)
    clean_redundant_files(FRONT_DEPLOY, FRONTEND_EXCLUDE_PATTERNS)

    # 完成提示（含TemplateImg路径核对）
    print_separator()
    print("[成功] 迁移文件同步完成！✅")
    print(f"迁移包根目录: {DEPLOY_ROOT}")
    print(f"后端文件目录: {BACK_DEPLOY}")
    print(f"前端文件目录: {FRONT_DEPLOY}")
    print(f"启动文件位置: {DEPLOY_ROOT} (run_server.py、启动服务器.bat)")
    print(f"📷 图片目录已复制: {BACK_DEPLOY}/assets/{BACKEND_ASSETS_COPY}")
    print_separator()

def show_menu():
    """显示功能菜单"""
    print_separator()
    print("          OA系统文件处理脚本 - 功能菜单")
    print_separator()
    print("请选择要执行的功能（输入对应编号）：")
    print("1 - 完整迁移包同步（原脚本所有功能）")
    print("2 - 仅复制前端Vue+后端Flask关键分析代码到桌面")
    print("0 - 退出脚本")
    print_separator()

def main():
    """主执行函数（带菜单选择）"""
    # 设置控制台编码为UTF-8（解决中文乱码）
    if sys.platform == "win32":
        os.system("chcp 65001 > nul")
        sys.stdout.reconfigure(encoding='utf-8')  # 修复Python3.9+ stdout编码

    while True:
        show_menu()
        try:
            choice = input("请输入功能编号（直接回车=完整迁移包）: ").strip()
            if choice == "":
                choice = "1"
            if choice == "0":
                print("\n[退出] 脚本已退出，感谢使用！")
                break
            elif choice == "1":
                print("\n[执行] 开始执行完整迁移包同步功能...")
                full_deploy_sync()
                input("\n功能执行完成，按回车键返回菜单...")
            elif choice == "2":
                print("\n[执行] 开始执行复制关键分析代码功能...")
                copy_analysis_code()
                input("\n功能执行完成，按回车键返回菜单...")
            else:
                print("\n[错误] 无效的编号，请输入 0/1/2 中的一个！")
                input("按回车键重新选择...")
        except KeyboardInterrupt:
            print("\n\n[取消] 用户中断了操作 ❌")
            break
        except Exception as e:
            print(f"\n\n[致命错误] 脚本执行失败: {str(e)}")
            input("按回车键返回菜单...")

if __name__ == "__main__":
    main()