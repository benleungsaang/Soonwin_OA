import sqlite3

def cleanup_invalid_progress_items():
    conn = sqlite3.connect('soonwin-os-Python-Server/soonwin_oa_dev.db')
    cursor = conn.cursor()

    print('检查错误的进度项数据...')

    # 查找所有错误关联的进度项（progress_id不是UUID格式，而是一个简单的数字字符串）
    # 首先查看当前所有的progress_id值
    cursor.execute('SELECT DISTINCT progress_id FROM progress_item ORDER BY progress_id;')
    all_progress_ids = cursor.fetchall()
    print(f'所有不同的progress_id值: {all_progress_ids}')

    # 查找那些可能是错误的进度项（长度较短，不是UUID格式）
    cursor.execute("SELECT id, progress_id, title FROM progress_item WHERE length(progress_id) <= 10 AND progress_id NOT LIKE '%-%';")
    short_progress_id_items = cursor.fetchall()
    print(f'\n疑似错误的进度项（短ID格式）: {len(short_progress_id_items)} 个')
    for item in short_progress_id_items:
        print(f'  项ID: {item[0]}, progress_id: {item[1]}, 标题: {item[2]}')

    # 现在检查所有实际的进度表ID，以确认哪些是无效的
    cursor.execute('SELECT id FROM order_progress;')
    valid_progress_ids = [row[0] for row in cursor.fetchall()]
    print(f'\n有效的进度表ID数量: {len(valid_progress_ids)}')

    # 查找无效的进度项（progress_id不在有效的进度表ID列表中）
    invalid_items = []
    cursor.execute('SELECT id, progress_id, title FROM progress_item;')
    all_items = cursor.fetchall()
    for item in all_items:
        item_id, progress_id, title = item
        if progress_id not in valid_progress_ids:
            invalid_items.append(item)

    print(f'\n无效的进度项数量: {len(invalid_items)}')
    for item in invalid_items:
        print(f'  项ID: {item[0]}, 无效progress_id: {item[1]}, 标题: {item[2]}')

    # 删除无效的进度项
    if invalid_items:
        print(f'\n准备删除 {len(invalid_items)} 个无效的进度项...')
        for item in invalid_items:
            cursor.execute('DELETE FROM progress_item WHERE id = ?', (item[0],))
        
        conn.commit()
        print('删除完成！')
    else:
        print('\n没有发现无效的进度项。')

    # 验证删除结果
    cursor.execute('SELECT COUNT(*) FROM progress_item;')
    remaining_count = cursor.fetchone()[0]
    print(f'\n删除后剩余的进度项数量: {remaining_count}')

    conn.close()

if __name__ == "__main__":
    cleanup_invalid_progress_items()