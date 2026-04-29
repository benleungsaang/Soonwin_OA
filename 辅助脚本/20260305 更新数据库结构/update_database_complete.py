"""
数据库结构完整更新脚本
将new.db的完整结构（包括所有字段属性、约束、索引等）更新应用到soonwin_oa.db
同时保留soonwin_oa.db中的原有数据
"""

import sqlite3
import os
import tempfile
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

def get_complete_db_schema(conn):
    """获取数据库的完整结构信息，包括表、字段、约束、索引等"""
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    schema = {}
    
    for table in tables:
        # 获取表的创建SQL
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
        table_sql = cursor.fetchone()
        table_create_sql = table_sql[0] if table_sql else None
        
        # 获取列信息
        cursor.execute(f"PRAGMA table_info([{table}]);")
        columns = cursor.fetchall()
        column_info = []
        for col in columns:
            column_info.append({
                'cid': col[0],           # 列ID
                'name': col[1],          # 列名
                'type': col[2],          # 数据类型
                'notnull': bool(col[3]), # 是否非空
                'dflt_value': col[4],    # 默认值
                'pk': bool(col[5])       # 是否主键
            })
        
        # 获取表的索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?", (table,))
        indexes = [idx[0] for idx in cursor.fetchall()]
        
        index_info = {}
        for index in indexes:
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name=?", (index,))
            index_sql = cursor.fetchone()
            if index_sql and index_sql[0]:
                index_info[index] = index_sql[0]
        
        schema[table] = {
            'create_sql': table_create_sql,
            'columns': column_info,
            'indexes': index_info
        }
    
    return schema

