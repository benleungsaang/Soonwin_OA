"""
数据库迁移脚本
用于在字段变更时更新数据库结构
"""

import sqlite3
import sys
import os

def check_and_update_employee_table(db_path):
    """检查并更新Employee表结构"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取当前Employee表的列信息
        cursor.execute("PRAGMA table_info(Employee);")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        print(f"当前Employee表的列: {existing_columns}")
        
        # 检查是否需要添加last_login_time列
        if 'last_login_time' not in existing_columns:
            print("正在添加last_login_time列...")
            cursor.execute("ALTER TABLE Employee ADD COLUMN last_login_time DATETIME;")
            print("last_login_time列添加成功")
        
        # 检查是否需要添加login_device列
        if 'login_device' not in existing_columns:
            print("正在添加login_device列...")
            cursor.execute("ALTER TABLE Employee ADD COLUMN login_device VARCHAR(100);")
            print("login_device列添加成功")
        
        # 可以在这里添加更多字段检查和更新逻辑
        
        conn.commit()
        print("Employee表结构更新完成")
        
    except Exception as e:
        print(f"更新Employee表时出错: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

def check_and_update_other_tables(db_path):
    """检查和更新其他表的结构（预留接口）"""
    # 在这里可以添加其他表的检查和更新逻辑
    pass

def main():
    # 设置数据库路径
    db_path = "soonwin_oa.db"  # 或者从环境变量或参数获取
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return 1
    
    print("开始检查数据库结构...")
    
    # 检查并更新Employee表
    if not check_and_update_employee_table(db_path):
        print("Employee表更新失败")
        return 1
    
    # 检查和更新其他表
    check_and_update_other_tables(db_path)
    
    print("数据库结构检查和更新完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())