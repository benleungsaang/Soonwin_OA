import sqlite3
import os

# 检查主数据库中Order表的search_field列
db_path = os.path.join('soonwin_oa.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查是否有订单数据
    cursor.execute('SELECT COUNT(*) FROM "Order"')
    order_count = cursor.fetchone()[0]
    print(f'✓ 主数据库中有 {order_count} 个订单')
    
    # 检查是否有订单已经设置了search_field
    cursor.execute('SELECT COUNT(*) FROM "Order" WHERE search_field IS NOT NULL')
    search_field_count = cursor.fetchone()[0]
    print(f'✓ 主数据库中有 {search_field_count} 个订单已设置search_field')
    
    # 查看一个订单的search_field示例
    if order_count > 0:
        cursor.execute('SELECT id, area, customer_name, contract_no, search_field FROM "Order" LIMIT 1')
        sample_order = cursor.fetchone()
        if sample_order:
            print(f'✓ 主数据库订单示例 - ID: {sample_order[0]}, Area: {sample_order[1]}, Customer: {sample_order[2]}, Contract: {sample_order[3]}')
            print(f'  Search Field: {sample_order[4]}')

    conn.close()
else:
    print('主数据库文件不存在:', db_path)