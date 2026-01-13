"""
数据库迁移管理脚本
使用方法：
1. python db_migrate.py check - 检查当前数据库状态
2. python db_migrate.py migrate - 执行数据库迁移
3. python db_migrate.py create_migration "migration message" - 创建新的迁移文件
"""

import sys
import os
import subprocess
from datetime import datetime
import sqlite3

def check_db_structure(db_path):
    """检查数据库表结构"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查Employee表结构
        cursor.execute("PRAGMA table_info(Employee);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("Employee表当前结构:")
        for i, col in enumerate(columns):
            print(f"  {i}: {col[1]} ({col[2]}) - NOT NULL: {col[3]}, PK: {col[5]}")
        
        # 检查必需的列
        required_columns = ['last_login_time', 'login_device']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"\n缺少的列: {missing_columns}")
            return False
        else:
            print(f"\nEmployee表结构完整")
            return True
            
    except Exception as e:
        print(f"检查数据库结构时出错: {e}")
        return False
    finally:
        conn.close()

def manual_migrate(db_path):
    """手动执行数据库迁移"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取当前列
        cursor.execute("PRAGMA table_info(Employee);")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # 添加缺失的列
        if 'last_login_time' not in existing_columns:
            print("添加 last_login_time 列...")
            cursor.execute("ALTER TABLE Employee ADD COLUMN last_login_time DATETIME;")
            print("✓ last_login_time 列已添加")
        
        if 'login_device' not in existing_columns:
            print("添加 login_device 列...")
            cursor.execute("ALTER TABLE Employee ADD COLUMN login_device VARCHAR(100);")
            print("✓ login_device 列已添加")
        
        conn.commit()
        print("\n数据库迁移完成!")
        return True
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_alembic_migration(message):
    """创建Alembic迁移文件"""
    try:
        # 检查alembic是否配置正确
        os.chdir(os.path.dirname(__file__))
        
        # 生成迁移文件
        cmd = [
            sys.executable, "-c",
            f"""
import sys
sys.path.insert(0, '.')
from app import create_app
from extensions import db
from flask_migrate import Migrate
from flask import Flask

app = create_app()
migrate = Migrate(app, db)

with app.app_context():
    from alembic import command
    command.revision(
        config=migrate.get_config(),
        message='{message}',
        autogenerate=True
    )
"""
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        
        if result.returncode == 0:
            print("迁移文件创建成功")
        else:
            print("创建迁移文件失败，使用手动方法")
        
    except Exception as e:
        print(f"创建迁移文件时出错: {e}")

def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python db_migrate.py check          - 检查数据库结构")
        print("  python db_migrate.py migrate        - 执行数据库迁移")
        print("  python db_migrate.py create <msg>   - 创建迁移文件")
        return
    
    command = sys.argv[1]
    db_path = "soonwin_oa.db"
    
    if command == "check":
        print("正在检查数据库结构...")
        check_db_structure(db_path)
        
    elif command == "migrate":
        print("正在执行数据库迁移...")
        if check_db_structure(db_path):
            print("数据库结构已经是最新版本")
        else:
            if manual_migrate(db_path):
                print("迁移完成，正在验证...")
                check_db_structure(db_path)
            else:
                print("迁移失败")
                
    elif command == "create":
        if len(sys.argv) < 3:
            print("请提供迁移消息")
            return
        message = " ".join(sys.argv[2:])
        print(f"创建迁移文件: {message}")
        create_alembic_migration(message)
        
    else:
        print(f"未知命令: {command}")
        print("使用方法:")
        print("  python db_migrate.py check          - 检查数据库结构")
        print("  python db_migrate.py migrate        - 执行数据库迁移")
        print("  python db_migrate.py create <msg>   - 创建迁移文件")

if __name__ == "__main__":
    main()
