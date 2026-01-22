import sqlite3

def update_db_structure_for_nullable_time_fields():
    """
    更新数据库结构，移除时间字段的默认值
    由于SQLite限制，我们将创建新的表，迁移数据，然后替换原表
    """
    conn = sqlite3.connect('instance/oa_system.db')
    cursor = conn.cursor()

    print("开始更新数据库结构以支持可空时间字段...")

    try:
        # 1. 创建新的OrderInspection表（复制现有结构，但移除current_status_time的默认值）
        # 首先获取现有表结构
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='OrderInspection'")
        old_table_sql = cursor.fetchone()[0]
        print("原表结构:", old_table_sql)

        # 2. 创建临时表结构，复制数据
        cursor.execute('''
            CREATE TABLE OrderInspection_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                inspection_status TEXT DEFAULT 'pending',
                inspection_progress INTEGER DEFAULT 0,
                total_items INTEGER DEFAULT 0,
                completed_items INTEGER DEFAULT 0,
                remarks TEXT,
                current_status INTEGER DEFAULT 1,
                current_status_time TEXT,  -- 移除默认值
                create_time TEXT DEFAULT CURRENT_TIMESTAMP,
                update_time TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 3. 将原表数据复制到新表
        cursor.execute('''
            INSERT INTO OrderInspection_new (id, order_id, inspection_status, inspection_progress, 
                                           total_items, completed_items, remarks, current_status, 
                                           current_status_time, create_time, update_time)
            SELECT id, order_id, inspection_status, inspection_progress, 
                   total_items, completed_items, remarks, current_status, 
                   current_status_time, create_time, update_time
            FROM OrderInspection
        ''')

        # 4. 删除原表
        cursor.execute('DROP TABLE OrderInspection')

        # 5. 重命名新表为原表名
        cursor.execute('ALTER TABLE OrderInspection_new RENAME TO OrderInspection')

        # 对OrderInspectionStatusLog表执行相同操作
        cursor.execute('''
            CREATE TABLE OrderInspectionStatusLog_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER NOT NULL,
                status INTEGER NOT NULL,
                status_time TEXT,  -- 移除默认值
                create_time TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 复制数据
        cursor.execute('''
            INSERT INTO OrderInspectionStatusLog_new (id, inspection_id, status, status_time, create_time)
            SELECT id, inspection_id, status, status_time, create_time
            FROM OrderInspectionStatusLog
        ''')

        # 删除原表并重命名
        cursor.execute('DROP TABLE OrderInspectionStatusLog')
        cursor.execute('ALTER TABLE OrderInspectionStatusLog_new RENAME TO OrderInspectionStatusLog')

        # 提交更改
        conn.commit()
        print("数据库结构更新完成")

        # 验证更新
        print("\n验证OrderInspection表结构:")
        cursor.execute("PRAGMA table_info(OrderInspection)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]}) - {col[4]} (not null: {col[3]})")

        print("\n验证OrderInspectionStatusLog表结构:")
        cursor.execute("PRAGMA table_info(OrderInspectionStatusLog)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]}) - {col[4]} (not null: {col[3]})")

    except Exception as e:
        print(f"更新数据库结构时出错: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_db_structure_for_nullable_time_fields()
