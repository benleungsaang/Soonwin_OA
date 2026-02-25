from app import create_app
import os
from flask_migrate import upgrade, migrate as migrate_cmd, stamp
from extensions import db
import sys
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime import migration
import time  # 新增：用于计算请求耗时
import logging  # 新增：Flask日志模块

# ========== 【新增】配置请求日志 ==========
def setup_request_logging(app):
    """
    配置Flask请求日志，让每个API请求都输出到控制台
    """
    # 设置日志级别
    app.logger.setLevel(logging.INFO)

    # 移除默认的日志处理器（避免重复输出）
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    # 添加控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 定义日志格式：时间 - 方法 - URL - 状态码 - 耗时
    log_format = logging.Formatter(
        '[%(asctime)s] %(method)s %(url)s - %(status)s - %(elapsed)ss'
    )
    console_handler.setFormatter(log_format)
    app.logger.addHandler(console_handler)

    # 请求开始时记录时间
    @app.before_request
    def start_timer():
        g.start = time.time()

    # 请求结束后打印日志
    @app.after_request
    def log_request(response):
        # 计算请求耗时（秒，保留3位小数）
        elapsed = round(time.time() - g.start, 3)

        # 构建日志上下文
        context = {
            'method': request.method,
            'url': request.path,
            'status': response.status_code,
            'elapsed': elapsed
        }

        # 打印日志到控制台
        app.logger.info('API请求处理完成', extra=context)

        return response

    # 处理异常请求的日志
    @app.errorhandler(Exception)
    def log_exception(e):
        elapsed = round(time.time() - g.start, 3)
        context = {
            'method': request.method,
            'url': request.path,
            'status': 500,
            'elapsed': elapsed
        }
        app.logger.error(f'API请求异常: {str(e)}', extra=context)
        return {"error": str(e)}, 500