def get_table_data(conn, table_name):
    """获取表的数据"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        return rows, column_names
    except:
        return [], []

def get_compatible_columns(source_columns, target_columns):
    """获取源表和目标表中列名兼容的部分（用于数据迁移）"""
    source_col_names = {col['name'] for col in source_columns}
    target_col_names = {col['name'] for col in target_columns}
    compatible_cols = source_col_names & target_col_names
    return list(compatible_cols)

def update_database_structure_complete(dev_db_path, prod_db_path):
    """完整更新生产数据库的结构以匹配开发数据库"""
    print("开始完整更新数据库结构...")
    
    # 打开源数据库和目标数据库
    dev_conn = sqlite3.connect(dev_db_path)
    prod_conn = sqlite3.connect(prod_db_path)
    
    dev_schema = get_complete_db_schema(dev_conn)
    prod_schema = get_complete_db_schema(prod_conn)
    
    # 获取目标数据库中各表的数据
    table_data = {}
    for table in prod_schema.keys():
        if table not in ['sqlite_sequence', 'sqlite_stat1', 'sqlite_stat2', 'sqlite_stat3', 'sqlite_stat4', 
                         'alembic_version', '_migration_history', '_migrate_history']:
            table_data[table], _ = get_table_data(prod_conn, table)
    
    cursor = prod_conn.cursor()
    
    # 1. 删除不需要的旧表（新数据库中不存在的表）
    tables_to_drop = set(prod_schema.keys()) - set(dev_schema.keys())
    tables_to_drop = tables_to_drop - {'sqlite_sequence', 'sqlite_stat1', 'sqlite_stat2', 'sqlite_stat3', 'sqlite_stat4',
                                        'alembic_version', '_migration_history', '_migrate_history'}
    if tables_to_drop:
        print(f"⚠️  以下表将在旧数据库中删除（这些表在新数据库中不存在）:")
        for table in tables_to_drop:
            print(f"    - {table}")
        confirm = input("确认删除这些表吗？(y/N): ").strip().lower()
        if confirm in ['n', 'N']:
            print("[v] 用户取消删除操作，脚本退出")
            return
        for table in tables_to_drop:
            print(f"删除表: {table}")
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
    else:
        print("[v] 没有需要删除的表")
    
    # 2. 重建需要更新结构的表（使用新结构但保留数据）
    for table in set(dev_schema.keys()) & set(prod_schema.keys()):
        if table in ['sqlite_sequence', 'sqlite_stat1', 'sqlite_stat2', 'sqlite_stat3', 'sqlite_stat4', 
                     'alembic_version', '_migration_history', '_migrate_history']:
            continue
            
        # 获取新旧表的创建SQL
        old_create_sql = prod_schema[table]['create_sql']
        new_create_sql = dev_schema[table]['create_sql']
        
        # 如果表结构不同，则需要重建表
        if old_create_sql != new_create_sql:
            print(f"重建表结构: {table}")
            
            # 获取旧表数据
            old_data, old_columns = get_table_data(prod_conn, table)
            
            # 临时重命名旧表
            temp_table_name = f"{table}_temp_for_update"
            cursor.execute(f"ALTER TABLE {table} RENAME TO {temp_table_name}")
            
            # 创建新结构的表
            cursor.execute(new_create_sql)
            
            # 确定可兼容的列
            old_col_names = {col['name'] for col in prod_schema[table]['columns']}
            new_col_names = {col['name'] for col in dev_schema[table]['columns']}
            compatible_cols = old_col_names & new_col_names
            
            # 将兼容的数据迁移到新表
            if old_data and compatible_cols:
                compatible_cols_list = list(compatible_cols)
                old_col_indices = {i: col['name'] for i, col in enumerate(prod_schema[table]['columns']) 
                                   if col['name'] in compatible_cols}
                new_col_indices = {col['name']: i for i, col in enumerate(dev_schema[table]['columns']) 
                                   if col['name'] in compatible_cols}
                
                # 构建插入语句
                placeholders = ','.join(['?' for _ in compatible_cols_list])
                new_col_names_for_insert = [col['name'] for col in dev_schema[table]['columns'] 
                                            if col['name'] in compatible_cols]
                
                insert_sql = f"INSERT INTO {table} ({','.join(new_col_names_for_insert)}) VALUES ({placeholders})"
                
                # 从旧数据中选择兼容列的数据并插入新表
                for row in old_data:
                    compatible_row = []
                    for i, value in enumerate(row):
                        if i in old_col_indices and old_col_indices[i] in new_col_indices:
                            compatible_row.append(value)
                        else:
                            # 如果新表中没有对应的列，则跳过这个值
                            continue
                    
                    if len(compatible_row) == len(new_col_names_for_insert):
                        try:
                            cursor.execute(insert_sql, compatible_row)
                        except sqlite3.Error as e:
                            print(f"  插入数据到 {table} 时出错: {e}")
            
            # 删除临时表
            cursor.execute(f"DROP TABLE {temp_table_name}")
        else:
            print(f"表结构相同，跳过: {table}")
    
    # 3. 创建新表（新数据库中存在但旧数据库中不存在的表）
    new_tables = set(dev_schema.keys()) - set(prod_schema.keys())
    for table in new_tables:
        if table in ['sqlite_sequence', 'sqlite_stat1', 'sqlite_stat2', 'sqlite_stat3', 'sqlite_stat4', 
                     'alembic_version', '_migration_history', '_migrate_history']:
            continue
            
        print(f"创建新表: {table}")
        create_sql = dev_schema[table]['create_sql']
        if create_sql:
            cursor.execute(create_sql)
    
    # 4. 创建索引
    # 首先删除旧的索引（如果新结构中没有）
    for table_name, table_info in prod_schema.items():
        if table_name in dev_schema:
            old_indexes = set(table_info['indexes'].keys())
            new_indexes = set(dev_schema[table_name]['indexes'].keys())
            
            # 删除不再需要的索引
            indexes_to_drop = old_indexes - new_indexes
            for index in indexes_to_drop:
                print(f"删除索引: {index}")
                cursor.execute(f"DROP INDEX IF EXISTS {index}")
            
            # 添加新的或更新的索引
            for index, index_sql in dev_schema[table_name]['indexes'].items():
                if index not in table_info['indexes'] or table_info['indexes'][index] != index_sql:
                    print(f"创建/更新索引: {index}")
                    try:
                        cursor.execute(f"DROP INDEX IF EXISTS {index}")
                        cursor.execute(index_sql)
                    except sqlite3.OperationalError as e:
                        print(f"  创建索引 {index} 失败: {e}")
        else:
            # 表被删除了，删除该表的所有索引
            for index in table_info['indexes'].keys():
                print(f"删除已移除表的索引: {index}")
                cursor.execute(f"DROP INDEX IF EXISTS {index}")
    
    # 记录迁移操作
    migration_name = f"complete_structure_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
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
    
    print(f"数据库完整结构更新完成！")
    print(f"迁移记录: {migration_name}")

def main():
    new_db_path = "new.db"
    old_db_path = "old.db"
    target_db_path = "soonwin_oa.db"
    
    # 检查数据库文件是否存在
    if not os.path.exists(new_db_path):
        print(f"错误: 开发数据库文件 {new_db_path} 不存在")
        return
    
    if not os.path.exists(old_db_path):
        print(f"错误: 旧数据库文件 {old_db_path} 不存在")
        return
    
    # 复制 old.db 为 soonwin_oa.db
    print(f"正在复制 {old_db_path} 为 {target_db_path}...")
    old_conn = sqlite3.connect(old_db_path)
    target_conn = sqlite3.connect(target_db_path)
    
    old_conn.backup(target_conn)
    old_conn.close()
    target_conn.close()
    
    # 备份 soonwin_oa.db 数据库
    print("正在备份 soonwin_oa.db 数据库...")
    backup_path = backup_database(target_db_path)
    
    try:
        # 更新数据库结构
        update_database_structure_complete(new_db_path, target_db_path)
        print(f"\n数据库结构已成功从 {new_db_path} 完整更新到 {target_db_path}")
        print(f"原始数据库已备份到: {backup_path}")
    except Exception as e:
        print(f"更新数据库结构时发生错误: {e}")
        print("请检查错误并考虑从备份恢复数据库")

if __name__ == "__main__":
    main()
