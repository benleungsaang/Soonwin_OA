"""待办事项（Todo）路由蓝图

URL 前缀：/api/todos

权限模型：
- 路由级：route_permission(ROUTE_TODO_MANAGE)（全员共有）
- 数据级：
  * 普通用户：只能看/操作 author_id == 自己 emp_id 的 todo
  * 管理员（user_role='admin'）：全部可见可操作
- 操作级：
  * 留言（POST/DELETE messages）：管理员或任务创建人可添加，仅管理员可删除

emoji 说明：SQLite 默认 UTF-8 编码 + Python 3.12 str 原生支持 4 字节 emoji，
所有 text 字段都允许 emoji 输入，无需特殊处理。
"""
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from extensions import db
from app.utils.simple_auth_utils import route_permission
from app.utils.auth_utils import (
    get_user_id_from_token, get_user_role_from_token
)


def _resolve_user_name(user_id: str, fallback: str = '') -> str:
    """通过 emp_id 查 Employee 表获取姓名；查不到返回 fallback"""
    if not user_id:
        return fallback or '匿名'
    try:
        emp = Employee.query.filter_by(emp_id=user_id).first()
        return emp.name if emp and emp.name else (fallback or user_id)
    except Exception:
        return fallback or user_id
from app.constants.simple_permission_constants import ROUTE_TODO_MANAGE
from app.models.todo import Todo, TodoMessage, TodoMessageRead
from app.models.employee import Employee
from app.utils.upload_utils import save_uploaded_file, process_image_with_variants

todo_bp = Blueprint('todo', __name__)

# 待办媒体存储根目录（与 task 模块的 assets/TasksMedia 同级）
TODO_MEDIA_BASE = 'assets/TodoMedia'


