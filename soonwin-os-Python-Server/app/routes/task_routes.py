"""任务跟踪相关路由

可见性逻辑：
    visible_to(user) = isAdmin(user)
                     OR isAuthor(user, task)
                     OR (visibilityType='role' AND value=user.role)
                     OR (visibilityType='employee' AND value=user.emp_id)

默认：仅创建人 + 管理员可见。设了 visibility 后"或"逻辑可见。
"""
import json
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from extensions import db
from app.utils.simple_auth_utils import route_permission
from app.utils.auth_utils import (
    require_auth, get_user_id_from_token, get_user_role_from_token
)
from app.constants.simple_permission_constants import ROUTE_TASK_TRACK_MANAGE
from app.models.task import Task
from app.models.task_comment import TaskComment
from app.models.task_visibility import TaskVisibility
from app.models.task_like import TaskLike
from app.models.task_history import TaskHistory
from app.utils.upload_utils import (
    save_uploaded_file, generate_unique_filename, sanitize_filename,
    UPLOAD_CONFIG
)

task_bp = Blueprint('task', __name__)

# 任务媒体文件存储路径（相对于 app 目录）
TASK_MEDIA_BASE = 'assets/TasksMedia'


def _get_task_media_dir():
    """获取任务媒体文件的绝对存储目录"""
    base_dir = os.path.join(current_app.root_path, '..', TASK_MEDIA_BASE)
    base_dir = os.path.abspath(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _get_current_user_name():
    """获取当前用户名"""
    user_id = get_user_id_from_token()
    if not user_id:
        return '匿名'
    try:
        from app.models.employee import Employee
        emp = Employee.query.filter_by(emp_id=user_id).first()
        return emp.name if emp else user_id
    except Exception:
        return user_id


def _is_admin(user_role: str) -> bool:
    """判断是否为管理员"""
    return user_role == 'admin'


def _build_task_subquery(user_role: str, user_id: str):
    """根据可见性规则构建任务过滤子查询（管理员可见全部）"""
    q = Task.query.filter_by(is_deleted=0)
    if _is_admin(user_role):
        return q

    # 可见的任务 ID：
    # 1. 创建人自己的任务
    # 2. TaskVisibility 记录匹配的任务
    own_ids = db.select(Task.id).where(Task.author_id == user_id)
    role_ids = db.select(TaskVisibility.task_id).where(
        db.and_(
            TaskVisibility.visibility_type == 'role',
            TaskVisibility.visibility_value == user_role
        )
    )
    emp_ids = db.select(TaskVisibility.task_id).where(
        db.and_(
            TaskVisibility.visibility_type == 'employee',
            TaskVisibility.visibility_value == user_id
        )
    )
    q = q.filter(
        db.or_(
            Task.id.in_(own_ids),
            Task.id.in_(role_ids),
            Task.id.in_(emp_ids)
        )
    )
    return q


def _is_task_visible_to_user(task: Task, user_role: str, user_id: str) -> bool:
    """检查单个任务对用户是否可见（用于详情/编辑/删除等单条操作）"""
    if _is_admin(user_role):
        return True
    if task.author_id == user_id:
        return True
    # 检查 visibility 配置
    vis = TaskVisibility.query.filter_by(task_id=task.id).all()
    for v in vis:
        if v.visibility_type == 'role' and v.visibility_value == user_role:
            return True
        if v.visibility_type == 'employee' and v.visibility_value == user_id:
            return True
    return False


def _save_task_image(file, sub_dir='todo') -> str:
    """保存任务附图，返回相对路径

    简化实现：只支持图片，不做 v2 缩略图（任务卡片不需要展开灯箱）。
    """
    base_dir = _get_task_media_dir()
    target_dir = os.path.join(base_dir, sub_dir)
    os.makedirs(target_dir, exist_ok=True)

    save_path, relative_path, filename = save_uploaded_file(file, target_dir, use_date_subdir=True)
    return relative_path.replace('\\', '/')


def _create_history_snapshot(task: Task, modified_by: str):
    """创建任务快照（修改前完整 JSON 快照）"""
    snapshot = {
        'id': task.id,
        'author_id': task.author_id,
        'author_name': task.author_name,
        'content': task.content,
        'status': task.status,
        'completion_note': task.completion_note,
        'completion_image_url': task.completion_image_url,
        'todo_image_url': task.todo_image_url,
        'expected_date': task.expected_date,
        'background_color': task.background_color,
        'like_count': task.like_count,
        'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else None,
        'updated_at': task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else None,
        'completed_at': task.completed_at.strftime('%Y-%m-%d %H:%M:%S') if task.completed_at else None,
    }
    history = TaskHistory(
        task_id=task.id,
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        modified_by=modified_by or '',
    )
    db.session.add(history)


# ============================================================
# 任务 CRUD
# ============================================================

@task_bp.route('/tasks', methods=['GET'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def get_tasks():
    """获取任务列表（搜索/筛选/分页）

    查询参数：
        page, per_page: 分页
        search: 关键词搜索（content / completion_note）
        status: pending | completed | all
        show_deleted: 1=包含已删除（仅管理员可用）
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        status_filter = request.args.get('status', 'all', type=str)
        show_deleted = request.args.get('show_deleted', '0', type=str) == '1'

        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''

        # 基础查询（可见性过滤）
        if show_deleted and _is_admin(user_role):
            query = Task.query.filter_by(is_deleted=1)
        else:
            query = _build_task_subquery(user_role, user_id)

        # 状态过滤
        if status_filter in ('pending', 'completed'):
            query = query.filter(Task.status == status_filter)

        # 关键词搜索
        if search:
            query = query.filter(
                db.or_(
                    Task.content.like(f'%{search}%'),
                    Task.completion_note.like(f'%{search}%')
                )
            )

        query = query.order_by(Task.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # 批量计算每条任务的修改历史数（避免 N+1 查询）
        task_ids = [t.id for t in pagination.items]
        history_count_map: dict = {}
        if task_ids:
            from sqlalchemy import func
            rows = db.session.query(
                TaskHistory.task_id, func.count(TaskHistory.id)
            ).filter(TaskHistory.task_id.in_(task_ids)).group_by(TaskHistory.task_id).all()
            for tid, cnt in rows:
                history_count_map[tid] = cnt

        tasks = []
        for t in pagination.items:
            d = t.to_dict()
            # 标记当前用户是否已点赞
            if user_id:
                d['is_liked'] = TaskLike.query.filter_by(
                    task_id=t.id, user_id=user_id).first() is not None
            else:
                d['is_liked'] = False
            # 计算可见留言数（仅未删除的）
            d['comment_count'] = t.comments.filter_by(is_deleted=0).count()
            # 覆盖 to_dict 的逐条 N+1 结果，使用批量查询值
            d['history_count'] = history_count_map.get(t.id, 0)
            tasks.append(d)

        return jsonify({
            'success': True,
            'data': {
                'tasks': tasks,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages,
            }
        })
    except Exception as e:
        print(f"获取任务列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@task_bp.route('/tasks', methods=['POST'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def create_task():
    """创建任务

    支持两种模式：
    1. 单文件：直接通过 file 字段上传
    2. JSON：纯文本任务，无附图
    """
    try:
        # 优先尝试 JSON 格式
        if request.is_json:
            data = request.get_json() or {}
            content = (data.get('content') or '').strip()
            expected_date = data.get('expected_date') or None
            background_color = data.get('background_color') or None
            todo_image_url = data.get('todo_image_url') or None
        else:
            content = (request.form.get('content') or '').strip()
            expected_date = request.form.get('expected_date') or None
            background_color = request.form.get('background_color') or None
            todo_image_url = request.form.get('todo_image_url') or None

        if not content:
            return jsonify({'success': False, 'message': '任务内容不能为空'}), 400

        # 处理图片上传（如果有）
        file = None
        if not request.is_json:
            file = request.files.get('todo_image')
            if file and file.filename:
                todo_image_url = _save_task_image(file, sub_dir='todo')

        user_id = get_user_id_from_token() or ''
        user_name = _get_current_user_name()

        task = Task(
            author_id=user_id,
            author_name=user_name,
            content=content,
            status='pending',
            expected_date=expected_date,
            background_color=background_color,
            todo_image_url=todo_image_url,
        )
        db.session.add(task)
        db.session.commit()

        return jsonify({'success': True, 'data': task.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        print(f"创建任务失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def get_task(task_id):
    """获取任务详情"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        if not _is_task_visible_to_user(task, user_role, user_id):
            return jsonify({'success': False, 'message': '无权限查看此任务'}), 403

        d = task.to_dict()
        if user_id:
            d['is_liked'] = TaskLike.query.filter_by(
                task_id=task.id, user_id=user_id).first() is not None
        else:
            d['is_liked'] = False
        d['comment_count'] = task.comments.filter_by(is_deleted=0).count()
        return jsonify({'success': True, 'data': d})
    except Exception as e:
        print(f"获取任务详情失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def update_task(task_id):
    """更新任务（自动保存修改历史）"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        if not _is_admin(user_role) and task.author_id != user_id:
            return jsonify({'success': False, 'message': '无权限编辑此任务'}), 403

        # 保存修改历史快照
        _create_history_snapshot(task, user_id)

        # 解析请求体
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict() if request.form else {}

        # 字段更新（仅更新提供的字段）
        if 'content' in data:
            task.content = (data.get('content') or '').strip() or task.content
        if 'expected_date' in data:
            task.expected_date = data.get('expected_date') or None
        if 'background_color' in data:
            task.background_color = data.get('background_color') or None
        if 'completion_note' in data:
            task.completion_note = data.get('completion_note') or None
        if 'completion_image_url' in data:
            task.completion_image_url = data.get('completion_image_url') or None
        if 'todo_image_url' in data:
            task.todo_image_url = data.get('todo_image_url') or None

        # 处理状态切换（特殊处理：完成时设置 completed_at，回退时清除）
        if 'status' in data:
            new_status = data.get('status')
            if new_status in ('pending', 'completed'):
                if new_status == 'completed' and task.status != 'completed':
                    task.completed_at = datetime.now()
                elif new_status == 'pending':
                    task.completed_at = None
                task.status = new_status

        # 处理图片上传
        file = None
        if not request.is_json:
            file = request.files.get('todo_image')
            if file and file.filename:
                task.todo_image_url = _save_task_image(file, sub_dir='todo')
            completion_file = request.files.get('completion_image')
            if completion_file and completion_file.filename:
                task.completion_image_url = _save_task_image(completion_file, sub_dir='completion')

        task.updated_at = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'data': task.to_dict()})
    except Exception as e:
        db.session.rollback()
        print(f"更新任务失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def delete_task(task_id):
    """软删除任务"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        if not _is_admin(user_role) and task.author_id != user_id:
            return jsonify({'success': False, 'message': '无权限删除此任务'}), 403

        task.is_deleted = 1
        task.updated_at = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'message': '任务已移至回收站'})
    except Exception as e:
        db.session.rollback()
        print(f"删除任务失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@task_bp.route('/tasks/<int:task_id>/restore', methods=['POST'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def restore_task(task_id):
    """恢复已删除的任务"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        task.is_deleted = 0
        task.updated_at = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'message': '任务已恢复'})
    except Exception as e:
        db.session.rollback()
        print(f"恢复任务失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 留言
# ============================================================

@task_bp.route('/tasks/<int:task_id>/comments', methods=['POST'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def create_comment(task_id):
    """添加留言"""
    try:
        task = Task.query.get(task_id)
        if not task or task.is_deleted:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        if not _is_task_visible_to_user(task, user_role, user_id):
            return jsonify({'success': False, 'message': '无权限留言'}), 403

        data = request.get_json() or {}
        content = (data.get('content') or '').strip()
        if not content:
            return jsonify({'success': False, 'message': '留言内容不能为空'}), 400

        comment = TaskComment(
            task_id=task_id,
            author_id=user_id,
            author_name=_get_current_user_name(),
            content=content,
        )
        db.session.add(comment)
        task.updated_at = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'data': comment.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        print(f"添加留言失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@task_bp.route('/tasks/comments/<int:comment_id>', methods=['DELETE'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def delete_comment(comment_id):
    """软删除留言（自己可删，管理员可删所有）"""
    try:
        comment = TaskComment.query.get(comment_id)
        if not comment:
            return jsonify({'success': False, 'message': '留言不存在'}), 404

        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        if not _is_admin(user_role) and comment.author_id != user_id:
            return jsonify({'success': False, 'message': '无权限删除此留言'}), 403

        comment.is_deleted = 1
        comment.deleted_at = datetime.now()
        comment.deleted_by = _get_current_user_name()
        db.session.commit()
        return jsonify({'success': True, 'message': '留言已删除'})
    except Exception as e:
        db.session.rollback()
        print(f"删除留言失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@task_bp.route('/tasks/<int:task_id>/comments', methods=['GET'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def get_comments(task_id):
    """获取任务的留言列表"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        if not _is_task_visible_to_user(task, user_role, user_id):
            return jsonify({'success': False, 'message': '无权限查看'}), 403

        comments = TaskComment.query.filter_by(task_id=task_id)\
            .order_by(TaskComment.created_at.asc()).all()
        return jsonify({'success': True, 'data': [c.to_dict() for c in comments]})
    except Exception as e:
        print(f"获取留言失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 点赞
# ============================================================

@task_bp.route('/tasks/<int:task_id>/like', methods=['POST'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def toggle_like(task_id):
    """切换点赞状态"""
    try:
        task = Task.query.get(task_id)
        if not task or task.is_deleted:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        if not _is_task_visible_to_user(task, user_role, user_id):
            return jsonify({'success': False, 'message': '无权限点赞'}), 403

        existing = TaskLike.query.filter_by(task_id=task_id, user_id=user_id).first()
        if existing:
            db.session.delete(existing)
            task.like_count = max(0, (task.like_count or 0) - 1)
            db.session.commit()
            return jsonify({'success': True, 'data': {'liked': False, 'like_count': task.like_count}})
        else:
            like = TaskLike(task_id=task_id, user_id=user_id)
            db.session.add(like)
            task.like_count = (task.like_count or 0) + 1
            db.session.commit()
            return jsonify({'success': True, 'data': {'liked': True, 'like_count': task.like_count}})
    except Exception as e:
        db.session.rollback()
        print(f"点赞操作失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@task_bp.route('/tasks/<int:task_id>/likes', methods=['GET'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def get_task_likes(task_id):
    """获取点赞该任务的用户列表"""
    try:
        from app.models.employee import Employee
        likes = TaskLike.query.filter_by(task_id=task_id).order_by(TaskLike.created_at.desc()).all()
        users = []
        for like in likes:
            emp = Employee.query.filter_by(emp_id=like.user_id).first()
            users.append({
                'user_id': like.user_id,
                'name': emp.name if emp else like.user_id,
            })
        return jsonify({'success': True, 'data': users})
    except Exception as e:
        print(f"获取点赞列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 可见性
# ============================================================

@task_bp.route('/tasks/<int:task_id>/visibility', methods=['PUT'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def update_visibility(task_id):
    """设置任务可见性（管理员操作）

    请求体：
        visibilities: [
            {"visibility_type": "role", "visibility_value": "sales"},
            {"visibility_type": "employee", "visibility_value": "E001"},
            ...
        ]

    说明：
        - visibilities 为空数组 → 重置为"仅创建人 + 管理员可见"（默认）
        - 传具体列表 → 先清空再写入
    """
    try:
        user_role = get_user_role_from_token() or ''
        if not _is_admin(user_role):
            return jsonify({'success': False, 'message': '仅管理员可设置可见性'}), 403

        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        data = request.get_json() or {}
        vis_list = data.get('visibilities', [])

        # 清空旧的
        TaskVisibility.query.filter_by(task_id=task_id).delete()

        # 写入新的
        for v in vis_list:
            vtype = v.get('visibility_type')
            vval = (v.get('visibility_value') or '').strip()
            if vtype in ('role', 'employee') and vval:
                db.session.add(TaskVisibility(
                    task_id=task_id,
                    visibility_type=vtype,
                    visibility_value=vval,
                ))

        task.updated_at = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'data': task.to_dict()})
    except Exception as e:
        db.session.rollback()
        print(f"更新可见性失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 底色
# ============================================================

@task_bp.route('/tasks/<int:task_id>/background', methods=['PUT'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def update_background(task_id):
    """设置任务自定义底色（仅作者或管理员）

    请求体：{"background_color": "#ff5500" | ""}
    """
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''
        if not _is_admin(user_role) and task.author_id != user_id:
            return jsonify({'success': False, 'message': '无权限操作'}), 403

        data = request.get_json() or {}
        color = (data.get('background_color') or '').strip() or None
        task.background_color = color
        task.updated_at = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'data': task.to_dict()})
    except Exception as e:
        db.session.rollback()
        print(f"更新底色失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 修改历史
# ============================================================

@task_bp.route('/tasks/<int:task_id>/history', methods=['GET'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def get_history(task_id):
    """获取任务修改历史（仅管理员）"""
    try:
        user_role = get_user_role_from_token() or ''
        if not _is_admin(user_role):
            return jsonify({'success': False, 'message': '仅管理员可查看历史'}), 403

        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        histories = TaskHistory.query.filter_by(task_id=task_id)\
            .order_by(TaskHistory.modified_at.desc()).all()
        return jsonify({
            'success': True,
            'data': {
                'current': task.to_dict(),
                'history': [h.to_dict(include_snapshot=True) for h in histories]
            }
        })
    except Exception as e:
        print(f"获取历史失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 通知
# ============================================================

@task_bp.route('/tasks/notifications', methods=['GET'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def get_notifications():
    """获取未读通知（仅返回当前用户可见卡片内的留言和点赞）

    说明：
        - 通知范围 = 当前用户可见的卡片范围内
        - 通知项 = 在用户可见卡片中、来自其他人的留言 / 点赞
        - 这里"未读"=self从未点击"清除"，简化实现：返回全部通知项
          （删除/状态切换由前端控制，已读语义由前端维护）
    """
    try:
        user_id = get_user_id_from_token() or ''
        user_role = get_user_role_from_token() or ''

        if not user_id:
            return jsonify({'success': True, 'data': {
                'comments': [], 'likes': [], 'unread_count': 0
            }})

        # 取所有可见任务
        tasks_query = _build_task_subquery(user_role, user_id)
        visible_task_ids = [t.id for t in tasks_query.all()]

        if not visible_task_ids:
            return jsonify({'success': True, 'data': {
                'comments': [], 'likes': [], 'unread_count': 0
            }})

        # 来自其他人的留言（未删除）
        comments = TaskComment.query.filter(
            TaskComment.task_id.in_(visible_task_ids),
            TaskComment.is_deleted == 0,
            TaskComment.author_id != user_id
        ).order_by(TaskComment.created_at.desc()).limit(50).all()

        # 来自其他人的点赞
        likes = TaskLike.query.filter(
            TaskLike.task_id.in_(visible_task_ids),
            TaskLike.user_id != user_id
        ).order_by(TaskLike.created_at.desc()).limit(50).all()

        # 关联任务信息
        from app.models.employee import Employee
        task_id_set = set([c.task_id for c in comments] + [l.task_id for l in likes])
        task_map = {}
        if task_id_set:
            for t in Task.query.filter(Task.id.in_(task_id_set)).all():
                task_map[t.id] = t.to_dict()

        comment_items = []
        for c in comments:
            t = task_map.get(c.task_id)
            comment_items.append({
                'id': c.id,
                'task_id': c.task_id,
                'author_name': c.author_name,
                'author_id': c.author_id,
                'content': c.content,
                'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S') if c.created_at else None,
                'task_content_preview': (t['content'][:50] + '...') if t and len(t['content']) > 50 else (t['content'] if t else ''),
            })

        like_items = []
        for l in likes:
            t = task_map.get(l.task_id)
            emp = Employee.query.filter_by(emp_id=l.user_id).first()
            like_items.append({
                'task_id': l.task_id,
                'user_id': l.user_id,
                'name': emp.name if emp else l.user_id,
                'created_at': l.created_at.strftime('%Y-%m-%d %H:%M:%S') if l.created_at else None,
                'task_content_preview': (t['content'][:50] + '...') if t and len(t['content']) > 50 else (t['content'] if t else ''),
            })

        return jsonify({
            'success': True,
            'data': {
                'comments': comment_items,
                'likes': like_items,
                'unread_count': len(comment_items) + len(like_items),
            }
        })
    except Exception as e:
        print(f"获取通知失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@task_bp.route('/tasks/notifications/clear', methods=['POST'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def clear_notifications():
    """清除全部通知（前端语义标记，后端无副作用）"""
    return jsonify({'success': True, 'message': '通知已清除'})


# ============================================================
# 可见性辅助数据（供前端下拉选择）
# ============================================================

@task_bp.route('/admin/all-roles', methods=['GET'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def get_all_roles():
    """获取所有 SimpleRole 列表（仅管理员可见，用于可见性下拉）"""
    try:
        user_role = get_user_role_from_token() or ''
        if not _is_admin(user_role):
            return jsonify({'success': False, 'message': '仅管理员可访问'}), 403
        from app.models.simple_permission import SimpleRole
        roles = SimpleRole.query.order_by(SimpleRole.id.asc()).all()
        return jsonify({'success': True, 'data': [r.to_dict() for r in roles]})
    except Exception as e:
        print(f"获取角色列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@task_bp.route('/admin/all-employees', methods=['GET'])
@route_permission(ROUTE_TASK_TRACK_MANAGE)
def get_all_employees():
    """获取所有 Employee 列表（仅管理员可见，用于可见性下拉）

    返回字段：emp_id, name（最小化数据）
    """
    try:
        user_role = get_user_role_from_token() or ''
        if not _is_admin(user_role):
            return jsonify({'success': False, 'message': '仅管理员可访问'}), 403
        from app.models.employee import Employee
        emps = Employee.query.order_by(Employee.emp_id.asc()).all()
        return jsonify({
            'success': True,
            'data': [{'emp_id': e.emp_id, 'name': e.name} for e in emps]
        })
    except Exception as e:
        print(f"获取员工列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500