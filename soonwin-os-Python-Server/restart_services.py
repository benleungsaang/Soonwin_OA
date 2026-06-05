"""
独立重启服务脚本
由 Flask /api/admin/restart 路由以子进程方式调用，不受 Flask 进程新旧影响。
也可手动执行：python restart_services.py
"""
import sqlite3
import subprocess
import os
import sys
import time
from datetime import datetime

# ======================== 配置 ========================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEV_DB = os.path.join(SCRIPT_DIR, "soonwin_oa_dev.db")
PROD_DB = os.path.join(SCRIPT_DIR, "soonwin_oa.db")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "数据库备份文件")
SERVICES = ["waitress", "nginx"]

# 系统表，比较和同步时跳过
_SYSTEM_TABLES = {
    "sqlite_sequence", "sqlite_stat1", "sqlite_stat2",
    "sqlite_stat3", "sqlite_stat4", "alembic_version",
    "_migration_history", "_migrate_history",
}


# ======================== 服务控制 ========================
def stop_services():
    """依次停止所有服务"""
    for svc in SERVICES:
        print(f"[Restart] 停止服务: {svc} ...")
        try:
            r = subprocess.run(
                ["sc", "query", svc],
                capture_output=True, text=True, encoding="gbk", timeout=10,
            )
            if "1060" in (r.stdout or "") or "1060" in (r.stderr or ""):
                print(f"  {svc} 服务不存在，跳过")
                continue
            subprocess.run(
                ["sc", "stop", svc],
                capture_output=True, text=True, encoding="gbk", timeout=60,
            )
            # 等待服务完全停止
            for _ in range(30):
                r2 = subprocess.run(
                    ["sc", "query", svc],
                    capture_output=True, text=True, encoding="gbk", timeout=10,
                )
                if "STOPPED" in (r2.stdout or ""):
                    print(f"  {svc} 已停止")
                    break
                time.sleep(1)
        except Exception as e:
            print(f"  {svc} 停止异常: {e}")


def start_services():
    """依次启动所有服务"""
    for svc in SERVICES:
        print(f"[Restart] 启动服务: {svc} ...")
        try:
            subprocess.run(
                ["sc", "start", svc],
                capture_output=True, text=True, encoding="gbk", timeout=60,
            )
            print(f"  {svc} 启动完成")
        except Exception as e:
            print(f"  {svc} 启动异常: {e}")
        time.sleep(2)


