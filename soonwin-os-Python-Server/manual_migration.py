import sqlite3

def apply_migration_manually():
    """
    手动执行第004和005号迁移的内容
    """
    conn = sqlite3.connect('instance/oa_system.db')
    cursor = conn.cursor()

    print("开始手动应用数据库迁移...")

    # 应用004号迁移：删除display_mode并添加page_count字段
    try:
        # 检查DisplayFile表是否存在display_mode列
        cursor.execute("PRAGMA table_info(DisplayFile)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'display_mode' in columns:
            print("检测到display_mode列，需要迁移...")
            # 由于SQLite不直接支持删除列，需要使用临时表方法
            # 1. 创建新表结构（没有display_mode，有page_count）
            cursor.execute('''
                CREATE TABLE DisplayFile_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    upload_time TEXT,
                    page_count INTEGER,
                    create_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    update_time TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 2. 将原表数据复制到新表
            cursor.execute('''
                INSERT INTO DisplayFile_new (id, title, file_path, upload_time, create_time, update_time)
                SELECT id, title, file_path, upload_time, create_time, update_time
                FROM DisplayFile
            ''')
            
            # 3. 删除原表
            cursor.execute('DROP TABLE DisplayFile')
            
            # 4. 重命名新表为原表名
            cursor.execute('ALTER TABLE DisplayFile_new RENAME TO DisplayFile')
            
            print("004号迁移完成：删除display_mode，添加page_count")
        else:
            print("display_mode列不存在，跳过004号迁移")
        
        # 应用005号迁移：添加current_status和current_status_time字段到OrderInspection表
        # 检查OrderInspection表是否存在这些列
        cursor.execute("PRAGMA table_info(OrderInspection)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'current_status' not in columns:
            print("添加current_status列...")
            cursor.execute("ALTER TABLE OrderInspection ADD COLUMN current_status INTEGER DEFAULT 1")
        else:
            print("current_status列已存在")
        
        if 'current_status_time' not in columns:
            print("添加current_status_time列...")
            cursor.execute("ALTER TABLE OrderInspection ADD COLUMN current_status_time TEXT")
        else:
            print("current_status_time列已存在")
        
        # 创建OrderInspectionStatusLog表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='OrderInspectionStatusLog'")
        if not cursor.fetchall():
            print("创建OrderInspectionStatusLog表...")
            cursor.execute('''
                CREATE TABLE OrderInspectionStatusLog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inspection_id INTEGER NOT NULL,
                    status INTEGER NOT NULL,
                    status_time TEXT,
                    create_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (inspection_id) REFERENCES OrderInspection (id)
                )
            ''')
            print("OrderInspectionStatusLog表创建完成")
        else:
            print("OrderInspectionStatusLog表已存在")
        
        conn.commit()
        print("数据库迁移手动应用完成")
        
        # 验证表结构
        print("\n验证OrderInspection表结构:")
        cursor.execute("PRAGMA table_info(OrderInspection)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]}) - {col[5]}")
        
        print("\n验证DisplayFile表结构:")
        cursor.execute("PRAGMA table_info(DisplayFile)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]}) - {col[5]}")
        
        print("\n验证OrderInspectionStatusLog表结构:")
        cursor.execute("PRAGMA table_info(OrderInspectionStatusLog)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]}) - {col[5]}")
        
    except Exception as e:
        print(f"迁移过程中出现错误: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    apply_migration_manually()