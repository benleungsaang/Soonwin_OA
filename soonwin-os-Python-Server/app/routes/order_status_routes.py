from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from extensions import db
from app.models.order import Order
from app.models.order_status import OrderStatus, OrderStatusLog, StatusTask, TaskMediaFile
from app.utils.upload_utils import allowed_file, get_file_type
from app.utils.auth_utils import require_module_permission
from app.constants.permission_constants import MODULE_ORDER_STATUS_MANAGE

order_status_bp = Blueprint('order_status_bp', __name__)

# 上传文件配置
UPLOAD_FOLDER = 'assets/OrderStatus'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@order_status_bp.route('/order-status-orders', methods=['GET'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "view")
def get_order_status_orders():
    """获取需要进度管理的订单列表"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 构建查询
        query = Order.query

        # 计算总数
        total = query.count()

        # 应用分页
        orders = query.order_by(Order.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 过滤敏感字段，仅返回基础数据
        result = []
        for order in orders:
            # 获取或创建相关的进度记录
            status_record = OrderStatus.query.filter_by(order_id=order.id).first()

            order_data = {
                'id': order.id,
                'contract_no': order.contract_no,
                'order_no': order.order_no,
                'machine_no': order.machine_no,
                'machine_name': order.machine_name,
                'machine_model': order.machine_model,
                'machine_count': order.machine_count,
                'order_time': order.order_time.strftime('%Y-%m-%d') if order.order_time else None,
                'ship_time': order.ship_time.strftime('%Y-%m-%d') if order.ship_time else None,
                'status_id': status_record.id if status_record else None,
                'current_status': status_record.current_status if status_record else None,
                'current_status_time': status_record.current_status_time.strftime('%Y-%m-%d') if status_record and status_record.current_status_time else None,
                'progress_percent': status_record.progress_percent if status_record else 0,
                'total_tasks': status_record.total_tasks if status_record else 0,
                'completed_tasks': status_record.completed_tasks if status_record else 0
            }
            result.append(order_data)

        return jsonify({
            'code': 200,
            'data': {
                'list': result,
                'total': total,
                'page': page,
                'size': size
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取订单列表失败: {str(e)}'})


@order_status_bp.route('/order-status', methods=['GET'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "view")
def get_order_status_by_order_no():
    """根据订单号获取进度记录"""
    try:
        order_no = request.args.get('order_no')
        order_id = request.args.get('order_id')  # 添加基于订单ID的查询支持

        order = None
        if order_no:
            # 先尝试根据订单号查找订单
            order = Order.query.filter_by(order_no=order_no).first()
        elif order_id:
            # 如果没有订单号，尝试根据订单ID查找
            try:
                order_id = int(order_id)
                order = Order.query.get(order_id)
            except ValueError:
                return jsonify({'code': 400, 'msg': '订单ID格式错误'})

        if not order:
            if order_no:
                return jsonify({'code': 404, 'msg': '订单不存在'})
            elif order_id:
                return jsonify({'code': 404, 'msg': '订单不存在'})
            else:
                return jsonify({'code': 400, 'msg': '必须提供订单号或订单ID'})

        # 查找或创建相关的进度记录
        status_record = OrderStatus.query.filter_by(order_id=order.id).first()
        if not status_record:
            # 如果不存在，创建一个新的进度记录
            status_record = OrderStatus(
                order_id=order.id,
                remarks='自动创建的进度记录'
            )
            db.session.add(status_record)
            db.session.commit()

            # 调用同步方法确保任务数等统计信息正确
            status_record.sync_progress()
            db.session.commit()

        # 获取关联的任务项
        tasks = StatusTask.query.filter_by(order_status_id=status_record.id).order_by(StatusTask.sort).all()

        # 获取关联的状态日志
        status_logs = OrderStatusLog.query.filter_by(order_status_id=status_record.id).all()

        # 构建返回数据
        result = status_record.to_dict()

        # 添加状态日志数据
        result['status_logs'] = [log.to_dict() for log in status_logs]

        # 添加任务项数据
        result['status'] = []

        # 按类别分组任务项
        categories = {}
        for task in tasks:
            if task.status_log_id not in categories:
                # 找到对应的状态日志
                status_log = next((log for log in status_logs if log.id == task.status_log_id), None)
                category_data = {
                    'status_log_id': task.status_log_id,  # 使用状态日志ID作为类别ID
                    'category': status_log.status if status_log else '未分类',
                    'item_type': 'category',
                    'tasks': []
                }
                categories[task.status_log_id] = category_data
                result['status'].append(category_data)

            # 添加子任务
            task_data = {
                'task_id': task.id,
                'parent_id': task.status_log_id,
                'category': status_log.status if status_log else '未分类',
                'name': task.name,
                'item_type': 'sub',
                'is_completed': task.is_completed,
                'description': task.description,
                'sort_order': task.sort,
                'create_time': task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
                'update_time': task.update_time.strftime('%Y-%m-%d %H:%M:%S') if task.update_time else None,
                # 新增多媒体文件信息
                'media_files': [mf.to_dict() for mf in task.media_files if not mf.is_deleted],
                'images': [mf.to_dict() for mf in task.media_files if mf.file_type == 'image' and not mf.is_deleted],
                'videos': [mf.to_dict() for mf in task.media_files if mf.file_type == 'video' and not mf.is_deleted],
                'image_count': len([mf for mf in task.media_files if mf.file_type == 'image' and not mf.is_deleted]),
                'video_count': len([mf for mf in task.media_files if mf.file_type == 'video' and not mf.is_deleted])
            }
            categories[task.status_log_id]['tasks'].append(task_data)

        return jsonify({'code': 200, 'data': result})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取订单进度记录失败: {str(e)}'})


@order_status_bp.route('/order-status', methods=['POST'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "edit")
def create_order_status():
    """创建订单进度记录"""
    try:
        data = request.json
        order_id = data.get('order_id')
        remarks = data.get('remarks', '')

        if not order_id:
            return jsonify({'code': 400, 'msg': '订单ID不能为空'})

        # 检查订单是否存在
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'})

        # 检查是否已存在该订单的进度记录
        existing_status = OrderStatus.query.filter_by(order_id=order_id).first()
        if existing_status:
            return jsonify({'code': 400, 'msg': '该订单的进度记录已存在'})

        # 创建新的进度记录
        new_status = OrderStatus(
            order_id=order_id,
            remarks=remarks
        )
        db.session.add(new_status)
        db.session.commit()

        # 调用同步方法确保任务数等统计信息正确
        new_status.sync_progress()
        db.session.commit()

        return jsonify({'code': 200, 'msg': '订单进度记录创建成功', 'data': new_status.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'创建订单进度记录失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>', methods=['GET'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "view")
def get_order_status(status_id):
    """获取订单进度详情"""
    try:
        # 获取进度记录
        status_record = OrderStatus.query.get(status_id)
        if not status_record:
            return jsonify({'code': 404, 'msg': '进度记录不存在'})

        # 获取关联的任务项
        tasks = StatusTask.query.filter_by(order_status_id=status_id).order_by(StatusTask.sort).all()

        # 获取关联的状态日志
        status_logs = OrderStatusLog.query.filter_by(order_status_id=status_id).all()

        # 构建返回数据
        result = status_record.to_dict()

        # 添加任务项数据
        result['status'] = []

        # 按类别分组任务项
        categories = {}
        for task in tasks:
            if task.status_log_id not in categories:
                # 找到对应的状态日志
                status_log = next((log for log in status_logs if log.id == task.status_log_id), None)
                category_data = {
                    'status_log_id': task.status_log_id,  # 使用状态日志ID作为类别ID
                    'category': status_log.status if status_log else '未分类',
                    'item_type': 'category',
                    'tasks': []
                }
                categories[task.status_log_id] = category_data
                result['status'].append(category_data)

            # 添加子任务
            task_data = {
                'task_id': task.id,
                'parent_id': task.status_log_id,
                'category': status_log.status if status_log else '未分类',
                'name': task.name,
                'item_type': 'sub',
                'is_completed': task.is_completed,
                'description': task.description,
                'sort_order': task.sort,
                'create_time': task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
                'update_time': task.update_time.strftime('%Y-%m-%d %H:%M:%S') if task.update_time else None,
                # 新增多媒体文件信息
                'media_files': [mf.to_dict() for mf in task.media_files if not mf.is_deleted],
                'images': [mf.to_dict() for mf in task.media_files if mf.file_type == 'image' and not mf.is_deleted],
                'videos': [mf.to_dict() for mf in task.media_files if mf.file_type == 'video' and not mf.is_deleted],
                'image_count': len([mf for mf in task.media_files if mf.file_type == 'image' and not mf.is_deleted]),
                'video_count': len([mf for mf in task.media_files if mf.file_type == 'video' and not mf.is_deleted])
            }
            categories[task.status_log_id]['tasks'].append(task_data)

        return jsonify({'code': 200, 'data': result})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取订单进度详情失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>', methods=['PUT'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "edit")
def update_order_status(status_id):
    """更新订单进度记录"""
    try:
        status_record = OrderStatus.query.get(status_id)
        if not status_record:
            return jsonify({'code': 404, 'msg': '进度记录不存在'})

        data = request.json

        # 更新备注
        if 'remarks' in data:
            status_record.remarks = data['remarks']

        # 更新当前状态
        if 'current_status' in data:
            status_record.current_status = data['current_status']
            status_record.current_status_time = datetime.now()

        status_record.update_time = datetime.now()
        db.session.commit()

        # 同步进度
        status_record.sync_progress()

        return jsonify({'code': 200, 'msg': '订单进度记录更新成功', 'data': status_record.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'更新订单进度记录失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>/status', methods=['PUT'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "edit")
def update_order_status_status(status_id):
    """更新订单状态"""
    try:
        status_record = OrderStatus.query.get(status_id)
        if not status_record:
            return jsonify({'code': 404, 'msg': '进度记录不存在'})

        data = request.json
        new_status = data.get('status')
        status_time_str = data.get('status_time')

        if new_status is None:
            return jsonify({'code': 400, 'msg': '状态值不能为空'})

        # 更新当前状态
        status_record.current_status = new_status
        if status_time_str:
            status_record.current_status_time = datetime.strptime(status_time_str, '%Y-%m-%d')
        else:
            status_record.current_status_time = datetime.now()

        status_record.update_time = datetime.now()
        db.session.commit()

        return jsonify({'code': 200, 'msg': '订单状态更新成功', 'data': status_record.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'更新订单状态失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>/clear', methods=['POST'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "edit")
def clear_order_status_tasks(status_id):
    """清空订单进度记录的所有任务项"""
    try:
        status_record = OrderStatus.query.get(status_id)
        if not status_record:
            return jsonify({'code': 404, 'msg': '进度记录不存在'})

        # 获取所有任务项
        tasks = StatusTask.query.filter_by(order_status_id=status_id).all()

        # 记录要删除的项目数
        total_deleted = len(tasks)

        # 删除所有任务项
        for task in tasks:
            db.session.delete(task)

        # 重置进度统计
        status_record.total_tasks = 0
        status_record.completed_tasks = 0
        status_record.progress_percent = 0
        status_record.progress_status = 'pending'

        status_record.update_time = datetime.now()
        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': '任务项清空成功',
            'data': {'total_deleted': total_deleted}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'清空任务项失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>/tasks/batch', methods=['POST'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "edit")
def batch_update_status_tasks(status_id):
    """批量更新任务项"""
    try:
        status_record = OrderStatus.query.get(status_id)
        if not status_record:
            return jsonify({'code': 404, 'msg': '进度记录不存在'})

        data = request.json
        tasks_data = data.get('tasks', [])

        created_tasks = []
        updated_tasks = []
        deleted_tasks = []

        for task_data in tasks_data:
            task_id = task_data.get('id')

            if task_data.get('_toBeDeleted'):
                # 删除标记的项目
                task = StatusTask.query.get(task_id)
                if task and task.order_status_id == status_id:
                    db.session.delete(task)
                    deleted_tasks.append(task.to_dict())
            elif task_data.get('is_local_new'):
                # 创建新项目
                new_task = StatusTask(
                    order_status_id=status_id,
                    status_log_id=task_data.get('status_log_id', 1),  # 默认使用第一个状态日志
                    category=task_data.get('category', ''),
                    name=task_data.get('name', ''),
                    is_completed=task_data.get('is_completed', False),
                    description=task_data.get('description'),
                    sort=task_data.get('sort', 0)
                )
                db.session.add(new_task)
                db.session.flush()  # 获取ID但不提交
                created_tasks.append(new_task.to_dict())
            else:
                # 更新现有项目
                task = StatusTask.query.get(task_id)
                if task and task.order_status_id == status_id:
                    task.category = task_data.get('category', task.category)
                    task.name = task_data.get('name', task.name)
                    task.is_completed = task_data.get('is_completed', task.is_completed)
                    task.description = task_data.get('description', task.description)
                    task.sort = task_data.get('sort', task.sort)
                    task.update_time = datetime.now()
                    updated_tasks.append(task.to_dict())

        db.session.commit()

        # 同步进度
        status_record.sync_progress()

        return jsonify({
            'code': 200,
            'msg': '批量更新任务项成功',
            'data': {
                'created_tasks': [task for task in created_tasks],
                'updated_tasks': [task for task in updated_tasks],
                'deleted_tasks': [task for task in deleted_tasks],
                'progress': status_record.progress_percent,
                'completed_tasks': status_record.completed_tasks,
                'total_tasks': status_record.total_tasks
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'批量更新任务项失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>/tasks', methods=['POST'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "edit")
def create_status_task(status_id):
    """创建任务项"""
    try:
        status_record = OrderStatus.query.get(status_id)
        if not status_record:
            return jsonify({'code': 404, 'msg': '进度记录不存在'})

        data = request.json
        required_fields = ['name', 'status_log_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'code': 400, 'msg': f'缺少必要字段: {field}'})

        new_task = StatusTask(
            order_status_id=status_id,
            status_log_id=data['status_log_id'],
            category=data.get('category', '未分类'),
            name=data['name'],
            is_completed=data.get('is_completed', False),
            description=data.get('description'),
            sort=data.get('sort', 0)
        )

        db.session.add(new_task)
        db.session.commit()

        # 同步进度
        status_record.sync_progress()

        return jsonify({
            'code': 200,
            'msg': '任务项创建成功',
            'data': new_task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'创建任务项失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>/tasks/<int:task_id>', methods=['PUT'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "edit")
def update_status_task(status_id, task_id):
    """更新任务项"""
    try:
        task = StatusTask.query.filter_by(id=task_id, order_status_id=status_id).first()
        if not task:
            return jsonify({'code': 404, 'msg': '任务项不存在或不属于该进度记录'})

        data = request.json

        # 更新字段
        if 'category' in data:
            task.category = data['category']
        if 'name' in data:
            task.name = data['name']
        if 'is_completed' in data:
            task.is_completed = data['is_completed']
        if 'description' in data:
            task.description = data['description']
        if 'sort' in data:
            task.sort = data['sort']

        task.update_time = datetime.now()
        db.session.commit()

        # 同步进度
        status_record = OrderStatus.query.get(status_id)
        if status_record:
            status_record.sync_progress()

        return jsonify({
            'code': 200,
            'msg': '任务项更新成功',
            'data': task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'更新任务项失败: {str(e)}'})








@order_status_bp.route('/order-status/<int:status_id>/tasks/<int:task_id>/media', methods=['DELETE'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "delete")
def delete_status_task_media(status_id, task_id):
    """删除任务项的媒体文件"""
    try:
        task = StatusTask.query.filter_by(id=task_id, order_status_id=status_id).first()
        if not task:
            return jsonify({'code': 404, 'msg': '任务项不存在或不属于该进度记录'})

        media_file_id = request.json.get('media_file_id') if request.json else None
        if not media_file_id:
            return jsonify({'code': 400, 'msg': '缺少媒体文件ID'})

        # 根据ID查找媒体文件记录
        media_file = TaskMediaFile.query.filter_by(id=media_file_id, status_task_id=task_id).first()
        if not media_file:
            return jsonify({'code': 404, 'msg': '媒体文件不存在或不属于该任务'})

        # 软删除媒体文件记录
        media_file.is_deleted = True
        task.update_time = datetime.now()
        db.session.commit()

        # 删除实际文件
        try:
            if media_file.file_path and os.path.exists(media_file.file_path.lstrip('/')):
                os.remove(media_file.file_path.lstrip('/'))

            # 如果有缩略图，也删除它
            if media_file.thumb_path and os.path.exists(media_file.thumb_path.lstrip('/')):
                os.remove(media_file.thumb_path.lstrip('/'))
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            pass  # 文件删除失败不影响记录更新

        return jsonify({'code': 200, 'msg': '媒体文件删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'删除媒体文件失败: {str(e)}'})


@order_status_bp.route('/order-status-logs/<int:log_id>', methods=['PUT'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "edit")
def update_order_status_log(log_id):
    """更新订单状态日志"""
    try:
        status_log = OrderStatusLog.query.get(log_id)
        if not status_log:
            return jsonify({'code': 404, 'msg': '订单状态日志不存在'})

        data = request.json
        # 更新可修改的字段
        if 'status' in data:
            status_log.status = data['status']
        if 'start_time' in data:
            status_log.start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S') if data['start_time'] else None
        if 'expected_completion_time' in data:
            status_log.expected_completion_time = datetime.strptime(data['expected_completion_time'], '%Y-%m-%d %H:%M:%S') if data['expected_completion_time'] else None
        if 'actual_completion_time' in data:
            status_log.actual_completion_time = datetime.strptime(data['actual_completion_time'], '%Y-%m-%d %H:%M:%S') if data['actual_completion_time'] else None

        status_log.order_status.update_time = datetime.now()
        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': '订单状态日志更新成功',
            'data': status_log.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'更新订单状态日志失败: {str(e)}'})


@order_status_bp.route('/order-status-logs/<int:log_id>', methods=['DELETE'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "delete")
def delete_order_status_log(log_id):
    """删除订单状态日志"""
    try:
        status_log = OrderStatusLog.query.get(log_id)
        if not status_log:
            return jsonify({'code': 404, 'msg': '订单状态日志不存在'})

        # 获取关联的进度记录和订单，用于构建文件路径
        status_record = OrderStatus.query.get(status_log.order_status_id)
        if status_record:
            order = Order.query.get(status_record.order_id)
            if order and status_log:
                # 构建要删除的文件夹路径：./assets/OrderStatus/合同编号/status_log_id/
                # 使用纯ID作为文件夹名，避免名称更改影响路径
                contract_no = order.contract_no.replace('/', '_').replace('\\', '_')  # 替换路径分隔符
                status_log_folder = str(status_log.id)

                import os
                upload_dir = os.path.join(UPLOAD_FOLDER, contract_no, status_log_folder)

                # 删除整个状态日志的文件夹（如果存在）
                if os.path.exists(upload_dir):
                    import shutil
                    try:
                        shutil.rmtree(upload_dir)
                        print(f"已删除状态日志文件夹: {upload_dir}")
                    except Exception as e:
                        print(f"删除状态日志文件夹失败: {str(e)}")

        # 首先删除与该状态日志关联的所有任务项
        related_tasks = StatusTask.query.filter_by(status_log_id=log_id).all()
        for task in related_tasks:
            db.session.delete(task)

        # 删除状态日志本身
        db.session.delete(status_log)
        db.session.commit()

        # 同步进度
        status_record = OrderStatus.query.get(status_log.order_status_id)
        if status_record:
            status_record.sync_progress()

        return jsonify({'code': 200, 'msg': '订单状态日志删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'删除订单状态日志失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>/tasks/<int:task_id>', methods=['DELETE'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "delete")
def delete_task(status_id, task_id):
    """删除任务项（单独删除任务项，不是删除状态日志）"""
    try:
        task = StatusTask.query.filter_by(id=task_id, order_status_id=status_id).first()
        if not task:
            return jsonify({'code': 404, 'msg': '任务项不存在或不属于该进度记录'})

        # 获取关联的订单状态、订单和状态日志，用于构建文件路径
        status_record = OrderStatus.query.get(status_id)
        status_log = OrderStatusLog.query.get(task.status_log_id)
        if status_record:
            order = Order.query.get(status_record.order_id)
            if order and status_log:
                # 构建要删除的文件夹路径：./assets/OrderStatus/合同编号/status_log_id/task_id/
                # 使用纯ID作为文件夹名，避免名称更改影响路径
                contract_no = order.contract_no.replace('/', '_').replace('\\', '_')  # 替换路径分隔符
                status_log_folder = str(status_log.id)
                task_folder = str(task.id)

                import os
                upload_dir = os.path.join(UPLOAD_FOLDER, contract_no, status_log_folder, task_folder)

                # 删除整个任务的文件夹（如果存在）
                if os.path.exists(upload_dir):
                    import shutil
                    try:
                        shutil.rmtree(upload_dir)
                        print(f"已删除任务文件夹: {upload_dir}")
                    except Exception as e:
                        print(f"删除任务文件夹失败: {str(e)}")

        # 删除关联的媒体文件（新的TaskMediaFile表）
        media_files = TaskMediaFile.query.filter_by(status_task_id=task.id).all()
        for media_file in media_files:
            try:
                # 删除实际文件
                if media_file.file_path and os.path.exists(media_file.file_path.lstrip('/')):
                    os.remove(media_file.file_path.lstrip('/'))
                if media_file.thumb_path and os.path.exists(media_file.thumb_path.lstrip('/')):
                    os.remove(media_file.thumb_path.lstrip('/'))

                # 从数据库中删除记录
                db.session.delete(media_file)
            except Exception as e:
                # 删除文件失败不影响任务删除
                print(f"删除媒体文件失败: {str(e)}")

        # 为了兼容旧数据，仍然删除旧的路径字段（如果存在）
        # 注意：在新模型中，task.photo_path 应该不存在，但为了向后兼容保留此代码

        db.session.delete(task)
        db.session.commit()

        # 同步进度
        status_record = OrderStatus.query.get(status_id)
        if status_record:
            status_record.sync_progress()

        return jsonify({'code': 200, 'msg': '任务项删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'删除任务项失败: {str(e)}'})


@order_status_bp.route('/order-status-logs', methods=['POST'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "edit")
def create_order_status_log():
    """创建订单状态日志"""
    try:
        data = request.json
        order_status_id = data.get('order_status_id')
        status = data.get('status')
        start_time_str = data.get('start_time')
        expected_completion_time_str = data.get('expected_completion_time')

        if not order_status_id or not status:
            return jsonify({'code': 400, 'msg': '缺少必要参数: order_status_id 和 status'})

        # 检查订单状态记录是否存在
        order_status = OrderStatus.query.get(order_status_id)
        if not order_status:
            return jsonify({'code': 404, 'msg': '订单状态记录不存在'})

        # 解析时间字符串
        start_time = None
        expected_completion_time = None

        if start_time_str:
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        else:
            start_time = datetime.now()

        if expected_completion_time_str:
            expected_completion_time = datetime.strptime(expected_completion_time_str, '%Y-%m-%d %H:%M:%S')

        # 创建新的状态日志记录
        new_status_log = OrderStatusLog(
            order_status_id=order_status_id,
            status=status,
            start_time=start_time,
            expected_completion_time=expected_completion_time
        )

        db.session.add(new_status_log)
        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': '订单状态日志创建成功',
            'data': new_status_log.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'创建订单状态日志失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>/report', methods=['GET'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "view")
def get_order_status_report(status_id):
    """生成订单状态报告（目前返回JSON格式，后续可扩展为PDF等格式）"""
    try:
        # 获取进度记录
        status_record = OrderStatus.query.get(status_id)
        if not status_record:
            return jsonify({'code': 404, 'msg': '进度记录不存在'})

        # 获取关联的订单信息
        order = Order.query.get(status_record.order_id)
        if not order:
            return jsonify({'code': 404, 'msg': '关联订单不存在'})

        # 获取关联的任务项
        tasks = StatusTask.query.filter_by(order_status_id=status_id).order_by(StatusTask.sort).all()

        # 获取关联的状态日志
        status_logs = OrderStatusLog.query.filter_by(order_status_id=status_id).all()

        # 构建报告数据
        report_data = {
            'status_info': status_record.to_dict(),
            'order_info': order.to_dict(),
            'status_logs': [log.to_dict() for log in status_logs],
            'tasks': []
        }

        # 按状态日志分组任务
        for task in tasks:
            # 找到对应的状态日志对象并转换为字典
            status_log_obj = next((log for log in status_logs if log.id == task.status_log_id), None)
            task_data = {
                'id': task.id,
                'status_log_id': task.status_log_id,
                'status_log': status_log_obj.to_dict() if status_log_obj else None,  # 转换为字典
                'category': task.category,
                'name': task.name,
                'is_completed': task.is_completed,
                'description': task.description,
                'sort': task.sort,
                'create_time': task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
                'update_time': task.update_time.strftime('%Y-%m-%d %H:%M:%S') if task.update_time else None,
                # 新增多媒体文件信息
                'media_files': [mf.to_dict() for mf in task.media_files if not mf.is_deleted],
                'images': [mf.to_dict() for mf in task.media_files if mf.file_type == 'image' and not mf.is_deleted],
                'videos': [mf.to_dict() for mf in task.media_files if mf.file_type == 'video' and not mf.is_deleted],
                'image_count': len([mf for mf in task.media_files if mf.file_type == 'image' and not mf.is_deleted]),
                'video_count': len([mf for mf in task.media_files if mf.file_type == 'video' and not mf.is_deleted])
            }
            report_data['tasks'].append(task_data)

        return jsonify({
            'code': 200,
            'data': report_data,
            'msg': '订单状态报告获取成功'
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'生成订单状态报告失败: {str(e)}'})


@order_status_bp.route('/order-status-logs/batch', methods=['POST'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "edit")
def batch_create_order_status_logs():
    """批量创建订单状态日志和任务项"""
    try:
        data = request.json

        order_status_id = data.get('order_status_id')
        if not order_status_id:
            return jsonify({'code': 400, 'msg': '缺少order_status_id参数'})

        # 检查订单状态记录是否存在
        order_status = OrderStatus.query.get(order_status_id)
        if not order_status:
            return jsonify({'code': 404, 'msg': '订单状态记录不存在'})

        statuses_data = data.get('statuses', [])
        if not statuses_data:
            return jsonify({'code': 400, 'msg': '缺少statuses参数'})

        created_status_logs = []
        created_tasks = []

        # 开始批量创建
        for status_data in statuses_data:
            status_name = status_data.get('status')
            if not status_name:
                continue  # 跳过无效数据

            # 创建状态日志
            new_status_log = OrderStatusLog(
                order_status_id=order_status_id,
                status=status_name,
                start_time=datetime.now()
            )
            db.session.add(new_status_log)
            db.session.flush()  # 获取ID但不提交

            # 重新查询以确保获取到完整的数据（包括ID）
            created_status_logs.append(OrderStatusLog.query.get(new_status_log.id).to_dict())

            # 创建关联的任务项
            tasks_data = status_data.get('tasks', [])
            for task_name in tasks_data:
                if not task_name.strip():
                    continue  # 跳过空任务名

                new_task = StatusTask(
                    order_status_id=order_status_id,
                    status_log_id=new_status_log.id,
                    category=status_name,  # 使用状态名作为分类
                    name=task_name.strip(),
                    is_completed=False,
                    description=f'任务: {task_name.strip()}',
                    sort=0
                )
                db.session.add(new_task)
                db.session.flush()  # 获取ID但不提交

                # 重新查询以确保获取到完整的数据（包括ID）
                created_tasks.append(StatusTask.query.get(new_task.id).to_dict())

        # 提交所有更改
        db.session.commit()

        # 同步进度
        order_status.sync_progress()
        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': f'批量创建成功: {len(created_status_logs)} 个状态日志, {len(created_tasks)} 个任务',
            'data': {
                'created_status_logs': created_status_logs,
                'created_tasks': created_tasks,
                'progress': order_status.progress_percent,
                'total_tasks': order_status.total_tasks,
                'completed_tasks': order_status.completed_tasks
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'批量创建失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>/clear-all', methods=['POST'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "delete")
def clear_all_order_status_data(status_id):
    """清空订单进度记录的所有数据（包括状态日志、任务项及关联的文件）"""
    try:
        status_record = OrderStatus.query.get(status_id)
        if not status_record:
            return jsonify({'code': 404, 'msg': '进度记录不存在'})

        # 获取关联的订单，用于构建文件路径
        order = Order.query.get(status_record.order_id)
        if not order:
            return jsonify({'code': 404, 'msg': '关联订单不存在'})

        # 获取所有任务项
        tasks = StatusTask.query.filter_by(order_status_id=status_id).all()

        # 获取所有状态日志
        status_logs = OrderStatusLog.query.filter_by(order_status_id=status_id).all()

        # 删除所有关联的文件和文件夹
        import os
        import shutil
        from extensions import db

        # 构建基础上传路径
        UPLOAD_FOLDER = 'assets/OrderStatus'

        # 删除每个任务项的文件夹
        for task in tasks:
            status_log = next((log for log in status_logs if log.id == task.status_log_id), None)
            if status_log and order:
                # 构建任务文件夹路径：./assets/OrderStatus/合同编号/status_log_id/task_id/
                contract_no = order.contract_no.replace('/', '_').replace('\\', '_')
                status_log_folder = str(status_log.id)
                task_folder = str(task.id)

                task_upload_dir = os.path.join(UPLOAD_FOLDER, contract_no, status_log_folder, task_folder)

                # 删除任务文件夹（如果存在）
                if os.path.exists(task_upload_dir):
                    try:
                        shutil.rmtree(task_upload_dir)
                        print(f"已删除任务文件夹: {task_upload_dir}")
                    except Exception as e:
                        print(f"删除任务文件夹失败: {str(e)}")

        # 删除每个状态日志的文件夹（可能包含任务文件夹）
        for status_log in status_logs:
            if order:
                # 构建状态日志文件夹路径：./assets/OrderStatus/合同编号/status_log_id/
                contract_no = order.contract_no.replace('/', '_').replace('\\', '_')
                status_log_folder = str(status_log.id)

                status_log_upload_dir = os.path.join(UPLOAD_FOLDER, contract_no, status_log_folder)

                # 删除状态日志文件夹（如果存在）
                if os.path.exists(status_log_upload_dir):
                    try:
                        shutil.rmtree(status_log_upload_dir)
                        print(f"已删除状态日志文件夹: {status_log_upload_dir}")
                    except Exception as e:
                        print(f"删除状态日志文件夹失败: {str(e)}")

        # 记录要删除的数量
        tasks_count = len(tasks)
        status_logs_count = len(status_logs)

        # 删除所有任务项
        for task in tasks:
            db.session.delete(task)

        # 删除所有状态日志
        for status_log in status_logs:
            db.session.delete(status_log)

        # 重置进度统计
        status_record.total_tasks = 0
        status_record.completed_tasks = 0
        status_record.progress_percent = 0
        status_record.progress_status = 'pending'
        status_record.current_status = 1  # 重置为初始状态
        status_record.current_status_time = None

        status_record.update_time = datetime.now()
        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': f'清空成功: {status_logs_count} 个状态日志, {tasks_count} 个任务项及关联文件',
            'data': {
                'status_logs_deleted': status_logs_count,
                'tasks_deleted': tasks_count
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'清空数据失败: {str(e)}'})


@order_status_bp.route('/order-status/upload-multiple-images', methods=['POST'])
@require_module_permission(MODULE_ORDER_STATUS_MANAGE, "edit")
def upload_multiple_images():
    """批量上传任务项媒体文件"""
    try:
        # 检查是否包含文件
        if 'files' not in request.files:
            return jsonify({'code': 400, 'msg': '未上传文件'})

        files = request.files.getlist('files')
        task_id = request.form.get('task_id')

        if not task_id:
            return jsonify({'code': 400, 'msg': '任务ID不能为空'})

        if not files or len(files) == 0:
            return jsonify({'code': 400, 'msg': '请至少上传一个文件'})

        # 检查任务项是否存在
        task = StatusTask.query.filter_by(id=task_id).first()
        if not task:
            return jsonify({'code': 404, 'msg': '任务项不存在'})

        # 获取关联的订单状态记录、状态日志和订单
        status_record = OrderStatus.query.get(task.order_status_id)
        status_log = OrderStatusLog.query.get(task.status_log_id)
        order = Order.query.get(status_record.order_id) if status_record else None

        if not status_record or not status_log or not order:
            return jsonify({'code': 404, 'msg': '关联的订单信息不完整'})

        # 构建上传路径：./assets/OrderStatus/合同编号_下单日期/
        # 使用合同编号和下单日期作为文件夹名
        contract_no = order.contract_no.replace('/', '_').replace('\\', '_')  # 替换路径分隔符
        order_date = order.order_time.strftime('%Y%m%d') if order.order_time else datetime.now().strftime('%Y%m%d')
        order_folder = f"{contract_no}_{order_date}"

        upload_dir = os.path.join(UPLOAD_FOLDER, order_folder)
        os.makedirs(upload_dir, exist_ok=True)

        uploaded_media_files = []

        # 逐个处理上传的文件
        for file in files:
            if not allowed_file(file.filename):
                return jsonify({'code': 400, 'msg': f'不允许的文件类型: {file.filename}'})

            # 根据需求，文件名使用：task.category_task.name+上传时标题+时间缀
            # 使用安全文件名确保兼容性
            safe_filename = secure_filename(file.filename)
            name, ext = os.path.splitext(safe_filename)
            
            # 根据任务的category和name生成文件前缀
            category_prefix = task.category.replace('/', '_').replace('\\', '_').replace(' ', '_') if task.category else 'default'
            name_prefix = task.name.replace('/', '_').replace('\\', '_').replace(' ', '_') if task.name else 'default'
            
            # 确保文件名不会过长
            if len(category_prefix) > 20:
                category_prefix = category_prefix[:20]
            if len(name_prefix) > 20:
                name_prefix = name_prefix[:20]
            
            # 生成新的文件名 - 使用当前时间戳作为文件名后缀
            file_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{category_prefix}_{name_prefix}_{file_timestamp}{ext}"

            # 保存文件
            file_path = os.path.join(upload_dir, new_filename)
            file.save(file_path)

            # 确定文件类型
            file_type = get_file_type(file.filename)

            # 生成相对路径URL
            relative_path = os.path.relpath(file_path, UPLOAD_FOLDER).replace('\\', '/')
            file_url = f"/assets/OrderStatus/{relative_path}"

            # 生成缩略图 - 对图片和视频都生成缩略图
            thumb_url = None
            if file_type == 'image':
                try:
                    from PIL import Image
                    # 打开原始图片
                    img = Image.open(file_path)

                    # 生成缩略图尺寸（保持宽高比）
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)

                    # 生成缩略图文件名
                    thumb_filename = f"thumb_{new_filename}"
                    thumb_path = os.path.join(upload_dir, thumb_filename)

                    # 保存缩略图
                    img.save(thumb_path, optimize=True, quality=70)

                    # 生成缩略图的相对路径URL
                    thumb_relative_path = os.path.relpath(thumb_path, UPLOAD_FOLDER).replace('\\', '/')
                    thumb_url = f"/assets/OrderStatus/{thumb_relative_path}"
                except Exception as e:
                    print(f"生成图片缩略图失败: {str(e)}")
                    # 如果缩略图生成失败，继续处理原图
            elif file_type == 'video':
                # 对于视频，使用upload_utils.py中的视频处理功能生成缩略图
                try:
                    from app.utils.upload_utils import process_video_with_variants
                    # 获取文件前缀（不含扩展名）
                    file_prefix = os.path.splitext(new_filename)[0]
                    # 生成缩略图
                    result = process_video_with_variants(file_path, UPLOAD_FOLDER, file_prefix, ext.lower())
                    
                    if result['paths'].get('thumbnail'):
                        # 缩略图路径是相对于UPLOAD_FOLDER的，需要构建完整URL
                        thumb_relative_path = result['paths']['thumbnail']
                        thumb_url = f"/assets/OrderStatus/{thumb_relative_path}"
                except Exception as e:
                    print(f"生成视频缩略图失败: {str(e)}")
                    # 视频缩略图生成失败不影响上传

            # 创建媒体文件记录
            media_file = TaskMediaFile(
                status_task_id=task.id,
                file_type=file_type,
                file_format=ext[1:] if ext else None,  # 去除点号的扩展名
                file_size=os.path.getsize(file_path),
                file_path=file_url,
                thumb_path=thumb_url,
                file_name=new_filename,  # 使用新生成的文件名
                sort=0  # 新上传的文件默认排序为0
            )
            db.session.add(media_file)
            uploaded_media_files.append(media_file)

        task.update_time = datetime.now()
        db.session.commit()

        # 返回上传的媒体文件信息
        uploaded_file_info = []
        for media_file in uploaded_media_files:
            uploaded_file_info.append({
                'id': media_file.id,
                'file_type': media_file.file_type,
                'file_path': media_file.file_path,
                'thumb_path': media_file.thumb_path,
                'file_name': media_file.file_name,
                'file_size': media_file.file_size,
                'upload_time': media_file.upload_time.isoformat() if media_file.upload_time else None
            })

        return jsonify({
            'code': 200,
            'msg': f'成功上传 {len(files)} 个媒体文件',
            'data': {
                'media_files': uploaded_file_info,
                'file_count': len(files),
                # 添加任务信息，用于前端更新本地状态
                'task_id': task.id,
                'status_log_id': task.status_log_id,
                'order_status_id': task.order_status_id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'批量上传失败: {str(e)}'})