# ======================== 数据库备份 ========================
def backup_databases():
    """备份 dev 和 prod 两个数据库到备份目录"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    paths = []
    for db_path in [DEV_DB, PROD_DB]:
        if not os.path.exists(db_path):
            print(f"  跳过（不存在）: {db_path}")
            continue
        base = os.path.basename(db_path)
        name, ext = os.path.splitext(base)
        backup_name = f"{name}_{date_str}{ext}"
        backup_path = os.path.join(BACKUP_DIR, backup_name)

        src = sqlite3.connect(db_path)
        dst = sqlite3.connect(backup_path)
        try:
            src.backup(dst)
        finally:
            src.close()
            dst.close()

        print(f"  备份: {backup_path}")
        paths.append(backup_path)

    return paths


# ======================== 数据库结构同步 ========================
def _get_create_sqls(conn):
    """获取所有用户表的 CREATE TABLE SQL"""
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    tables = {}
    for name, sql in cursor.fetchall():
        if name in _SYSTEM_TABLES or not sql:
            continue
        tables[name] = " ".join(sql.split())
    return tables


def compare_schemas(dev_db, prod_db):
    """比较结构，返回 (是否一致, 差异列表)"""
    dev_conn = sqlite3.connect(dev_db)
    prod_conn = sqlite3.connect(prod_db)
    try:
        dev_tables = _get_create_sqls(dev_conn)
        prod_tables = _get_create_sqls(prod_conn)
        diffs = []
        for t in set(dev_tables.keys()) - set(prod_tables.keys()):
            diffs.append(f"新增表: {t}")
        for t in sorted(set(dev_tables.keys()) & set(prod_tables.keys())):
            if dev_tables[t] != prod_tables[t]:
                diffs.append(f"结构变化: {t}")
        return len(diffs) == 0, diffs
    finally:
        dev_conn.close()
        prod_conn.close()


def sync_structure(dev_db, prod_db):
    """以 dev 结构为准，更新 prod 结构（保留 prod 数据）"""
    is_same, diffs = compare_schemas(dev_db, prod_db)
    if is_same:
        print("[DB Sync] 库结构一致，无需同步")
        return True

    print(f"[DB Sync] 检测到 {len(diffs)} 处结构差异:")
    for d in diffs:
        print(f"  - {d}")

    dev_conn = sqlite3.connect(dev_db)
    prod_conn = sqlite3.connect(prod_db)
    try:
        _do_sync(dev_conn, prod_conn)
        prod_conn.commit()
        print("[DB Sync] 结构同步完成")
        return True
    except Exception as e:
        prod_conn.rollback()
        print(f"[DB Sync] 同步失败: {e}")
        return False
    finally:
        dev_conn.close()
        prod_conn.close()


def _do_sync(dev_conn, prod_conn):
    """执行结构同步"""
    cursor = prod_conn.cursor()

    # 收集 dev 表信息
    dev_cursor = dev_conn.cursor()
    dev_cursor.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table'"
    )
    dev_tables = {}
    for name, sql in dev_cursor.fetchall():
        if name not in _SYSTEM_TABLES and sql:
            dev_tables[name] = sql

    # 收集 prod 表信息
    prod_cursor = prod_conn.cursor()
    prod_cursor.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table'"
    )
    prod_tables = {}
    for name, sql in prod_cursor.fetchall():
        if name not in _SYSTEM_TABLES and sql:
            prod_tables[name] = " ".join(sql.split())

    # 1) 新建 dev 有但 prod 没有的表
    for t in sorted(set(dev_tables.keys()) - set(prod_tables.keys())):
        print(f"[DB Sync] 创建新表: {t}")
        cursor.execute(dev_tables[t])

    # 2) 重建结构变化的表
    for t in set(dev_tables.keys()) & set(prod_tables.keys()):
        new_sql = " ".join(dev_tables[t].split())
        if new_sql == prod_tables[t]:
            continue
        print(f"[DB Sync] 重建表: {t}")

        try:
            prod_cursor.execute(f"SELECT * FROM [{t}]")
            old_rows = prod_cursor.fetchall()
            col_names = [d[0] for d in prod_cursor.description]
        except Exception:
            old_rows, col_names = [], []

        dev_cursor.execute(f"PRAGMA table_info([{t}])")
        dev_cols = [row[1] for row in dev_cursor.fetchall()]
        compatible = [c for c in dev_cols if c in col_names]

        temp = f"{t}_sync_temp"
        cursor.execute(f"ALTER TABLE [{t}] RENAME TO [{temp}]")
        cursor.execute(dev_tables[t])

        if old_rows and compatible:
            ph = ",".join(["?" for _ in compatible])
            ins = (
                f"INSERT INTO [{t}] ({','.join(compatible)}) VALUES ({ph})"
            )
            indices = [col_names.index(c) for c in compatible]
            for row in old_rows:
                try:
                    cursor.execute(ins, [row[i] for i in indices])
                except sqlite3.Error:
                    pass

        cursor.execute(f"DROP TABLE [{temp}]")

    # 3) 同步索引
    dev_cursor.execute(
        "SELECT name, sql, tbl_name FROM sqlite_master "
        "WHERE type='index' AND sql IS NOT NULL"
    )
    prod_cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    existing = {row[0] for row in prod_cursor.fetchall()}
    for idx_name, idx_sql, tbl_name in dev_cursor.fetchall():
        if tbl_name in _SYSTEM_TABLES or idx_name in existing:
            continue
        try:
            cursor.execute(idx_sql)
        except sqlite3.OperationalError:
            pass


# ======================== 主流程 ========================
def main():
    print("=" * 50)
    print("  OA 系统重启脚本")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 1. 备份数据库（无论有无差异都备份）
    print("\n[1/4] 备份数据库...")
    try:
        backup_databases()
    except Exception as e:
        print(f"备份异常: {e}")

    # 2. 同步数据库结构
    print("\n[2/4] 同步数据库结构...")
    try:
        sync_structure(DEV_DB, PROD_DB)
    except Exception as e:
        print(f"同步异常: {e}")

    # 3. 停止服务
    print("\n[3/4] 停止服务...")
    stop_services()

    # 4. 启动服务
    print("\n[4/4] 启动服务...")
    start_services()

    print("\n" + "=" * 50)
    print("  重启完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
