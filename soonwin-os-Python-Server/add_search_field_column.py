import sqlite3
import os

# 确保实例目录存在
db_path = os.path.join('instance', 'oa_system.db')

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查是否存在search_field列
cursor.execute('PRAGMA table_info("Order")')
columns = [column[1] for column in cursor.fetchall()]
print('当前Order表的列:', columns)

# 如果不存在search_field列，则添加
if 'search_field' not in columns:
    cursor.execute('ALTER TABLE "Order" ADD COLUMN search_field TEXT')
    conn.commit()
    print('已成功添加search_field列')
else:
    print('search_field列已存在')

conn.close()