"""
独立重启服务脚本
由 Flask /api/admin/restart 路由以子进程方式调用，不受 Flask 进程新旧影响。
也可手动执行：python restart_services.py

流程：停服务 → 备份DB → 同步DB结构 → 启服务
"""
import sqlite3
import subprocess
import os
import sys
import time
from datetime import datetime

# ======================== 路径 ========================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEV_DB = os.path.join(SCRIPT_DIR, "soonwin_oa_dev.db")
PROD_DB = os.path.join(SCRIPT_DIR, "soonwin_oa.db")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "数据库备份文件")

# 系统表
_SYSTEM_TABLES = {
    "sqlite_sequence", "sqlite_stat1", "sqlite_stat2",
    "sqlite_stat3", "sqlite_stat4", "alembic_version",
    "_migration_history", "_migrate_history",
}

# 服务名搜索关键词（按顺序匹配，找到第一个就停止搜索）
_SERVICE_KEYWORDS = ["waitress", "nginx", "SoonwinOA", "OA_Backend"]


# ======================== 服务管理（Windows 服务） ========================
def _find_services():
    """搜索系统中含有关键词的 Windows 服务，返回 {关键词: 服务名} 映射"""
    try:
        result = subprocess.run(
            ["sc", "query", "state=", "all"],
            capture_output=True, text=True, encoding="gbk", timeout=15,
        )
    except Exception as e:
        print(f"[Restart] 查询服务列表失败: {e}")
        return {}

    # 解析 SERVICE_NAME 行
    lines = result.stdout.splitlines()
    service_names = []
    for line in lines:
        line = line.strip()
        if line.startswith("SERVICE_NAME:"):
            name = line.split(":", 1)[1].strip()
            service_names.append(name)

    # 按关键词匹配
    found = {}
    for svc in service_names:
        svc_lower = svc.lower()
        for kw in _SERVICE_KEYWORDS:
            if kw.lower() in svc_lower and kw not in found:
                found[kw] = svc

    return found


def _get_svc_state(svc_name):
    """查询服务运行状态，返回 'RUNNING' / 'STOPPED' / 'UNKNOWN'"""
    try:
        r = subprocess.run(
            ["sc", "query", svc_name],
            capture_output=True, text=True, encoding="gbk", timeout=10,
        )
        for line in r.stdout.splitlines():
            if "STATE" in line.upper():
                if "RUNNING" in line.upper():
                    return "RUNNING"
                if "STOPPED" in line.upper():
                    return "STOPPED"
        return "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def stop_services():
    """停止所有匹配的 Windows 服务"""
    svc_map = _find_services()
    if not svc_map:
        print("[Restart] 未找到匹配的 Windows 服务，跳过停止")
        return svc_map

    print(f"[Restart] 找到服务: {svc_map}")

    for kw, svc_name in svc_map.items():
        state = _get_svc_state(svc_name)
        print(f"  {svc_name} = {state}")
        if state == "RUNNING":
            print(f"  停止 {svc_name} ...")
            try:
                subprocess.run(
                    ["sc", "stop", svc_name],
                    capture_output=True, text=True, encoding="gbk", timeout=60,
                )
                # 等待服务完全停止
                for _ in range(30):
                    if _get_svc_state(svc_name) == "STOPPED":
                        print(f"  {svc_name} 已停止")
                        break
                    time.sleep(1)
                else:
                    print(f"  [!] {svc_name} 停止超时(30s)")
            except Exception as e:
                print(f"  停止 {svc_name} 异常: {e}")

    return svc_map


def start_services(svc_map=None):
    """启动之前找到的服务"""
    if svc_map is None:
        svc_map = _find_services()
    if not svc_map:
        print("[Restart] 未找到匹配的 Windows 服务，跳过启动")
        return

    for kw, svc_name in svc_map.items():
        state = _get_svc_state(svc_name)
        if state == "RUNNING":
            print(f"  {svc_name} 已在运行，跳过")
            continue
        print(f"  启动 {svc_name} ...")
        try:
            subprocess.run(
                ["sc", "start", svc_name],
                capture_output=True, text=True, encoding="gbk", timeout=60,
            )
            time.sleep(3)
            new_state = _get_svc_state(svc_name)
            print(f"  {svc_name} = {new_state}")
        except Exception as e:
            print(f"  启动 {svc_name} 异常: {e}")


