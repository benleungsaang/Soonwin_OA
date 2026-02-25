import sqlite3
import os

# 检查数据库中是否有照片相关的操作日志
db_path = 'soonwin_oa.db'
if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查照片日志记录数
    cursor.execute('SELECT COUNT(*) FROM business_operation_log WHERE module="photo"')
    photo_count = cursor.fetchone()[0]
    print(f'照片日志记录数: {photo_count}')
    
    # 检查所有日志记录数，了解总体情况
    cursor.execute('SELECT COUNT(*) FROM business_operation_log')
    total_count = cursor.fetchone()[0]
    print(f'总日志记录数: {total_count}')
    
    # 检查不同模块的日志记录数
    cursor.execute('SELECT module, COUNT(*) FROM business_operation_log GROUP BY module')
    module_counts = cursor.fetchall()
    print('各模块日志记录数:')
    for module, count in module_counts:
        print(f'  {module}: {count}')
    
    # 如果有照片日志，显示前几条
    if photo_count > 0:
        cursor.execute('SELECT * FROM business_operation_log WHERE module="photo" LIMIT 5')
        records = cursor.fetchall()
        print('\n前5条照片日志:')
        for record in records:
            print(f'  {record}')
    
    conn.close()