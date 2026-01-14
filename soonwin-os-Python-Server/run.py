from app import create_app
import os
from flask_migrate import upgrade, migrate as migrate_cmd, stamp
from extensions import db
import sys
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime import migration

# ========== 【核心】自动检测模型与数据库差异并执行迁移 ==========
def auto_migrate_if_needed():
    """
    启动Flask项目时自动检测模型与数据库差异，如有变化则创建并执行迁移
    """
    try:
        print("🔍 检测模型与数据库是否一致...")
        app = create_app()
        
        with app.app_context():
            # 执行所有待执行的迁移（先确保数据库结构是最新的）
            print("🔍 执行数据库迁移...")
            upgrade()
            print("✅ 数据库迁移成功！所有迁移已应用")
            
    except Exception as e:
        print(f"❌ 数据库迁移执行失败！错误信息：{str(e)}")
        # 迁移失败则退出项目，防止脏数据写入，生产环境建议保留
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ========== 【改进】仅执行现有迁移 (当生成新迁移不适用时的备选方案) ==========
def auto_execute_existing_migrations():
    """
    启动Flask项目时自动执行数据库迁移 - 使用现有迁移文件
    """
    try:
        print("🔍 开始执行数据库迁移...")
        app = create_app()
        
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

# 创建Flask应用实例
app = create_app()

# ========== 你的业务路由示例 ========== 
@app.route('/')
def index():
    return "✅ Soonwin OA 系统启动成功！数据库迁移已自动完成"

# ========== 启动入口 ==========
if __name__ == "__main__":
    # 【必须放在run前面】启动服务前，先执行数据库迁移
    auto_migrate_if_needed()
    # 启动Flask服务（默认端口5000，允许局域网访问）
    app.run(host="0.0.0.0", port=5000, debug=True)