"""
数据库模块 - todo 精简版
=======================

只包含 todo 模块所需的表（todos + settings）。
如果你新项目中已经存在 database.py，可以直接使用本文件中的表结构，
或合并到现有 database.py 中。

提供的功能：
- get_db()              获取连接
- get_db_conn()         上下文管理器（推荐用法）
- init_db()             初始化 todo 相关表
- import_todos_from_json()  从旧 JSON 文件迁移数据（可选）
"""

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
    """上下文管理器：自动 commit / rollback / close（推荐用法）"""
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
    """初始化 todo 相关数据表（可重复执行）"""
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

        # 设置表（用于保存前端开关、排序等偏好）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        conn.commit()


def import_todos_from_json():
    """
    可选：从旧的 data/todos.json 一次性迁移到 SQLite
    在新项目通常不需要调用，但保留作为数据恢复参考。
    """
    import json

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


if __name__ == '__main__':
    init_db()
    import_todos_from_json()
    print('todo 数据库初始化完成！')