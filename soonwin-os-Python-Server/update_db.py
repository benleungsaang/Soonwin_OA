from app import create_app
from extensions import db
from app.models.employee import Employee
import sqlite3
import os

# 创建应用上下文
app = create_app()

# 获取数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'soonwin_oa.db')

# 直接使用SQL更新数据库表结构
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 添加user_role列
    try:
        cursor.execute("ALTER TABLE Employee ADD COLUMN user_role TEXT DEFAULT 'user'")
        print("Added user_role column to Employee table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("user_role column already exists")
        else:
            print(f"Error adding user_role column: {e}")
    
    # 添加status列
    try:
        cursor.execute("ALTER TABLE Employee ADD COLUMN status TEXT DEFAULT 'pending_binding'")
        print("Added status column to Employee table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("status column already exists")
        else:
            print(f"Error adding status column: {e}")
    
    conn.commit()
    print("Database schema updated successfully")
    
except Exception as e:
    print(f"Error updating database: {e}")
    conn.rollback()
finally:
    conn.close()