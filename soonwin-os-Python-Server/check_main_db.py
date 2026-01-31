import sqlite3
import os

# 检查主数据库
main_db_path = os.path.join('soonwin_oa.db')
if os.path.exists(main_db_path):
    conn = sqlite3.connect(main_db_path)
    cursor = conn.cursor()

    # 检查Order表的列
    cursor.execute('PRAGMA table_info("Order")')
    columns = [column[1] for column in cursor.fetchall()]
    print('主数据库Order表的列:', columns)

    # 检查search_field列是否存在
    if 'search_field' in columns:
        print('✓ search_field列已成功添加到主数据库的Order表')
    else:
        print('将为主数据库添加search_field列...')
        
        # 添加search_field列到主数据库
        cursor.execute('ALTER TABLE "Order" ADD COLUMN search_field TEXT')
        conn.commit()
        print('✓ 已成功添加search_field列到主数据库')

    conn.close()
else:
    print('主数据库文件不存在:', main_db_path)