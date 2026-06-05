"""
数据库结构同步工具
在重启服务前自动将生产库结构对齐开发库，保留生产库数据
"""
import sqlite3
import os
from datetime import datetime

# 系统表，结构比较和同步时跳过
_SYSTEM_TABLES = {
    'sqlite_sequence', 'sqlite_stat1', 'sqlite_stat2', 'sqlite_stat3', 'sqlite_stat4',
    'alembic_version', '_migration_history', '_migrate_history',
}


def backup_prod_db(prod_db_path):
    """备份生产数据库，文件名加日期前缀"""
    dir_name = os.path.dirname(prod_db_path)
    base_name = os.path.basename(prod_db_path)
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    name_without_ext, ext = os.path.splitext(base_name)
    backup_name = f"{name_without_ext}_{date_str}{ext}"
    backup_path = os.path.join(dir_name, backup_name)

    src = sqlite3.connect(prod_db_path)
    dst = sqlite3.connect(backup_path)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()

    print(f"[DB Sync] 数据库已备份: {backup_path}")
    return backup_path


def _get_create_sqls(conn):
    """获取数据库中所有用户表（排除系统表）的 CREATE TABLE SQL"""
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    tables = {}
    for name, sql in cursor.fetchall():
        if name in _SYSTEM_TABLES:
            continue
        if sql:
            # normalize: 去除多余的空白以便比较
            normalized = ' '.join(sql.split())
            tables[name] = normalized
    return tables


def compare_db_schemas(dev_db_path, prod_db_path):
    """比较 dev 和 prod 的库结构是否一致，返回 (is_same, diff_info)"""
    dev_conn = sqlite3.connect(dev_db_path)
    prod_conn = sqlite3.connect(prod_db_path)
    try:
        dev_tables = _get_create_sqls(dev_conn)
        prod_tables = _get_create_sqls(prod_conn)

        diffs = []

        # 检查 dev 有但 prod 没有的新表
        new_tables = set(dev_tables.keys()) - set(prod_tables.keys())
        for t in new_tables:
            diffs.append(f"[新增表] {t}")

        # 检查结构不同的表
        common = set(dev_tables.keys()) & set(prod_tables.keys())
        for t in sorted(common):
            if dev_tables[t] != prod_tables[t]:
                diffs.append(f"[结构变化] {t}")

        is_same = len(diffs) == 0
        return is_same, diffs
    finally:
        dev_conn.close()
        prod_conn.close()


def sync_prod_structure(dev_db_path, prod_db_path):
    """以 dev 库结构为准，更新 prod 库结构（保留 prod 数据）"""
    # 步骤1：检查结构是否一致
    is_same, diffs = compare_db_schemas(dev_db_path, prod_db_path)
    if is_same:
        print("[DB Sync] 库结构一致，无需同步")
        return True

    print(f"[DB Sync] 检测到结构差异 ({len(diffs)} 项):")
    for d in diffs:
        print(f"  {d}")

    # 步骤2：备份生产库
    try:
        backup_path = backup_prod_db(prod_db_path)
    except Exception as e:
        print(f"[DB Sync] 备份失败: {e}")
        return False

    # 步骤3：执行结构同步
    dev_conn = sqlite3.connect(dev_db_path)
    prod_conn = sqlite3.connect(prod_db_path)
    try:
        _do_sync(dev_conn, prod_conn)
        prod_conn.commit()
        print("[DB Sync] 结构同步完成")
        return True
    except Exception as e:
        prod_conn.rollback()
        print(f"[DB Sync] 结构同步失败: {e}")
        print(f"[DB Sync] 备份文件: {backup_path}，可用于手动恢复")
        return False
    finally:
        dev_conn.close()
        prod_conn.close()


def _do_sync(dev_conn, prod_conn):
    """执行实际的数据库结构同步"""
    cursor = prod_conn.cursor()

    dev_cursor = dev_conn.cursor()
    dev_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    dev_table_sql = {}
    for name, sql in dev_cursor.fetchall():
        if name not in _SYSTEM_TABLES and sql:
            dev_table_sql[name] = sql

    prod_cursor = prod_conn.cursor()
    prod_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    prod_table_sql = {}
    for name, sql in prod_cursor.fetchall():
        if name not in _SYSTEM_TABLES and sql:
            prod_table_sql[name] = ' '.join(sql.split())

    # 先建新表（dev 有但 prod 没有的）
    new_tables = set(dev_table_sql.keys()) - set(prod_table_sql.keys())
    for table_name in sorted(new_tables):
        print(f"[DB Sync] 创建新表: {table_name}")
        cursor.execute(dev_table_sql[table_name])

    # 重建结构变化的已有表
    for table_name in set(dev_table_sql.keys()) & set(prod_table_sql.keys()):
        new_sql = ' '.join(dev_table_sql[table_name].split())
        old_sql = prod_table_sql[table_name]

        if new_sql == old_sql:
            continue

        print(f"[DB Sync] 重建表结构: {table_name}")

        # 读出旧表全量数据
        try:
            prod_cursor.execute(f"SELECT * FROM [{table_name}]")
            old_rows = prod_cursor.fetchall()
            col_names = [d[0] for d in prod_cursor.description]
        except Exception:
            old_rows = []
            col_names = []

        # 读取 dev 表结构（列信息）
        dev_cursor.execute(f"PRAGMA table_info([{table_name}])")
        dev_cols = [row[1] for row in dev_cursor.fetchall()]
        # 新表和旧表的列交集
        compatible = [c for c in dev_cols if c in col_names]

        # 重命名旧表 → 创建新表 → 迁移数据 → 删除旧表
        temp_name = f"{table_name}_sync_temp"
        cursor.execute(f"ALTER TABLE [{table_name}] RENAME TO [{temp_name}]")
        cursor.execute(dev_table_sql[table_name])

        if old_rows and compatible:
            placeholders = ','.join(['?' for _ in compatible])
            insert_sql = f"INSERT INTO [{table_name}] ({','.join(compatible)}) VALUES ({placeholders})"
            col_indices = [col_names.index(c) for c in compatible]
            for row in old_rows:
                try:
                    cursor.execute(insert_sql, [row[i] for i in col_indices])
                except sqlite3.Error:
                    pass

        cursor.execute(f"DROP TABLE [{temp_name}]")

    # 同步索引：确保 dev 库中的索引都存在于 prod
    dev_cursor.execute("SELECT name, sql, tbl_name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
    prod_cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    existing_indexes = {row[0] for row in prod_cursor.fetchall()}

    for idx_name, idx_sql, tbl_name in dev_cursor.fetchall():
        if tbl_name in _SYSTEM_TABLES:
            continue
        if idx_name not in existing_indexes:
            try:
                cursor.execute(idx_sql)
            except sqlite3.OperationalError:
                pass
