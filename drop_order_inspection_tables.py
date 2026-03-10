import sqlite3
import os

# 连接到数据库
db_path = os.path.join("soonwin-os-Python-Server", "soonwin_oa_dev.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("开始删除order_inspection.py中定义的数据表...")

try:
    # 开始事务
    conn.execute("BEGIN TRANSACTION")

    # 检查表是否存在
    tables_to_drop = ['OrderInspection', 'OrderInspectionStatusLog', 'InspectionItem']
    
    for table_name in tables_to_drop:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            cursor.execute(f"DROP TABLE {table_name}")
            print(f"已删除 {table_name} 表")
        else:
            print(f"{table_name} 表不存在")

    # 提交事务
    conn.commit()
    print("数据表删除操作完成！")
    
except Exception as e:
    # 回滚事务
    conn.rollback()
    print(f"删除失败，已回滚: {e}")
    
finally:
    conn.close()
    print("数据库连接已关闭。")

# 验证删除结果
print("\n验证删除结果:")
conn_verify = sqlite3.connect(db_path)
cursor_verify = conn_verify.cursor()

cursor_verify.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = cursor_verify.fetchall()
print("当前数据库中的表:")
for table in all_tables:
    print(f"  - {table[0]}")

conn_verify.close()
print("验证完成。")