from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from extensions import db
from app.models.order import Order
from app.models.order_status import OrderStatus, OrderStatusLog, StatusTask
from app.utils.upload_utils import allowed_file, get_file_type

order_status_bp = Blueprint('order_status_bp', __name__)

# 上传文件配置
UPLOAD_FOLDER = 'assets/OrderStatus'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@order_status_bp.route('/order-status-orders', methods=['GET'])
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
        result['tasks'] = []

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
                    'children': []
                }
                categories[task.status_log_id] = category_data
                result['tasks'].append(category_data)

            # 添加子任务
            task_data = {
                'task_id': task.id,
                'parent_id': task.status_log_id,
                'category': status_log.status if status_log else '未分类',
                'name': task.name,
                'item_type': 'sub',
                'is_completed': task.is_completed,
                'photo_path': task.photo_path,
                'thumb_photo_path': task.thumb_photo_path,
                'description': task.description,
                'sort_order': task.sort,
                'create_time': task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
                'update_time': task.update_time.strftime('%Y-%m-%d %H:%M:%S') if task.update_time else None
            }
            categories[task.status_log_id]['children'].append(task_data)

        return jsonify({'code': 200, 'data': result})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取订单进度记录失败: {str(e)}'})


@order_status_bp.route('/order-status', methods=['POST'])
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
        result['tasks'] = []

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
                    'children': []
                }
                categories[task.status_log_id] = category_data
                result['tasks'].append(category_data)

            # 添加子任务
            task_data = {
                'task_id': task.id,
                'parent_id': task.status_log_id,
                'category': status_log.status if status_log else '未分类',
                'name': task.name,
                'item_type': 'sub',
                'is_completed': task.is_completed,
                'photo_path': task.photo_path,
                'thumb_photo_path': task.thumb_photo_path,
                'description': task.description,
                'sort_order': task.sort,
                'create_time': task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
                'update_time': task.update_time.strftime('%Y-%m-%d %H:%M:%S') if task.update_time else None
            }
            categories[task.status_log_id]['children'].append(task_data)

        return jsonify({'code': 200, 'data': result})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取订单进度详情失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>', methods=['PUT'])
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
                    photo_path=task_data.get('photo_path'),
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
                    task.photo_path = task_data.get('photo_path', task.photo_path)
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
            photo_path=data.get('photo_path'),
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
        if 'photo_path' in data:
            task.photo_path = data['photo_path']
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





