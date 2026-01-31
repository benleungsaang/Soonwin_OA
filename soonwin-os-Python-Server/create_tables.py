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
db_path = os.path.join('instance', 'oa_system.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查是否有Order表
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [table[0] for table in cursor.fetchall()]
print('数据库中的表:', tables)

conn.close()