import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from modules.database import get_db_conn

todo_bp = Blueprint('todo', __name__)

@todo_bp.route('', methods=['GET'])
def get_tasks():
    """获取所有任务"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM todos ORDER BY date DESC, id DESC')
        rows = cursor.fetchall()
        tasks = []
        for row in rows:
            tasks.append({
                'id': row['id'],
                'content': row['content'],
                'completed': bool(row['completed']),
                'color': row['color'],
                'date': row['date'],
                'note': row['note'],
                'createdAt': row['created_at'],
                'updatedAt': row['updated_at']
            })
        return jsonify(tasks)

@todo_bp.route('/settings', methods=['GET'])
def get_settings():
    """获取设置"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM settings')
        rows = cursor.fetchall()
        settings = {}
        for row in rows:
            val = row['value']
            # 尝试转换为合适类型
            if val == 'true':
                val = True
            elif val == 'false':
                val = False
            elif val.isdigit():
                val = int(val)
            try:
                settings[row['key']] = json.loads(val)
            except:
                settings[row['key']] = val
        return jsonify(settings)

@todo_bp.route('/settings', methods=['PUT'])
def update_settings():
    """更新设置"""
    data = request.get_json()
    with get_db_conn() as conn:
        cursor = conn.cursor()
        for key, value in data.items():
            if isinstance(value, bool):
                value = 'true' if value else 'false'
            elif isinstance(value, (dict, list)):
                value = json.dumps(value)
            else:
                value = str(value)
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            ''', (key, value))
    return jsonify(data)

@todo_bp.route('', methods=['POST'])
def add_task():
    """添加新任务"""
    data = request.get_json()
    now = datetime.now().isoformat()
    task = {
        'id': str(datetime.now().timestamp() * 1000),
        'content': data.get('content', ''),
        'completed': False,
        'color': data.get('color', 'white'),
        'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'note': data.get('note', ''),
        'createdAt': now,
        'updatedAt': now
    }
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO todos (id, content, completed, color, date, note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (task['id'], task['content'], 0, task['color'], task['date'], task['note'], task['createdAt'], task['updatedAt']))
    return jsonify(task), 201

@todo_bp.route('/<task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    data = request.get_json()
    now = datetime.now().isoformat()
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM todos WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Task not found'}), 404

        completed = data.get('completed', bool(row['completed']))
        cursor.execute('''
            UPDATE todos SET content=?, completed=?, color=?, date=?, note=?, updated_at=?
            WHERE id=?
        ''', (
            data.get('content', row['content']),
            1 if completed else 0,
            data.get('color', row['color']),
            data.get('date', row['date']),
            data.get('note', row['note']),
            now,
            task_id
        ))
    return jsonify({'id': task_id, 'updated': True})

@todo_bp.route('/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM todos WHERE id = ?', (task_id,))
        if cursor.rowcount == 0:
            return jsonify({'error': 'Task not found'}), 404
    return jsonify({'success': True})

@todo_bp.route('/reorder', methods=['POST'])
def reorder_tasks():
    """重新排序任务"""
    data = request.get_json()
    new_order = data.get('order', [])
    with get_db_conn() as conn:
        cursor = conn.cursor()
        for i, task_id in enumerate(new_order):
            cursor.execute('UPDATE todos SET updated_at=? WHERE id=?', (datetime.now().isoformat(), task_id))
    return jsonify({'success': True})

@todo_bp.route('/export', methods=['GET'])
def export_tasks():
    """导出所有任务为JSON"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM todos ORDER BY id')
        rows = cursor.fetchall()
        tasks = []
        for row in rows:
            tasks.append({
                'id': row['id'],
                'content': row['content'],
                'completed': bool(row['completed']),
                'color': row['color'],
                'date': row['date'],
                'note': row['note'],
                'createdAt': row['created_at'],
                'updatedAt': row['updated_at']
            })
        return jsonify(tasks)

@todo_bp.route('/import', methods=['POST'])
def import_tasks():
    """导入任务JSON"""
    data = request.get_json()
    if isinstance(data, list):
        with get_db_conn() as conn:
            cursor = conn.cursor()
            for i, task in enumerate(data):
                task['id'] = str(datetime.now().timestamp() * 1000) + str(i)
                task.setdefault('content', '')
                task.setdefault('completed', False)
                task.setdefault('color', 'white')
                task.setdefault('date', datetime.now().strftime('%Y-%m-%d'))
                task.setdefault('note', '')
                now = datetime.now().isoformat()
                cursor.execute('''
                    INSERT INTO todos (id, content, completed, color, date, note, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (task['id'], task['content'], 1 if task['completed'] else 0, task['color'],
                      task['date'], task['note'], now, now))
        return jsonify({'success': True, 'count': len(data)})
    return jsonify({'error': 'Invalid format'}), 400

@todo_bp.route('/save', methods=['POST'])
def save_all():
    """保存所有任务（手动保存）"""
    data = request.get_json()
    if isinstance(data, list):
        with get_db_conn() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            for task in data:
                task.setdefault('content', '')
                task.setdefault('completed', False)
                task.setdefault('color', 'white')
                task.setdefault('date', datetime.now().strftime('%Y-%m-%d'))
                task.setdefault('note', '')
                cursor.execute('''
                    INSERT OR REPLACE INTO todos (id, content, completed, color, date, note, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (task['id'], task['content'], 1 if task['completed'] else 0, task['color'],
                      task['date'], task['note'], task.get('createdAt', now), now))
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid format'}), 400
