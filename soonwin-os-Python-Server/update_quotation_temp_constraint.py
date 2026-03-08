import sqlite3
import os

# 连接到数据库
db_path = "G:\\Soonwin_OA\\soonwin-os-Python-Server\\soonwin_oa_dev.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("正在修改 QuotationTemp 表结构...")

try:
    # 首先查看当前表的结构
    cursor.execute("PRAGMA table_info(QuotationTemp)")
    current_columns = cursor.fetchall()
    print("当前 QuotationTemp 表结构：")
    for col in current_columns:
        print(f"  {col}")

    # 获取当前表的所有索引
    cursor.execute("PRAGMA index_list(QuotationTemp)")
    indexes = cursor.fetchall()
    print("\n当前 QuotationTemp 表的索引：")
    for idx in indexes:
        print(f"  {idx}")
        
        # 获取索引详细信息
        cursor.execute(f"PRAGMA index_info('{idx[1]}')")
        idx_info = cursor.fetchall()
        print(f"    列信息: {idx_info}")

    # SQLite 不直接支持删除唯一约束，我们可以通过创建新表并复制数据来实现
    # 1. 重命名原表
    cursor.execute("ALTER TABLE QuotationTemp RENAME TO QuotationTemp_old")
    
    # 2. 创建新表（不包含 order_mark 的唯一约束）
    cursor.execute("""
    CREATE TABLE QuotationTemp (
        id INTEGER NOT NULL, 
        order_mark VARCHAR(100) NOT NULL, 
        machine_list TEXT, 
        temp_params TEXT, 
        total_amount NUMERIC(12, 2), 
        creator_id VARCHAR(20), 
        create_time DATETIME, 
        update_time DATETIME, 
        remark TEXT, 
        PRIMARY KEY (id), 
        FOREIGN KEY(creator_id) REFERENCES Employee (emp_id)
    )
    """)
    
    # 3. 复制数据
    cursor.execute("""
    INSERT INTO QuotationTemp (id, order_mark, machine_list, temp_params, total_amount, creator_id, create_time, update_time, remark)
    SELECT id, order_mark, machine_list, temp_params, total_amount, creator_id, create_time, update_time, remark
    FROM QuotationTemp_old
    """)
    
    # 4. 删除旧表
    cursor.execute("DROP TABLE QuotationTemp_old")
    
    print("\n表结构修改完成！")
    
    # 验证修改结果
    cursor.execute("PRAGMA table_info(QuotationTemp)")
    new_columns = cursor.fetchall()
    print("\n修改后的 QuotationTemp 表结构：")
    for col in new_columns:
        print(f"  {col}")

    conn.commit()
    print("\n数据库表结构已成功更新，order_mark 字段不再有唯一性约束。")
    
except sqlite3.OperationalError as e:
    print(f"SQL操作错误: {e}")
    
    # 如果重命名失败，可能是因为存在唯一性约束，尝试其他方法
    # 回滚操作
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='QuotationTemp_old'")
        if cursor.fetchone():
            cursor.execute("DROP TABLE QuotationTemp")
            cursor.execute("ALTER TABLE QuotationTemp_old RENAME TO QuotationTemp")
            print("已回滚到原始表结构")
    except:
        pass
    
except Exception as e:
    print(f"修改表结构时出错: {e}")
    conn.rollback()
    
finally:
    conn.close()
    print("数据库连接已关闭")