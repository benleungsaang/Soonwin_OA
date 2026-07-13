import sqlite3
import os
from contextlib import contextmanager

DATABASE = 'data/app.db'

def get_db():
    """获取数据库连接"""
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db_conn():
    """上下文管理器，自动关闭连接"""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """初始化数据库表"""
    with get_db_conn() as conn:
        cursor = conn.cursor()

        # 待办事项表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                color TEXT DEFAULT 'white',
                date TEXT,
                note TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        # 货柜表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cargo (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT DEFAULT 'white',
                weight_coefficient INTEGER DEFAULT 5000,
                total_weight REAL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        # 货柜货物明细表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cargo_boxes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cargo_id TEXT NOT NULL,
                name TEXT,
                length REAL DEFAULT 0,
                width REAL DEFAULT 0,
                height REAL DEFAULT 0,
                qty INTEGER DEFAULT 1,
                nw REAL DEFAULT 0,
                gw REAL DEFAULT 0,
                meas REAL DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY (cargo_id) REFERENCES cargo(id) ON DELETE CASCADE
            )
        ''')

        # 微博客表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                repost_from TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        # 兼容旧表：添加 repost_from 列
        try:
            cursor.execute('ALTER TABLE posts ADD COLUMN repost_from TEXT')
        except:
            pass

        # 微博客媒体附件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT NOT NULL,
                media_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
            )
        ''')

        # 微博客留言表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_comments (
                id TEXT PRIMARY KEY,
                post_id TEXT NOT NULL,
                author TEXT DEFAULT '匿名',
                content TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
            )
        ''')

        # 货柜汇总数据表（冗余存储，加速查询）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cargo_summary (
                cargo_id TEXT PRIMARY KEY,
                total_boxes INTEGER DEFAULT 0,
                total_lines INTEGER DEFAULT 0,
                total_volume_cbm REAL DEFAULT 0,
                total_nw REAL DEFAULT 0,
                total_gw REAL DEFAULT 0,
                total_volume_weight_express REAL DEFAULT 0,
                total_volume_weight_air REAL DEFAULT 0,
                total_volume_weight_sea REAL DEFAULT 0,
                chargeable_weight_express REAL DEFAULT 0,
                chargeable_weight_air REAL DEFAULT 0,
                chargeable_weight_sea REAL DEFAULT 0,
                FOREIGN KEY (cargo_id) REFERENCES cargo(id) ON DELETE CASCADE
            )
        ''')

        # 设置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # 添加索引（如果不存在）
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_post_media_post_id ON post_media(post_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON post_comments(post_id)')

        conn.commit()

def import_todos_from_json():
    """从 todos.json 导入数据"""
    import json
    from datetime import datetime

    if not os.path.exists('data/todos.json'):
        return

    with open('data/todos.json', 'r', encoding='utf-8') as f:
        todos = json.load(f)

    with get_db_conn() as conn:
        cursor = conn.cursor()
        for todo in todos:
            cursor.execute('''
                INSERT OR IGNORE INTO todos (id, content, completed, color, date, note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                todo.get('id'),
                todo.get('content', ''),
                1 if todo.get('completed') else 0,
                todo.get('color', 'white'),
                todo.get('date'),
                todo.get('note', ''),
                todo.get('createdAt'),
                todo.get('updatedAt')
            ))

def import_cargo_from_json():
    """从 cargo.json 导入数据"""
    import json
    from datetime import datetime

    if not os.path.exists('data/cargo.json'):
        return

    with open('data/cargo.json', 'r', encoding='utf-8') as f:
        cargo_list = json.load(f)

    with get_db_conn() as conn:
        cursor = conn.cursor()
        for cargo in cargo_list:
            # 导入货柜主表
            cursor.execute('''
                INSERT OR IGNORE INTO cargo (id, name, color, weight_coefficient, total_weight, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                cargo.get('id'),
                cargo.get('name', ''),
                cargo.get('color', 'white'),
                cargo.get('weightCoefficient', 5000),
                cargo.get('totalWeight', 0),
                cargo.get('createdAt'),
                cargo.get('updatedAt')
            ))

            # 导入货柜货物明细
            for box in cargo.get('boxes', []):
                cursor.execute('''
                    INSERT INTO cargo_boxes (cargo_id, name, length, width, height, qty, nw, gw, meas, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cargo.get('id'),
                    box.get('name', ''),
                    box.get('length', 0),
                    box.get('width', 0),
                    box.get('height', 0),
                    box.get('qty', 1),
                    box.get('nw', 0),
                    box.get('gw', 0),
                    box.get('meas', 0),
                    cargo.get('createdAt')
                ))

            # 导入汇总数据
            summary = cargo.get('summary', {})
            if summary:
                cursor.execute('''
                    INSERT OR IGNORE INTO cargo_summary (
                        cargo_id, total_boxes, total_lines, total_volume_cbm,
                        total_nw, total_gw, total_volume_weight_express,
                        total_volume_weight_air, total_volume_weight_sea,
                        chargeable_weight_express, chargeable_weight_air, chargeable_weight_sea
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cargo.get('id'),
                    summary.get('totalBoxes', 0),
                    summary.get('totalLines', 0),
                    summary.get('totalVolumeCBM', 0),
                    summary.get('totalNW', 0),
                    summary.get('totalGW', 0),
                    summary.get('totalVolumeWeightExpress', 0),
                    summary.get('totalVolumeWeightAir', 0),
                    summary.get('totalVolumeWeightSea', 0),
                    summary.get('chargeableWeightExpress', 0),
                    summary.get('chargeableWeightAir', 0),
                    summary.get('chargeableWeightSea', 0)
                ))

def migrate_all():
    """执行全量迁移"""
    init_db()
    import_todos_from_json()
    import_cargo_from_json()
    print("数据迁移完成！")

if __name__ == '__main__':
    migrate_all()
