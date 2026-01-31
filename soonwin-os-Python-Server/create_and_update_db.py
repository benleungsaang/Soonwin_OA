import os
import sys
sys.path.append('.')

from app import create_app
from extensions import db

app = create_app()

# 创建所有数据库表
with app.app_context():
    db.create_all()
    print('已创建所有数据库表')

# 现在检查表是否已创建
import sqlite3
db_path = os.path.join('soonwin_oa.db')  # 按照配置文件中的默认数据库名
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查是否有Order表
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = [table[0] for table in cursor.fetchall()]
    print('数据库中的表:', tables)

    # 检查Order表的列
    if 'Order' in tables:
        cursor.execute('PRAGMA table_info("Order")')
        columns = [column[1] for column in cursor.fetchall()]
        print('Order表的列:', columns)

        # 如果不存在search_field列，则添加
        if 'search_field' not in columns:
            cursor.execute('ALTER TABLE "Order" ADD COLUMN search_field TEXT')
            conn.commit()
            print('已成功添加search_field列')
        else:
            print('search_field列已存在')

    conn.close()
else:
    print('数据库文件不存在:', db_path)