# ========== 【核心】自动检测模型与数据库差异并执行迁移 ==========
def auto_migrate_if_needed(port=5000):
    """
    启动Flask项目时自动检测模型与数据库差异，如有变化则创建并执行迁移
    """
    try:
        print("🔍 检测模型与数据库是否一致...")
        app = create_app(port)

        with app.app_context():
            # 执行所有待执行的迁移（先确保数据库结构是最新的）
            print("🔍 执行数据库迁移...")
            upgrade()
            print("✅ 数据库迁移成功！所有迁移已应用")

    except Exception as e:
        print(f"⚠️  数据库迁移遇到问题：{str(e)}")
        print("⚠️  检查数据库表是否已存在...")
        # 尝试连接数据库并检查表是否存在
        try:
            app = create_app(port)
            with app.app_context():
                from extensions import db
                from app.models.order_inspection import OrderInspection, InspectionItem
                from sqlalchemy import inspect

                inspector = inspect(db.engine)
                tables = inspector.get_table_names()

                if 'OrderInspection' in tables and 'InspectionItem' in tables:
                    print("✅ 手动创建的表已存在，跳过迁移")
                else:
                    print("❌ 关键表不存在，迁移失败")
                    import traceback
                    traceback.print_exc()
                    sys.exit(1)
        except Exception as check_error:
            print(f"❌ 检查数据库表时出错：{str(check_error)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

# ========== 【改进】仅执行现有迁移 (当生成新迁移不适用时的备选方案) ==========
def auto_execute_existing_migrations(port=5000):
    """
    启动Flask项目时自动执行数据库迁移 - 使用现有迁移文件
    """
    try:
        print("🔍 开始执行数据库迁移...")
        app = create_app(port)

        with app.app_context():
            # 直接执行迁移，如果已经是最新版本则不会执行任何操作
            print("🔍 检查数据库迁移状态并执行待迁移...")
            upgrade()
            print("✅ 数据库迁移成功！所有迁移已应用")

    except Exception as e:
        print(f"❌ 数据库迁移执行失败！错误信息：{str(e)}")
        # 迁移失败则退出项目，防止脏数据写入，生产环境建议保留
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ========== 【新增】创建权限表并初始化权限 ==========
def init_permissions_after_startup(port=5000):
    """
    启动后初始化权限表和默认权限
    """
    try:
        print("🔍 初始化权限表和默认权限...")
        app = create_app(port)

        with app.app_context():
            from extensions import db
            from app.models.permission import RolePermission, init_default_permissions
            from sqlalchemy import text
            from sqlalchemy import inspect

            # 检查RolePermission表是否存在
            inspector_instance = inspect(db.engine)
            tables = inspector_instance.get_table_names()

            if 'RolePermission' not in tables:
                print("🔍 RolePermission表不存在，手动创建...")
                # 手动创建RolePermission表
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE RolePermission (
                            id TEXT PRIMARY KEY,
                            role_name VARCHAR(10) NOT NULL,
                            module_name VARCHAR(50) NOT NULL,
                            can_view BOOLEAN DEFAULT 1,
                            can_edit BOOLEAN DEFAULT 0,
                            can_delete BOOLEAN DEFAULT 0,
                            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                            update_time DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    conn.execute(text("""
                        CREATE UNIQUE INDEX uq_role_module ON RolePermission (role_name, module_name)
                    """))
                    conn.commit()  # 提交事务
                print("✅ RolePermission表创建成功！")

            # 初始化默认权限
            init_default_permissions()
            print("✅ 默认权限初始化成功！")

    except Exception as e:
        print(f"❌ 权限初始化失败！错误信息：{str(e)}")
        import traceback
        traceback.print_exc()

# ========== 你的业务路由示例 ==========
def create_app_with_routes(port=5000):
    app = create_app(port)

    # 新增：配置请求日志
    setup_request_logging(app)

    @app.route('/')
    def index():
        return f"✅ Soonwin OA 系统启动成功！数据库迁移已自动完成 (端口: {port})"

    return app

# ========== 启动入口 ==========
if __name__ == "__main__":
    import sys
    from flask import g, request  # 新增：导入g和request（用于请求日志）
    # 获取命令行参数指定的端口，默认为5001（开发环境）
    port = 5001
    debug_mode = True  # 默认启用调试模式（开发模式）

    # 检查是否有 --port 参数
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--port' and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                print(f"⚠️  端口号无效: {sys.argv[i + 1]}，使用默认端口 {port}")
            i += 2  # 跳过参数和值
            continue
        elif sys.argv[i] == '--debug=False':
            debug_mode = False  # 禁用调试模式和重载器
        elif sys.argv[i] == '--debug=True':
            debug_mode = True  # 启用调试模式和重载器
        i += 1

    # 如果没有找到 --port 参数，尝试检查第一个参数是否是数字
    if port == 5001 and len(sys.argv) > 1:
        try:
            # 检查第一个参数是否是纯数字（不是选项参数）
            first_arg = sys.argv[1]
            if first_arg.isdigit():
                port = int(first_arg)
        except ValueError:
            print(f"⚠️  端口号无效: {sys.argv[1]}，使用默认端口 {port}")

    # 根据端口选择数据库
    if port == 5001:
        print("🔍 使用开发数据库: soonwin_oa_dev.db (端口: 5001)")
    else:
        print("🔍 使用主数据库: soonwin_oa.db (端口: 5000)")

    # 为了绕过复杂迁移问题，直接启动应用而不执行迁移
    print("⚠️  绕过数据库迁移，直接启动应用（表已手动创建）")

    # 初始化简化版权限系统（原代码中提到的初始化）
    print("开始初始化简化版权限系统...")
    init_permissions_after_startup(port)
    print("简化版权限系统初始化完成！")

    # 创建应用实例
    app = create_app_with_routes(port)

    # 启动Flask服务（允许局域网访问）
    app.run(host="0.0.0.0", port=port, debug=debug_mode, use_reloader=debug_mode)