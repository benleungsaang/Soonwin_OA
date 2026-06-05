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

# ======================== 路径自动检测 ========================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 后端目录（可能是开发路径或部署路径）
DEV_DB = os.path.join(SCRIPT_DIR, "soonwin_oa_dev.db")
PROD_DB = os.path.join(SCRIPT_DIR, "soonwin_oa.db")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "数据库备份文件")

# 端口
BACKEND_PORT = 5000
NGINX_PORT = 5183

# nginx 路径（与 run_server.py 一致）
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
NGINX_PATH = os.path.join(PARENT_DIR, "nginx-1.28.1", "nginx.exe")
if not os.path.exists(NGINX_PATH):
    # 兜底：检查常见位置
    NGINX_PATH = r"C:\nginx\nginx.exe"
NGINX_CONF = os.path.join(os.path.dirname(NGINX_PATH), "conf", "nginx.conf")
if not os.path.exists(NGINX_CONF):
    NGINX_CONF = os.path.join(os.path.dirname(NGINX_PATH), "..", "conf", "nginx.conf")

VENV_ACTIVATE = os.path.join(SCRIPT_DIR, "venv", "Scripts", "activate.bat")
WSGI_FILE = os.path.join(SCRIPT_DIR, "wsgi.py")

# 系统表
_SYSTEM_TABLES = {
    "sqlite_sequence", "sqlite_stat1", "sqlite_stat2",
    "sqlite_stat3", "sqlite_stat4", "alembic_version",
    "_migration_history", "_migrate_history",
}


# ======================== 服务启停（进程管理，非 Windows 服务） ========================
def _get_pids_by_port(port):
    """通过 netstat 获取占用指定端口的 PID 列表"""
    try:
        result = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True, text=True, encoding="gbk", timeout=15,
        )
        pids = set()
        for line in result.stdout.splitlines():
            if f":{port}" in line and ("LISTENING" in line or "ESTABLISHED" in line):
                parts = line.strip().split()
                if parts:
                    pids.add(parts[-1])
        return list(pids)
    except Exception as e:
        print(f"  查询端口 {port} 失败: {e}")
        return []


def _kill_pids(pids, label=""):
    """强制终止指定 PID 列表"""
    for pid in pids:
        if pid == "0" or pid == "4":
            continue  # 跳过系统进程
        try:
            subprocess.run(
                ["taskkill", "/F", "/PID", pid],
                capture_output=True, text=True, encoding="gbk", timeout=10,
            )
            print(f"  已终止 {label} (PID: {pid})")
        except Exception as e:
            print(f"  终止 PID {pid} 失败: {e}")


def stop_services():
    """停止后端和 Nginx 进程"""
    print("[Restart] 停止后端 (端口 5000)...")
    pids = _get_pids_by_port(BACKEND_PORT)
    if pids:
        _kill_pids(pids, "waitress")
    else:
        print("  端口 5000 无进程")

    print("[Restart] 停止 Nginx (端口 5183)...")
    # 先尝试优雅停止
    if os.path.exists(NGINX_PATH):
        try:
            subprocess.run(
                [NGINX_PATH, "-s", "stop"],
                capture_output=True, text=True, encoding="gbk", timeout=15,
            )
        except Exception:
            pass
    time.sleep(2)
    # 再强制清理端口
    pids = _get_pids_by_port(NGINX_PORT)
    if pids:
        _kill_pids(pids, "nginx")
    else:
        print("  端口 5183 无进程")

    time.sleep(1)


def start_services():
    """启动后端和 Nginx"""
    # 启动后端
    print("[Restart] 启动后端 (端口 5000)...")
    if not os.path.exists(VENV_ACTIVATE):
        print(f"  [!] 虚拟环境不存在: {VENV_ACTIVATE}")
    elif not os.path.exists(WSGI_FILE):
        print(f"  [!] wsgi.py 不存在: {WSGI_FILE}")
    else:
        cmd = (
            f'cd /d "{SCRIPT_DIR}" && '
            f'call "{VENV_ACTIVATE}" && '
            f'waitress-serve --host=0.0.0.0 --port={BACKEND_PORT} wsgi:application'
        )
        try:
            subprocess.Popen(
                cmd, shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            print("  waitress 已启动")
        except Exception as e:
            print(f"  启动 waitress 失败: {e}")
    time.sleep(3)

    # 启动 Nginx
    print("[Restart] 启动 Nginx (端口 5183)...")
    if not os.path.exists(NGINX_PATH):
        print(f"  [!] nginx.exe 不存在: {NGINX_PATH}")
    elif not os.path.exists(NGINX_CONF):
        print(f"  [!] nginx.conf 不存在: {NGINX_CONF}")
    else:
        try:
            subprocess.run(
                [NGINX_PATH, "-c", NGINX_CONF],
                capture_output=True, text=True, encoding="gbk", timeout=15,
            )
            print("  nginx 已启动")
        except Exception as e:
            print(f"  启动 nginx 失败: {e}")
    time.sleep(2)


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
    """比较 dev 和 prod 结构"""
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
    """以 dev 结构为准更新 prod，保留 prod 数据"""
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

        # 收集 dev 表
        dev_cursor = dev_conn.cursor()
        dev_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        dev_tables = {}
        for n, s in dev_cursor.fetchall():
            if n not in _SYSTEM_TABLES and s:
                dev_tables[n] = s

        # 收集 prod 表
        prod_cursor = prod_conn.cursor()
        prod_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        prod_tables = {}
        for n, s in prod_cursor.fetchall():
            if n not in _SYSTEM_TABLES and s:
                prod_tables[n] = " ".join(s.split())

        # 新建表
        for t in sorted(set(dev_tables.keys()) - set(prod_tables.keys())):
            print(f"[DB Sync] 创建新表: {t}")
            cursor.execute(dev_tables[t])

        # 重建结构变化的表
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

        # 同步索引
        dev_cursor.execute(
            "SELECT name, sql, tbl_name FROM sqlite_master "
            "WHERE type='index' AND sql IS NOT NULL"
        )
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
def main():
    print("=" * 50)
    print("  OA 系统重启脚本")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  后端目录: {SCRIPT_DIR}")
    print("=" * 50)

    # 1. 停服务
    print("\n[1/4] 停止服务...")
    try:
        stop_services()
    except Exception as e:
        print(f"停止异常: {e}")

    # 2. 备份数据库
    print("\n[2/4] 备份数据库...")
    try:
        backup_databases()
    except Exception as e:
        print(f"备份异常: {e}")

    # 3. 同步数据库结构
    print("\n[3/4] 同步数据库结构...")
    try:
        sync_structure()
    except Exception as e:
        print(f"同步异常: {e}")

    # 4. 启服务
    print("\n[4/4] 启动服务...")
    start_services()

    print("\n" + "=" * 50)
    print("  重启完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
