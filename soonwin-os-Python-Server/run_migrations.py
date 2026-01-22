from alembic.config import Config
from alembic import command

def run_migrations():
    # 创建Alembic配置
    alembic_cfg = Config("migrations/alembic.ini")
    alembic_cfg.set_main_option("script_location", "migrations")
    
    # 运行升级命令
    command.upgrade(alembic_cfg, "head")
    print("数据库迁移已完成")

if __name__ == "__main__":
    run_migrations()