"""
数据库结构更新脚本
将soonwin_oa_dev.db的结构更新应用到soonwin_oa.db
"""

import sqlite3
import os
from datetime import datetime

def backup_database(source_db, backup_suffix="_backup_before_structure_update"):
    """备份数据库"""
    backup_path = source_db.replace(".db", backup_suffix + ".db")
    conn_source = sqlite3.connect(source_db)
    conn_backup = sqlite3.connect(backup_path)
    
    conn_source.backup(conn_backup)
    conn_source.close()
    conn_backup.close()
    
    print(f"数据库已备份到: {backup_path}")
    return backup_path

def get_db_schema(conn):
    """获取数据库的表结构"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    schema = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info([{table}]);")
        columns = cursor.fetchall()
        schema[table] = {
            'columns': [(col[1], col[2], bool(col[5])) for col in columns],  # name, type, is_pk
            'column_names': [col[1] for col in columns]
        }
    
    return schema

def update_database_structure(dev_db_path, prod_db_path):
    """更新生产数据库的结构以匹配开发数据库"""
    print("开始更新数据库结构...")
    
    # 打开源数据库和目标数据库
    dev_conn = sqlite3.connect(dev_db_path)
    prod_conn = sqlite3.connect(prod_db_path)
    
    dev_schema = get_db_schema(dev_conn)
    prod_schema = get_db_schema(prod_conn)
    
    # 检查新表
    new_tables = set(dev_schema.keys()) - set(prod_schema.keys())
    
    # 检查需要更新的表
    updated_tables = []
    for table in set(dev_schema.keys()) & set(prod_schema.keys()):
        if set(dev_schema[table]['column_names']) != set(prod_schema[table]['column_names']):
            updated_tables.append(table)
    
    print(f"发现 {len(new_tables)} 个新表: {list(new_tables)}")
    print(f"发现 {len(updated_tables)} 个需要更新的表: {updated_tables}")
    
    cursor = prod_conn.cursor()
    
    # 创建新的表
    for table in new_tables:
        print(f"创建表 {table}")
        # 获取表的创建SQL语句
        dev_cursor = dev_conn.cursor()
        dev_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
        create_sql = dev_cursor.fetchone()[0]
        
        # 执行创建表的SQL
        cursor.execute(create_sql)
        
        # 如果新表有数据，选择性复制数据（如果结构兼容）
        if table not in ['alembic_version', 'sqlite_sequence']:  # 跳过系统表
            try:
                # 从开发数据库复制数据
                dev_cursor.execute(f"SELECT * FROM {table};")
                rows = dev_cursor.fetchall()
                if rows:
                    # 构建插入语句
                    placeholders = ','.join(['?' for _ in dev_schema[table]['columns']])
                    insert_sql = f"INSERT INTO {table} ({','.join([col[0] for col in dev_schema[table]['columns']])}) VALUES ({placeholders})"
                    cursor.executemany(insert_sql, rows)
                    print(f"  复制 {len(rows)} 行数据到 {table} 表")
            except Exception as e:
                print(f"  复制数据到 {table} 表失败: {e}")
    
    # 更新现有表的结构
    for table in updated_tables:
        print(f"更新表 {table}")
        dev_columns = set(dev_schema[table]['column_names'])
        prod_columns = set(prod_schema[table]['column_names'])
        
        # 找到需要添加的列
        new_columns = dev_columns - prod_columns
        
        for col in new_columns:
            # 获取列信息
            dev_cursor = dev_conn.cursor()
            dev_cursor.execute(f"PRAGMA table_info([{table}]);")
            all_cols = dev_cursor.fetchall()
            col_info = [c for c in all_cols if c[1] == col][0]
            
            # 添加列
            col_name = col_info[1]
            col_type = col_info[2]
            col_notnull = 'NOT NULL' if col_info[3] and col_info[4] != 1 else ''  # 4 is 'dflt_value', 3 is 'notnull'
            
            alter_sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} {col_notnull}"
            try:
                cursor.execute(alter_sql)
                print(f"  添加列 {col_name} 到表 {table}")
            except sqlite3.OperationalError as e:
                print(f"  添加列 {col_name} 到表 {table} 失败: {e}")
    
    # 记录迁移操作
    migration_name = f"structure_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 检查是否存在_migrate_history表，如果不存在则创建
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_migration_history';")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE _migration_history (
                id INTEGER PRIMARY KEY,
                migration_name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    cursor.execute("INSERT INTO _migration_history (migration_name, applied_at) VALUES (?, ?)", 
                   (migration_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    # 提交更改并关闭连接
    prod_conn.commit()
    dev_conn.close()
    prod_conn.close()
    
    print(f"数据库结构更新完成！")
    print(f"迁移记录: {migration_name}")

def main():
    dev_db_path = "soonwin_oa_dev.db"
    prod_db_path = "soonwin_oa.db"
    
    # 检查数据库文件是否存在
    if not os.path.exists(dev_db_path):
        print(f"错误: 开发数据库文件 {dev_db_path} 不存在")
        return
    
    if not os.path.exists(prod_db_path):
        print(f"错误: 生产数据库文件 {prod_db_path} 不存在")
        return
    
    # 备份生产数据库
    print("正在备份生产数据库...")
    backup_path = backup_database(prod_db_path)
    
    try:
        # 更新数据库结构
        update_database_structure(dev_db_path, prod_db_path)
        print(f"\n数据库结构已成功从 {dev_db_path} 更新到 {prod_db_path}")
        print(f"原始数据库已备份到: {backup_path}")
    except Exception as e:
        print(f"更新数据库结构时发生错误: {e}")
        print("请检查错误并考虑从备份恢复数据库")

if __name__ == "__main__":
    main()