# ============================================================
# 内部辅助函数
# ============================================================
def _get_todo_media_dir():
    """获取 todo 媒体文件存储的绝对目录（自动创建）"""
    base_dir = os.path.join(current_app.root_path, '..', TODO_MEDIA_BASE)
    base_dir = os.path.abspath(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _is_admin(user_role: str) -> bool:
    return user_role == 'admin'


def _build_todo_query(user_role: str, user_id: str):
    """根据用户身份构建 todo 列表查询
    - 管理员：看全部未软删
    - 普通用户：仅看自己创建的
    """
    q = Todo.query.filter_by(is_deleted=0)
    if not _is_admin(user_role):
        q = q.filter(Todo.author_id == user_id)
    return q


def _can_access_todo(todo: Todo, user_role: str, user_id: str) -> bool:
    """校验当前用户对单条 todo 是否有权访问"""
    if _is_admin(user_role):
        return True
    return todo.author_id == user_id


def _save_todo_image(file, sub_dir: str = 'todo') -> str:
    """保存 todo 图片，生成 WebP 变体，删除原图

    生成规则：
    - display: 最大 1600px WebP（详情弹窗用）
    - thumbnail: 最大 800px WebP（列表缩略图用）
    - 原图（JPG/PNG）生成 WebP 后删除，不保留大图

    返回 display WebP 的相对路径，前端用同一路径填充 image_url，
    缩略图通过命名约定访问：将 _display.webp → _thumbnail.webp
    """
    base_dir = _get_todo_media_dir()
    target_dir = os.path.join(base_dir, sub_dir)
    os.makedirs(target_dir, exist_ok=True)
    save_path, relative_path, filename = save_uploaded_file(file, target_dir, use_date_subdir=True)
    # relative_path 相对 target_dir（如 "2026/07/13/xxx.jpg"）
    name_no_ext, _ = os.path.splitext(filename)

    # 生成 WebP 变体（file_prefix 仅为文件名不含扩展名）
    result = process_image_with_variants(
        save_path, base_dir,
        file_prefix=name_no_ext,
        ext='jpg',
    )
    display_path = result.get('paths', {}).get('display', '')

    # 删除原图（JPG/PNG）
    try:
        os.remove(save_path)
    except OSError:
        pass

    # 返回 display 路径（前端拼 /assets/TodoMedia/）
    return display_path


def _compute_unread_count(todo_id: int, user_id: str) -> int:
    """计算某用户对某 todo 的未读留言数"""
    read_row = TodoMessageRead.query.filter_by(todo_id=todo_id, user_id=user_id).first()
    last_read_at = read_row.last_read_at if read_row else datetime(1970, 1, 1)
    return TodoMessage.query.filter(
        TodoMessage.todo_id == todo_id,
        TodoMessage.is_deleted == 0,
        TodoMessage.author_id != user_id,
        TodoMessage.created_at > last_read_at,
    ).count()


def _compute_unread_map(todo_ids, user_id: str) -> dict:
    """批量计算多个 todo 的未读数（避免 N+1 查询）"""
    if not todo_ids:
        return {}
    # 读取该用户的 last_read_at 映射
    read_rows = TodoMessageRead.query.filter(
        TodoMessageRead.user_id == user_id,
        TodoMessageRead.todo_id.in_(todo_ids),
    ).all()
    read_map = {r.todo_id: r.last_read_at for r in read_rows}
    # 统计 last_read_at 之后的留言数（排除自己的）
    unread_map = {tid: 0 for tid in todo_ids}
    for tid in todo_ids:
        last_read_at = read_map.get(tid, datetime(1970, 1, 1))
        cnt = TodoMessage.query.filter(
            TodoMessage.todo_id == tid,
            TodoMessage.is_deleted == 0,
            TodoMessage.author_id != user_id,
            TodoMessage.created_at > last_read_at,
        ).count()
        unread_map[tid] = cnt
    return unread_map


# ============================================================
# 1. 列表 GET /api/todos
# ============================================================
@todo_bp.route('/todos', methods=['GET'])
@route_permission(ROUTE_TODO_MANAGE)
def list_todos():
    """获取 todo 列表（按 date 降序，组内按 created_at 降序）

    Query:
        search: 模糊匹配 content / note
        status: pending / completed / all（默认 all）
        date: 指定日期 YYYY-MM-DD
    """
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        search = (request.args.get('search') or '').strip()
        status_filter = request.args.get('status', 'all')
        date_filter = (request.args.get('date') or '').strip()

        q = _build_todo_query(user_role, user_id)
        if status_filter in ('pending', 'completed'):
            q = q.filter(Todo.status == status_filter)
        if date_filter:
            q = q.filter(Todo.date == date_filter)
        if search:
            q = q.filter(
                db.or_(
                    Todo.content.like(f'%{search}%'),
                    Todo.note.like(f'%{search}%'),
                )
            )

        todos = q.order_by(Todo.date.desc(), Todo.created_at.desc()).all()
        todo_ids = [t.id for t in todos]
        unread_map = _compute_unread_map(todo_ids, user_id)

        return jsonify({
            'success': True,
            'data': [t.to_dict(include_unread_count=unread_map.get(t.id, 0)) for t in todos]
        })
    except Exception as e:
        print(f"[todo] list_todos 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 2. 创建 POST /api/todos
# ============================================================
@todo_bp.route('/todos', methods=['POST'])
@route_permission(ROUTE_TODO_MANAGE)
def create_todo():
    """创建 todo（author_id = 当前用户）"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        user_name = _resolve_user_name(user_id, fallback=user_id)
        data = request.get_json(silent=True) or {}

        content = (data.get('content') or '').strip()
        if not content:
            return jsonify({'success': False, 'message': '任务内容不能为空'}), 400

        todo = Todo(
            author_id=user_id,
            author_name=user_name,
            content=content,
            date=data.get('date') or datetime.now().strftime('%Y-%m-%d'),
            color=data.get('color') or 'white',
            note=data.get('note') or '',
            image_url=data.get('image_url') or None,
            status='pending',
        )
        db.session.add(todo)
        db.session.commit()

        return jsonify({'success': True, 'data': todo.to_dict(include_unread_count=0)})
    except Exception as e:
        db.session.rollback()
        print(f"[todo] create_todo 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 3. 详情 GET /api/todos/<id>
# ============================================================
@todo_bp.route('/todos/<int:todo_id>', methods=['GET'])
@route_permission(ROUTE_TODO_MANAGE)
def get_todo(todo_id):
    """获取单条 todo 详情 + 留言列表（已删除条目也可查看）"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        todo = Todo.query.filter_by(id=todo_id).first()
        if not todo:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        # 已删除的条目需校验访问权限（管理员/创建人可看）
        if todo.is_deleted and not _can_access_todo(todo, user_role, user_id):
            return jsonify({'success': False, 'message': '无权访问'}), 403
        if not _can_access_todo(todo, user_role, user_id):
            return jsonify({'success': False, 'message': '无权访问'}), 403

        messages = TodoMessage.query.filter_by(todo_id=todo_id, is_deleted=0) \
            .order_by(TodoMessage.created_at.asc()).all()
        unread = _compute_unread_count(todo_id, user_id)

        return jsonify({
            'success': True,
            'data': {
                **todo.to_dict(include_unread_count=unread),
                'messages': [m.to_dict() for m in messages],
            }
        })
    except Exception as e:
        print(f"[todo] get_todo 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 4. 更新 PUT /api/todos/<id>
# ============================================================
@todo_bp.route('/todos/<int:todo_id>', methods=['PUT'])
@route_permission(ROUTE_TODO_MANAGE)
def update_todo(todo_id):
    """更新 todo（仅创建人/管理员）"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        todo = Todo.query.filter_by(id=todo_id, is_deleted=0).first()
        if not todo:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access_todo(todo, user_role, user_id):
            return jsonify({'success': False, 'message': '无权操作'}), 403

        data = request.get_json(silent=True) or {}
        if 'content' in data and data['content'] is not None:
            todo.content = data['content'].strip() or todo.content
        if 'date' in data and data['date']:
            todo.date = data['date']
        if 'color' in data and data['color']:
            todo.color = data['color']
        if 'note' in data:
            todo.note = data['note'] or ''
        if 'image_url' in data:
            todo.image_url = data['image_url'] or None
        db.session.commit()

        return jsonify({'success': True, 'data': todo.to_dict(include_unread_count=0)})
    except Exception as e:
        db.session.rollback()
        print(f"[todo] update_todo 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 5. 软删 DELETE /api/todos/<id>
# ============================================================
@todo_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
@route_permission(ROUTE_TODO_MANAGE)
def delete_todo(todo_id):
    """软删除 todo（仅创建人/管理员）"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        todo = Todo.query.filter_by(id=todo_id, is_deleted=0).first()
        if not todo:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access_todo(todo, user_role, user_id):
            return jsonify({'success': False, 'message': '无权操作'}), 403

        todo.is_deleted = 1
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"[todo] delete_todo 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 6. 标记完成 POST /api/todos/<id>/complete
# ============================================================
@todo_bp.route('/todos/<int:todo_id>/complete', methods=['POST'])
@route_permission(ROUTE_TODO_MANAGE)
def complete_todo(todo_id):
    """标记完成。要求 completion_note 或 completion_image_url 至少有一个非空"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        todo = Todo.query.filter_by(id=todo_id, is_deleted=0).first()
        if not todo:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access_todo(todo, user_role, user_id):
            return jsonify({'success': False, 'message': '无权操作'}), 403
        if todo.status == 'completed':
            return jsonify({'success': False, 'message': '任务已是完成状态'}), 400

        data = request.get_json(silent=True) or {}
        note = (data.get('completion_note') or '').strip()
        image_url = data.get('completion_image_url') or ''
        if not note and not image_url:
            return jsonify({'success': False, 'message': '完成时必须填写文字或图片'}), 400

        todo.completion_note = note or None
        todo.completion_image_url = image_url or None
        todo.status = 'completed'
        # 如果之前已有 completed_at（撤销后又重新完成），保留原值；否则记当前时间
        if not todo.completed_at:
            todo.completed_at = datetime.now()
        db.session.commit()

        return jsonify({'success': True, 'data': todo.to_dict(include_unread_count=0)})
    except Exception as e:
        db.session.rollback()
        print(f"[todo] complete_todo 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 7. 撤销完成 POST /api/todos/<id>/uncomplete
# ============================================================
@todo_bp.route('/todos/<int:todo_id>/uncomplete', methods=['POST'])
@route_permission(ROUTE_TODO_MANAGE)
def uncomplete_todo(todo_id):
    """撤销完成（仅创建人/管理员）"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        todo = Todo.query.filter_by(id=todo_id, is_deleted=0).first()
        if not todo:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access_todo(todo, user_role, user_id):
            return jsonify({'success': False, 'message': '无权操作'}), 403

        todo.status = 'pending'
        # 保留 completion_note / completion_image_url / completed_at（撤销完成时不丢弃，
        # 用户再次勾选完成时可恢复填写；后端 complete 接口会优先复用已有值）
        db.session.commit()

        return jsonify({'success': True, 'data': todo.to_dict(include_unread_count=0)})
    except Exception as e:
        db.session.rollback()
        print(f"[todo] uncomplete_todo 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 8. 图片上传 POST /api/todos/upload-image
# ============================================================
@todo_bp.route('/todos/upload-image', methods=['POST'])
@route_permission(ROUTE_TODO_MANAGE)
def upload_image():
    """独立图片上传接口，返回 {image_url}

    - 前端选图后调用此接口拿到 URL，再把 URL 传给 create_todo / complete_todo
    - sub_dir 参数可指定 'todo' / 'completion'（默认 todo）
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未收到文件'}), 400
        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'success': False, 'message': '文件为空'}), 400
        sub_dir = request.form.get('sub_dir', 'todo')
        if sub_dir not in ('todo', 'completion'):
            sub_dir = 'todo'

        image_url = _save_todo_image(file, sub_dir=sub_dir)
        return jsonify({'success': True, 'data': {'image_url': image_url}})
    except Exception as e:
        print(f"[todo] upload_image 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 9. 留言列表 GET /api/todos/<id>/messages
# ============================================================
@todo_bp.route('/todos/<int:todo_id>/messages', methods=['GET'])
@route_permission(ROUTE_TODO_MANAGE)
def list_messages(todo_id):
    """获取某 todo 的留言列表（创建人或管理员可访问）"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        todo = Todo.query.filter_by(id=todo_id, is_deleted=0).first()
        if not todo:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access_todo(todo, user_role, user_id):
            return jsonify({'success': False, 'message': '无权访问'}), 403

        messages = TodoMessage.query.filter_by(todo_id=todo_id, is_deleted=0) \
            .order_by(TodoMessage.created_at.asc()).all()
        return jsonify({'success': True, 'data': [m.to_dict() for m in messages]})
    except Exception as e:
        print(f"[todo] list_messages 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 10. 添加留言 POST /api/todos/<id>/messages（仅 admin）
# ============================================================
@todo_bp.route('/todos/<int:todo_id>/messages', methods=['POST'])
@route_permission(ROUTE_TODO_MANAGE)
def add_message(todo_id):
    """添加留言（管理员或创建人可添加）"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''

        todo = Todo.query.filter_by(id=todo_id, is_deleted=0).first()
        if not todo:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        # 校验权限：管理员或任务创建人可留言
        if not _is_admin(user_role) and todo.author_id != user_id:
            return jsonify({'success': False, 'message': '仅管理员或任务创建人可添加留言'}), 403

        data = request.get_json(silent=True) or {}
        content = (data.get('content') or '').strip()
        if not content and not data.get('image_url'):
            return jsonify({'success': False, 'message': '留言内容不能为空'}), 400

        msg = TodoMessage(
            todo_id=todo_id,
            author_id=user_id,
            author_name=_resolve_user_name(user_id, fallback='管理员'),
            content=content,
            image_url=data.get('image_url') or None,
        )
        db.session.add(msg)
        db.session.commit()
        return jsonify({'success': True, 'data': msg.to_dict()})
    except Exception as e:
        db.session.rollback()
        print(f"[todo] add_message 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 11. 删除留言 DELETE /api/todos/<id>/messages/<msg_id>（仅 admin）
# ============================================================
@todo_bp.route('/todos/<int:todo_id>/messages/<int:msg_id>', methods=['DELETE'])
@route_permission(ROUTE_TODO_MANAGE)
def delete_message(todo_id, msg_id):
    """管理员删除留言（软删）"""
    try:
        user_role = get_user_role_from_token() or ''
        if not _is_admin(user_role):
            return jsonify({'success': False, 'message': '仅管理员可删除留言'}), 403

        msg = TodoMessage.query.filter_by(id=msg_id, todo_id=todo_id, is_deleted=0).first()
        if not msg:
            return jsonify({'success': False, 'message': '留言不存在'}), 404
        msg.is_deleted = 1
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"[todo] delete_message 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 12. 未读统计 GET /api/todos/notifications
# ============================================================
@todo_bp.route('/todos/notifications', methods=['GET'])
@route_permission(ROUTE_TODO_MANAGE)
def get_notifications():
    """获取当前用户可见 todo 范围内的未读留言统计（红点用）"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        if not user_id:
            return jsonify({'success': True, 'data': {'total_unread': 0, 'items': []}})

        q = _build_todo_query(user_role, user_id)
        todos = q.all()
        todo_ids = [t.id for t in todos]
        if not todo_ids:
            return jsonify({'success': True, 'data': {'total_unread': 0, 'items': []}})

        # 该用户对各 todo 的 last_read_at
        read_rows = TodoMessageRead.query.filter(
            TodoMessageRead.user_id == user_id,
            TodoMessageRead.todo_id.in_(todo_ids),
        ).all()
        read_map = {r.todo_id: r.last_read_at for r in read_rows}

        # 每个 todo 取最新一条"来自别人、未删除、在 last_read_at 之后"的留言
        items = []
        total_unread = 0
        todo_map = {t.id: t for t in todos}
        for tid in todo_ids:
            last_read_at = read_map.get(tid, datetime(1970, 1, 1))
            latest = TodoMessage.query.filter(
                TodoMessage.todo_id == tid,
                TodoMessage.is_deleted == 0,
                TodoMessage.author_id != user_id,
                TodoMessage.created_at > last_read_at,
            ).order_by(TodoMessage.created_at.desc()).first()
            if not latest:
                continue
            count = TodoMessage.query.filter(
                TodoMessage.todo_id == tid,
                TodoMessage.is_deleted == 0,
                TodoMessage.author_id != user_id,
                TodoMessage.created_at > last_read_at,
            ).count()
            todo = todo_map.get(tid)
            items.append({
                'todo_id': tid,
                'unread_count': count,
                'latest_message': {
                    'id': latest.id,
                    'content': latest.content,
                    'author_name': latest.author_name,
                    'created_at': latest.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                },
                'todo_content_preview': (todo.content[:30] + '...') if todo and len(todo.content) > 30 else (todo.content if todo else ''),
            })
            total_unread += count

        return jsonify({'success': True, 'data': {'total_unread': total_unread, 'items': items}})
    except Exception as e:
        print(f"[todo] get_notifications 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 13. 标记已读 POST /api/todos/notifications/clear
# ============================================================
@todo_bp.route('/todos/notifications/clear', methods=['POST'])
@route_permission(ROUTE_TODO_MANAGE)
def clear_notifications():
    """将指定 todo 标记为已读（更新 last_read_at = now）"""
    try:
        user_id = get_user_id_from_token() or ''
        if not user_id:
            return jsonify({'success': False, 'message': '未登录'}), 401

        data = request.get_json(silent=True) or {}
        todo_id = data.get('todo_id')
        now = datetime.now()

        if todo_id:
            # 标记单个 todo 已读
            row = TodoMessageRead.query.filter_by(todo_id=todo_id, user_id=user_id).first()
            if row:
                row.last_read_at = now
            else:
                db.session.add(TodoMessageRead(todo_id=todo_id, user_id=user_id, last_read_at=now))
        else:
            # 标记所有可见 todo 已读
            user_role = get_user_role_from_token() or ''
            todos = _build_todo_query(user_role, user_id).all()
            existing = {r.todo_id: r for r in TodoMessageRead.query.filter(
                TodoMessageRead.user_id == user_id,
                TodoMessageRead.todo_id.in_([t.id for t in todos]),
            ).all()} if todos else {}
            for t in todos:
                row = existing.get(t.id)
                if row:
                    row.last_read_at = now
                else:
                    db.session.add(TodoMessageRead(todo_id=t.id, user_id=user_id, last_read_at=now))

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"[todo] clear_notifications 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 14. 回收站列表 GET /api/todos/deleted
# ============================================================
@todo_bp.route('/todos/deleted', methods=['GET'])
@route_permission(ROUTE_TODO_MANAGE)
def list_deleted_todos():
    """获取已软删除的 todo 列表（仅管理员可见全部，普通用户只看自己的）"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''

        q = Todo.query.filter_by(is_deleted=1)
        if not _is_admin(user_role):
            q = q.filter(Todo.author_id == user_id)
        todos = q.order_by(Todo.updated_at.desc()).all()

        return jsonify({
            'success': True,
            'data': [t.to_dict(include_unread_count=0) for t in todos]
        })
    except Exception as e:
        print(f"[todo] list_deleted_todos 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 15. 恢复已删除 todo POST /api/todos/<id>/restore
# ============================================================
@todo_bp.route('/todos/<int:todo_id>/restore', methods=['POST'])
@route_permission(ROUTE_TODO_MANAGE)
def restore_todo(todo_id):
    """恢复已软删除的 todo"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        todo = Todo.query.filter_by(id=todo_id, is_deleted=1).first()
        if not todo:
            return jsonify({'success': False, 'message': '待恢复的任务不存在'}), 404
        if not _can_access_todo(todo, user_role, user_id):
            return jsonify({'success': False, 'message': '无权操作'}), 403

        todo.is_deleted = 0
        db.session.commit()
        return jsonify({'success': True, 'data': todo.to_dict(include_unread_count=0)})
    except Exception as e:
        db.session.rollback()
        print(f"[todo] restore_todo 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 16. 永久删除 DELETE /api/todos/<id>/permanent
# ============================================================
@todo_bp.route('/todos/<int:todo_id>/permanent', methods=['DELETE'])
@route_permission(ROUTE_TODO_MANAGE)
def permanent_delete_todo(todo_id):
    """永久删除 todo（仅管理员可操作）"""
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        if not _is_admin(user_role):
            return jsonify({'success': False, 'message': '仅管理员可永久删除'}), 403

        todo = Todo.query.filter_by(id=todo_id).first()
        if not todo:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        # 删除相关留言
        TodoMessage.query.filter_by(todo_id=todo_id).delete()
        # 删除已读记录
        TodoMessageRead.query.filter_by(todo_id=todo_id).delete()
        # 删除 todo 本身
        db.session.delete(todo)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"[todo] permanent_delete_todo 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