# ======================== 数据库备份 ========================
def backup_databases():
    """备份 dev 和 prod 两个数据库"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = []
    for db_path in [DEV_DB, PROD_DB]:
        if not os.path.exists(db_path):
            print(f"  跳过（不存在）: {db_path}")
            continue
        name, ext = os.path.splitext(os.path.basename(db_path))
        backup_path = os.path.join(BACKUP_DIR, f"{name}_{date_str}{ext}")
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
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    tables = {}
    for name, sql in cursor.fetchall():
        if name in _SYSTEM_TABLES or not sql:
            continue
        tables[name] = " ".join(sql.split())
    return tables


def compare_schemas():
    dev_conn = sqlite3.connect(DEV_DB)
    prod_conn = sqlite3.connect(PROD_DB)
    try:
        dev_t = _get_create_sqls(dev_conn)
        prod_t = _get_create_sqls(prod_conn)
        diffs = []
        for t in set(dev_t.keys()) - set(prod_t.keys()):
            diffs.append(f"新增表: {t}")
        for t in sorted(set(dev_t.keys()) & set(prod_t.keys())):
            if dev_t[t] != prod_t[t]:
                diffs.append(f"结构变化: {t}")
        return len(diffs) == 0, diffs
    finally:
        dev_conn.close()
        prod_conn.close()


def sync_structure():
    is_same, diffs = compare_schemas()
    if is_same:
        print("[DB Sync] 库结构一致，无需同步")
        return True

    print(f"[DB Sync] 检测到 {len(diffs)} 处差异:")
    for d in diffs:
        print(f"  - {d}")

    dev_conn = sqlite3.connect(DEV_DB)
    prod_conn = sqlite3.connect(PROD_DB)
    try:
        cursor = prod_conn.cursor()
        dev_cursor = dev_conn.cursor()
        dev_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        dev_tables = {n: s for n, s in dev_cursor.fetchall() if n not in _SYSTEM_TABLES and s}

        prod_cursor = prod_conn.cursor()
        prod_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        prod_tables = {n: " ".join(s.split()) for n, s in prod_cursor.fetchall() if n not in _SYSTEM_TABLES and s}

        # 新建表
        for t in sorted(set(dev_tables.keys()) - set(prod_tables.keys())):
            print(f"[DB Sync] 创建新表: {t}")
            cursor.execute(dev_tables[t])

        # 重建变化表
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
            dev_cols = [r[1] for r in dev_cursor.fetchall()]
            compatible = [c for c in dev_cols if c in col_names]

            temp = f"{t}_sync_temp"
            cursor.execute(f"ALTER TABLE [{t}] RENAME TO [{temp}]")
            cursor.execute(dev_tables[t])
            if old_rows and compatible:
                ph = ",".join(["?" for _ in compatible])
                ins = f"INSERT INTO [{t}] ({','.join(compatible)}) VALUES ({ph})"
                indices = [col_names.index(c) for c in compatible]
                for row in old_rows:
                    try:
                        cursor.execute(ins, [row[i] for i in indices])
                    except sqlite3.Error:
                        pass
            cursor.execute(f"DROP TABLE [{temp}]")

        # 索引
        dev_cursor.execute("SELECT name, sql, tbl_name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        prod_cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        existing = {r[0] for r in prod_cursor.fetchall()}
        for idx_name, idx_sql, tbl_name in dev_cursor.fetchall():
            if tbl_name in _SYSTEM_TABLES or idx_name in existing:
                continue
            try:
                cursor.execute(idx_sql)
            except sqlite3.OperationalError:
                pass

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


# ======================== 主流程 ========================
def _open_log():
    """打开日志文件供 stdout 重定向"""
    log_path = os.path.join(SCRIPT_DIR, "restart_output.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log = open(log_path, "a", encoding="utf-8", buffering=1)  # line-buffered
    # 写入分隔标记
    log.write(f"\n{'='*60}\n")
    log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OA 系统重启脚本 — 启动\n")
    log.write(f"后端目录: {SCRIPT_DIR}\n")
    log.write(f"{'='*60}\n")
    log.flush()
    return log, log_path


def main():
    # 重定向 stdout → 日志文件（所有 print() 自动写入，不再依赖父进程传句柄）
    log, log_path = _open_log()
    old_stdout = sys.stdout
    sys.stdout = log

    try:
        print("\n[1/3] 停止服务...")
        svc_map = stop_services()

        print("\n[2/3] 检查数据库结构...")
        while True:  # 把后续逻辑包进来，保证 finally 可以恢复 stdout
            try:
                is_same, diffs = compare_schemas()
                if is_same:
                    print("[DB] 库结构一致，无需同步，跳过备份")
                    break

                print(f"[DB] 检测到 {len(diffs)} 处差异:")
                for d in diffs:
                    print(f"  - {d}")
                print("[DB] 先备份再同步...")
                sys.stdout.flush()
                backup_databases()
                sync_structure()
                break
            except Exception as e:
                print(f"数据库处理异常: {e}")
                import traceback
                traceback.print_exc()
                break

        print("\n[3/3] 启动服务...")
        sys.stdout.flush()
        start_services(svc_map)

        print(f"\n{'='*50}")
        print("  重启完成")
        print(f"{'='*50}")
    finally:
        sys.stdout.flush()
        sys.stdout = old_stdout
        log.close()

    print(f"→ 详细日志已写入: {log_path}")


if __name__ == "__main__":
    main()