@order_status_bp.route('/order-status/<int:status_id>/tasks/upload', methods=['POST'])
def upload_status_task_media(status_id):
    """上传任务项媒体文件"""
    try:
        status_record = OrderStatus.query.get(status_id)
        if not status_record:
            return jsonify({'code': 404, 'msg': '进度记录不存在'})

        if 'file' not in request.files:
            return jsonify({'code': 400, 'msg': '未上传文件'})

        file = request.files['file']
        task_id = request.form.get('task_id')

        if not task_id or file.filename == '':
            return jsonify({'code': 400, 'msg': '参数缺失'})

        if not allowed_file(file.filename):
            return jsonify({'code': 400, 'msg': '不允许的文件类型'})

        # 检查任务项是否存在
        task = StatusTask.query.filter_by(id=task_id, order_status_id=status_id).first()
        if not task:
            return jsonify({'code': 404, 'msg': '任务项不存在或不属于该进度记录'})

        # 获取关联的订单状态日志
        status_log = OrderStatusLog.query.get(task.status_log_id)
        if not status_log:
            return jsonify({'code': 404, 'msg': '关联的状态日志不存在'})

        # 获取关联的订单
        order = Order.query.get(status_record.order_id)
        if not order:
            return jsonify({'code': 404, 'msg': '关联的订单不存在'})

        # 构建上传路径：./assets/OrderStatus/合同编号/status_log_id/task_id/
        # 使用纯ID作为文件夹名，避免名称更改影响路径
        contract_no = order.contract_no.replace('/', '_').replace('\\', '_')  # 替换路径分隔符
        status_log_folder = str(status_log.id)
        task_folder = str(task.id)

        # 确保文件名安全
        safe_filename = secure_filename(file.filename)

        # 创建目录路径
        upload_dir = os.path.join(UPLOAD_FOLDER, contract_no, status_log_folder, task_folder)
        os.makedirs(upload_dir, exist_ok=True)

        # 检查该任务是否已有相同名称的文件，如果有则添加序号
        base_name, ext = os.path.splitext(safe_filename)
        counter = 1
        new_filename = safe_filename
        while os.path.exists(os.path.join(upload_dir, new_filename)):
            new_filename = f"{base_name}_{counter}{ext}"
            counter += 1

        # 保存文件
        file_path = os.path.join(upload_dir, new_filename)
        file.save(file_path)

        # 确定文件类型
        file_type = get_file_type(file.filename)

        # 生成相对路径URL
        relative_path = os.path.relpath(file_path, UPLOAD_FOLDER)
        file_url = f"/assets/OrderStatus/{relative_path}"

        # 如果是图片，生成缩略图
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
                thumb_relative_path = os.path.relpath(thumb_path, UPLOAD_FOLDER)
                thumb_url = f"/assets/OrderStatus/{thumb_relative_path}"
            except Exception as e:
                print(f"生成缩略图失败: {str(e)}")
                # 如果缩略图生成失败，继续处理原图

        # 更新任务项的photo_path字段（支持多张图片，用逗号分隔）
        if task.photo_path:
            task.photo_path = f"{task.photo_path},{file_url}"
        else:
            task.photo_path = file_url

        # 更新任务项的thumb_photo_path字段（支持多张缩略图，用逗号分隔）
        if thumb_url:
            if task.thumb_photo_path:
                task.thumb_photo_path = f"{task.thumb_photo_path},{thumb_url}"
            else:
                task.thumb_photo_path = thumb_url

        task.update_time = datetime.now()
        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': '文件上传成功',
            'data': {
                'file_url': file_url,
                'thumb_url': thumb_url,  # 返回缩略图URL
                'file_name': new_filename,
                'relative_path': relative_path
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'文件上传失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>/tasks/<int:task_id>/media', methods=['DELETE'])
def delete_status_task_media(status_id, task_id):
    """删除任务项的媒体文件"""
    try:
        task = StatusTask.query.filter_by(id=task_id, order_status_id=status_id).first()
        if not task:
            return jsonify({'code': 404, 'msg': '任务项不存在或不属于该进度记录'})

        media_file_path = request.json.get('media_file_path') if request.json else None
        if not media_file_path:
            return jsonify({'code': 400, 'msg': '缺少媒体文件路径'})

        # 从photo_path中移除指定的文件路径
        if task.photo_path:
            paths = task.photo_path.split(',')
            updated_paths = [path for path in paths if path != media_file_path]
            task.photo_path = ','.join(updated_paths)

        # 同时处理缩略图路径
        if task.thumb_photo_path:
            thumb_paths = task.thumb_photo_path.split(',')
            # 找到与原图对应的缩略图路径（通常是以thumb_开头的同目录文件）
            thumb_to_remove = None
            for path in thumb_paths:
                # 检查缩略图路径是否对应于要删除的原图
                original_filename = os.path.basename(media_file_path)
                thumb_filename = f"thumb_{original_filename}"
                if thumb_filename in path or path.replace('/thumb_', '/') == media_file_path:
                    thumb_to_remove = path
                    break

            if thumb_to_remove:
                updated_thumb_paths = [path for path in thumb_paths if path != thumb_to_remove]
                task.thumb_photo_path = ','.join(updated_thumb_paths)

        task.update_time = datetime.now()
        db.session.commit()

        # 删除实际文件
        try:
            if os.path.exists(media_file_path.lstrip('/')):
                os.remove(media_file_path.lstrip('/'))

            # 如果有对应的缩略图文件，也删除它
            if thumb_to_remove and os.path.exists(thumb_to_remove.lstrip('/')):
                os.remove(thumb_to_remove.lstrip('/'))
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            pass  # 文件删除失败不影响记录更新

        return jsonify({'code': 200, 'msg': '媒体文件删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'删除媒体文件失败: {str(e)}'})


@order_status_bp.route('/order-status-logs/<int:log_id>', methods=['PUT'])
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

        # 删除关联的图片文件（为了兼容旧数据，仍然删除单独的文件）
        if task.photo_path:
            photo_paths = task.photo_path.split(',')
            for photo_path in photo_paths:
                try:
                    # 移除URL前缀，获取实际文件路径
                    if photo_path.startswith('/assets/OrderStatus/'):
                        file_path = photo_path[1:]
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    # 如果有缩略图，也删除缩略图文件
                    if task.thumb_photo_path:
                        thumb_paths = task.thumb_photo_path.split(',')
                        for thumb_path in thumb_paths:
                            if thumb_path.startswith('/assets/OrderStatus/'):
                                thumb_file_path = thumb_path[1:]
                                if os.path.exists(thumb_file_path):
                                    os.remove(thumb_file_path)
                except Exception as e:
                    # 删除文件失败不影响任务删除
                    print(f"删除文件失败: {str(e)}")

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


@order_status_bp.route('/order-status/<int:status_id>', methods=['GET'])
def get_complete_order_status_details(status_id):
    """获取订单状态的完整详情（包含状态日志和任务项）"""
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

        # 添加状态日志数据
        result['status_logs'] = [log.to_dict() for log in status_logs]

        # 添加任务项数据
        result['tasks'] = []

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
                    'children': []
                }
                categories[task.status_log_id] = category_data
                result['tasks'].append(category_data)

            # 添加子任务
            task_data = {
                'task_id': task.id,
                'parent_id': task.status_log_id,
                'category': status_log.status if status_log else '未分类',
                'name': task.name,
                'item_type': 'sub',
                'is_completed': task.is_completed,
                'photo_path': task.photo_path,
                'thumb_photo_path': task.thumb_photo_path,
                'description': task.description,
                'sort_order': task.sort,
                'create_time': task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
                'update_time': task.update_time.strftime('%Y-%m-%d %H:%M:%S') if task.update_time else None
            }
            categories[task.status_log_id]['children'].append(task_data)

        return jsonify({
            'code': 200,
            'data': result,
            'msg': '订单状态详情获取成功'
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取订单状态详情失败: {str(e)}'})


@order_status_bp.route('/order-status/<int:status_id>/report', methods=['GET'])
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
                'photo_path': task.photo_path,
                'thumb_photo_path': task.thumb_photo_path,
                'description': task.description,
                'sort': task.sort,
                'create_time': task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
                'update_time': task.update_time.strftime('%Y-%m-%d %H:%M:%S') if task.update_time else None
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
def upload_multiple_images():
    """批量上传任务项图片"""
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

        # 构建上传路径：./assets/OrderStatus/合同编号/status_log_id/task_id/
        contract_no = order.contract_no.replace('/', '_').replace('\\', '_')
        status_log_folder = str(status_log.id)
        task_folder = str(task.id)

        upload_dir = os.path.join(UPLOAD_FOLDER, contract_no, status_log_folder, task_folder)
        os.makedirs(upload_dir, exist_ok=True)

        uploaded_urls = []
        uploaded_thumb_urls = []

        # 逐个处理上传的文件
        for file in files:
            if not allowed_file(file.filename):
                return jsonify({'code': 400, 'msg': f'不允许的文件类型: {file.filename}'})

            # 确保文件名安全
            safe_filename = secure_filename(file.filename)

            # 检查该任务是否已有相同名称的文件，如果有则添加序号
            base_name, ext = os.path.splitext(safe_filename)
            counter = 1
            new_filename = safe_filename
            while os.path.exists(os.path.join(upload_dir, new_filename)):
                new_filename = f"{base_name}_{counter}{ext}"
                counter += 1

            # 保存文件
            file_path = os.path.join(upload_dir, new_filename)
            file.save(file_path)

            # 生成相对路径URL
            relative_path = os.path.relpath(file_path, UPLOAD_FOLDER)
            file_url = f"/assets/OrderStatus/{relative_path}"

            # 如果是图片，生成缩略图
            thumb_url = None
            if get_file_type(file.filename) == 'image':
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
                    thumb_relative_path = os.path.relpath(thumb_path, UPLOAD_FOLDER)
                    thumb_url = f"/assets/OrderStatus/{thumb_relative_path}"
                except Exception as e:
                    print(f"生成缩略图失败: {str(e)}")
                    # 如果缩略图生成失败，继续处理原图

            uploaded_urls.append(file_url)
            if thumb_url:
                uploaded_thumb_urls.append(thumb_url)

        # 更新任务项的photo_path字段（追加新图片路径）
        if task.photo_path:
            task.photo_path = f"{task.photo_path},{','.join(uploaded_urls)}"
        else:
            task.photo_path = ','.join(uploaded_urls)

        # 更新任务项的thumb_photo_path字段（追加新缩略图路径）
        if task.thumb_photo_path:
            task.thumb_photo_path = f"{task.thumb_photo_path},{','.join(uploaded_thumb_urls)}"
        else:
            task.thumb_photo_path = ','.join(uploaded_thumb_urls)

        task.update_time = datetime.now()
        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': f'成功上传 {len(files)} 张图片',
            'data': {
                'file_urls': uploaded_urls,
                'thumb_urls': uploaded_thumb_urls,
                'file_count': len(files)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'批量上传失败: {str(e)}'})