"""
快速数据库迁移脚本
用于快速检查和修复数据库结构问题
"""

import sqlite3
import os
import sys
from datetime import datetime

def check_and_fix_database():
    """检查并修复数据库结构"""
    
    db_path = "soonwin_oa.db"
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在 - {db_path}")
        print("请确保在正确的目录下运行此脚本")
        return False
    
    print(f"正在检查数据库: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查Employee表
        cursor.execute("PRAGMA table_info(Employee);")
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        print(f"\nEmployee表当前列: {existing_columns}")
        
        # 定义需要的列
        required_columns = [
            ('last_login_time', 'DATETIME', '上次登录时间'),
            ('login_device', 'VARCHAR(100)', '登录设备')
        ]
        
        migrated = False
        
        for col_name, col_type, comment in required_columns:
            if col_name not in existing_columns:
                print(f"发现缺失列: {col_name} ({col_type}) - {comment}")
                
                try:
                    if col_type == 'DATETIME':
                        cursor.execute(f"ALTER TABLE Employee ADD COLUMN {col_name} DATETIME;")
                    else:
                        cursor.execute(f"ALTER TABLE Employee ADD COLUMN {col_name} {col_type};")
                    print(f"已添加列: {col_name}")
                    migrated = True
                except sqlite3.OperationalError as e:
                    print(f"添加列 {col_name} 失败: {e}")
                    return False
        
        if migrated:
            conn.commit()
            print(f"\n数据库迁移完成于 {datetime.now()}")
            
            # 重新检查结构
            cursor.execute("PRAGMA table_info(Employee);")
            columns = cursor.fetchall()
            print(f"\n更新后的Employee表列: {[col[1] for col in columns]}")
        else:
            print(f"\n数据库结构已是最新，无需迁移")
        
        return True
        
    except Exception as e:
        print(f"数据库操作错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    print("="*50)
    print("快速数据库迁移工具")
    print("="*50)
    
    success = check_and_fix_database()
    
    print("\n" + "="*50)
    if success:
        print("数据库结构检查和修复完成")
        print("现在前端应该可以正常获取数据了")
    else:
        print("数据库结构检查或修复失败")
    print("="*50)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())