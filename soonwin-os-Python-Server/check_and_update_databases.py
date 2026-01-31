import sqlite3
import os

# 检查开发数据库中Order表的search_field列
db_path = os.path.join('soonwin_oa_dev.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查Order表的列
    cursor.execute('PRAGMA table_info("Order")')
    columns = [column[1] for column in cursor.fetchall()]
    print('开发数据库Order表的列:', columns)

    # 检查search_field列是否存在
    if 'search_field' in columns:
        print('✓ search_field列已成功添加到开发数据库的Order表')
        
        # 检查是否有订单数据
        cursor.execute('SELECT COUNT(*) FROM "Order"')
        order_count = cursor.fetchone()[0]
        print(f'✓ 开发数据库中有 {order_count} 个订单')
        
        # 检查是否有订单已经设置了search_field
        cursor.execute('SELECT COUNT(*) FROM "Order" WHERE search_field IS NOT NULL')
        search_field_count = cursor.fetchone()[0]
        print(f'✓ 开发数据库中有 {search_field_count} 个订单已设置search_field')
        
        # 查看一个订单的search_field示例
        if order_count > 0:
            cursor.execute('SELECT id, area, customer_name, contract_no, search_field FROM "Order" LIMIT 1')
            sample_order = cursor.fetchone()
            if sample_order:
                print(f'✓ 订单示例 - ID: {sample_order[0]}, Area: {sample_order[1]}, Customer: {sample_order[2]}, Contract: {sample_order[3]}')
                print(f'  Search Field: {sample_order[4]}')
    else:
        print('✗ search_field列未添加到开发数据库的Order表')
        print('将为开发数据库添加search_field列...')
        
        # 添加search_field列到开发数据库
        cursor.execute('ALTER TABLE "Order" ADD COLUMN search_field TEXT')
        conn.commit()
        print('✓ 已成功添加search_field列到开发数据库')

    conn.close()
else:
    print('开发数据库文件不存在:', db_path)
    print('检查主数据库文件...')
    
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
            print('✗ search_field列未添加到主数据库的Order表')
            print('将为主数据库添加search_field列...')
            
            # 添加search_field列到主数据库
            cursor.execute('ALTER TABLE "Order" ADD COLUMN search_field TEXT')
            conn.commit()
            print('✓ 已成功添加search_field列到主数据库')

        conn.close()
    else:
        print('主数据库文件也不存在:', main_db_path)