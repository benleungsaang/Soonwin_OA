from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import uuid
from extensions import db
from app.models.order import Order
from app.models.order_progress import OrderProgress, ProgressStatusDetail, ProgressItem, ProgressMedia
from app.utils.upload_utils import allowed_file, get_file_type

progress_bp = Blueprint('progress_bp', __name__)

# 上传文件配置
UPLOAD_FOLDER = 'assets/OrderProgress'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@progress_bp.route('/orders/<order_id>/progress', methods=['GET'])
def get_order_progress(order_id):
    """获取订单进度详情"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'})
        
        progress = order.progress
        # 如果进度表不存在，自动创建一个
        if not progress:
            progress = OrderProgress(
                order_id=order.id,
                current_status=None  # 允许为空，不自动设置为"未开始"
            )
            db.session.add(progress)
            db.session.flush()  # 先flush获取ID，但不提交事务
            
            # 如果需要初始化默认状态，可以在这里创建，但目前我们允许为空
            db.session.commit()
        
        # 组装详情数据
        result = {
            # 订单基础信息（仅返回非敏感字段）
            'order_info': {
                'id': order.id,
                'contract_no': order.contract_no,
                'order_no': order.order_no,
                'machine_no': order.machine_no,
                'machine_name': order.machine_name,
                'machine_model': order.machine_model,
                'machine_count': order.machine_count,
                'order_time': order.order_time.strftime('%Y-%m-%d') if order.order_time else None,
                'ship_time': order.ship_time.strftime('%Y-%m-%d') if order.ship_time else None
            },
            # 进度总信息
            'progress_info': {
                'id': progress.id,  # 添加进度表ID
                'current_status': progress.current_status,
                'status_details': [
                    {
                        'id': detail.id,
                        'status': detail.status,
                        'start_time': detail.start_time.strftime('%Y-%m-%d %H:%M') if detail.start_time else None,
                        'expected_complete_time': detail.expected_complete_time.strftime('%Y-%m-%d %H:%M') if detail.expected_complete_time else None,
                        'actual_complete_time': detail.actual_complete_time.strftime('%Y-%m-%d %H:%M') if detail.actual_complete_time else None
                    } for detail in progress.status_details
                ]
            },
            # 进度项
            'progress_items': [
                {
                    'id': item.id,
                    'title': item.title,
                    'status': item.status,
                    'remark': item.remark,
                    'create_time': item.create_time.strftime('%Y-%m-%d %H:%M'),
                    'update_time': item.update_time.strftime('%Y-%m-%d %H:%M') if item.update_time else None,
                    'media_files': [
                        {
                            'id': media.id,
                            'file_type': media.file_type,
                            'file_url': media.file_url,
                            'file_name': media.file_name,
                            'upload_time': media.upload_time.strftime('%Y-%m-%d %H:%M')
                        } for media in item.media_files
                    ]
                } for item in progress.items
            ],
            # 进度统计
            'progress_stat': {
                'completed': len([i for i in progress.items if i.status == '已完成']),
                'total': len(progress.items),
                'rate': len([i for i in progress.items if i.status == '已完成']) / len(progress.items) * 100 if progress.items else 0
            }
        }
        return jsonify({'code': 200, 'data': result})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取订单进度详情失败: {str(e)}'})


@progress_bp.route('/orders/<order_id>/progress/status', methods=['PUT'])
def update_progress_status(order_id):
    """更新订单进度状态"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'})
        
        progress = order.progress
        if not progress:
            return jsonify({'code': 404, 'msg': '订单进度不存在'})
        
        data = request.json
        new_status = data.get('status')
        start_time_str = data.get('start_time')
        expected_complete_time_str = data.get('expected_complete_time')
        actual_complete_time_str = data.get('actual_complete_time')
        
        if not new_status:
            return jsonify({'code': 400, 'msg': '状态不能为空'})
        
        # 更新当前状态
        old_status = progress.current_status
        progress.current_status = new_status
        progress.update_time = datetime.now()
        
        # 检查是否已存在该状态的详情记录
        status_detail = next((detail for detail in progress.status_details if detail.status == new_status), None)
        
        if not status_detail:
            # 创建新的状态详情记录
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d') if start_time_str else datetime.now()
            expected_complete_time = datetime.strptime(expected_complete_time_str, '%Y-%m-%d') if expected_complete_time_str else None
            actual_complete_time = datetime.strptime(actual_complete_time_str, '%Y-%m-%d') if actual_complete_time_str else None
            
            status_detail = ProgressStatusDetail(
                progress_id=progress.id,
                status=new_status,
                start_time=start_time,
                expected_complete_time=expected_complete_time,
                actual_complete_time=actual_complete_time
            )
            db.session.add(status_detail)
        else:
            # 更新现有状态详情的时间
            if start_time_str:
                status_detail.start_time = datetime.strptime(start_time_str, '%Y-%m-%d')
            if expected_complete_time_str:
                status_detail.expected_complete_time = datetime.strptime(expected_complete_time_str, '%Y-%m-%d')
            if actual_complete_time_str:
                status_detail.actual_complete_time = datetime.strptime(actual_complete_time_str, '%Y-%m-%d')
        
        # 如果是从其他状态切换到已完成，则更新实际完成时间
        if new_status == '完成' and old_status != '完成' and not status_detail.actual_complete_time:
            status_detail.actual_complete_time = datetime.now()
        
        db.session.commit()
        return jsonify({'code': 200, 'msg': '进度状态更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'更新进度状态失败: {str(e)}'})


@progress_bp.route('/orders/<order_id>/progress/status', methods=['POST'])
def create_progress_status(order_id):
    """创建新的进度状态"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'})
        
        progress = order.progress
        if not progress:
            return jsonify({'code': 404, 'msg': '订单进度不存在'})
        
        data = request.json
        new_status = data.get('status')
        if not new_status:
            return jsonify({'code': 400, 'msg': '状态不能为空'})
        
        # 检查是否已存在该状态
        existing_detail = next((detail for detail in progress.status_details if detail.status == new_status), None)
        if existing_detail:
            return jsonify({'code': 400, 'msg': '该状态已存在'})
        
        # 创建新的状态详情记录
        start_time_str = data.get('start_time')
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d') if start_time_str else datetime.now()
        expected_complete_time_str = data.get('expected_complete_time')
        expected_complete_time = datetime.strptime(expected_complete_time_str, '%Y-%m-%d') if expected_complete_time_str else None
        actual_complete_time_str = data.get('actual_complete_time')
        actual_complete_time = datetime.strptime(actual_complete_time_str, '%Y-%m-%d') if actual_complete_time_str else None
        
        status_detail = ProgressStatusDetail(
            progress_id=progress.id,
            status=new_status,
            start_time=start_time,
            expected_complete_time=expected_complete_time,
            actual_complete_time=actual_complete_time
        )
        db.session.add(status_detail)
        
        # 更新当前状态
        progress.current_status = new_status
        
        db.session.commit()
        return jsonify({'code': 200, 'msg': '进度状态创建成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'创建进度状态失败: {str(e)}'})


@progress_bp.route('/progress/items', methods=['POST'])
def add_progress_item():
    """新增进度项"""
    try:
        data = request.json
        progress_id = data.get('progress_id')
        title = data.get('title')
        status = data.get('status', '未完成')
        remark = data.get('remark')
        
        if not progress_id or not title:
            return jsonify({'code': 400, 'msg': '进度表ID和标题不能为空'})
        
        new_item = ProgressItem(
            progress_id=progress_id,
            title=title,
            status=status,
            remark=remark
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '进度项创建成功', 'data': {'item_id': new_item.id}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'创建进度项失败: {str(e)}'})


@progress_bp.route('/progress/items/<item_id>', methods=['PUT'])
def update_progress_item(item_id):
    """更新进度项"""
    try:
        item = ProgressItem.query.get(item_id)
        if not item:
            return jsonify({'code': 404, 'msg': '进度项不存在'})
        
        data = request.json
        if 'title' in data:
            item.title = data['title']
        if 'status' in data:
            item.status = data['status']
        if 'remark' in data:
            item.remark = data['remark']
        item.update_time = datetime.now()
        
        db.session.commit()
        return jsonify({'code': 200, 'msg': '进度项更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'更新进度项失败: {str(e)}'})


@progress_bp.route('/progress/items/<item_id>', methods=['DELETE'])
def delete_progress_item(item_id):
    """删除进度项"""
    try:
        item = ProgressItem.query.get(item_id)
        if not item:
            return jsonify({'code': 404, 'msg': '进度项不存在'})
        
        # 删除关联的多媒体文件
        for media in item.media_files:
            # 删除实际文件
            try:
                if os.path.exists(media.file_url.lstrip('/')):
                    os.remove(media.file_url.lstrip('/'))
            except:
                pass  # 文件删除失败不影响记录删除
            db.session.delete(media)
        
        db.session.delete(item)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '进度项删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'删除进度项失败: {str(e)}'})


@progress_bp.route('/progress/media/upload', methods=['POST'])
def upload_progress_media():
    """上传进度项多媒体文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'code': 400, 'msg': '未上传文件'})
        
        file = request.files['file']
        item_id = request.form.get('item_id')
        
        if not item_id or file.filename == '':
            return jsonify({'code': 400, 'msg': '参数缺失'})
        
        if not allowed_file(file.filename):
            return jsonify({'code': 400, 'msg': '不允许的文件类型'})
        
        # 检查进度项是否存在
        item = ProgressItem.query.get(item_id)
        if not item:
            return jsonify({'code': 404, 'msg': '进度项不存在'})
        
        # 生成文件名并保存
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # 确定文件类型
        file_type = get_file_type(file.filename)
        
        # 记录文件信息
        new_media = ProgressMedia(
            item_id=item_id,
            file_type=file_type,
            file_url=f"/{UPLOAD_FOLDER}/{filename}",  # 前端访问路径
            file_name=file.filename
        )
        db.session.add(new_media)
        db.session.commit()
        
        return jsonify({
            'code': 200, 
            'msg': '文件上传成功', 
            'data': {
                'id': new_media.id,
                'file_url': new_media.file_url,
                'file_name': new_media.file_name
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'文件上传失败: {str(e)}'})


@progress_bp.route('/progress/media/<media_id>', methods=['DELETE'])
def delete_progress_media(media_id):
    """删除进度项多媒体文件"""
    try:
        media = ProgressMedia.query.get(media_id)
        if not media:
            return jsonify({'code': 404, 'msg': '媒体文件不存在'})
        
        # 删除实际文件
        try:
            if os.path.exists(media.file_url.lstrip('/')):
                os.remove(media.file_url.lstrip('/'))
        except:
            pass  # 文件删除失败不影响记录删除
        
        db.session.delete(media)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '媒体文件删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'删除媒体文件失败: {str(e)}'})


@progress_bp.route('/orders', methods=['POST'])
def create_order_with_progress():
    """创建订单时自动生成进度表"""
    try:
        data = request.json
        # 创建订单（过滤敏感字段，仅接收非敏感数据）
        new_order = Order(
            is_new=data.get('is_new'),
            area=data.get('area'),
            customer_name=data.get('customer_name'),
            customer_type=data.get('customer_type'),
            order_time=datetime.strptime(data.get('order_time'), '%Y-%m-%d') if data.get('order_time') else None,
            ship_time=datetime.strptime(data.get('ship_time'), '%Y-%m-%d') if data.get('ship_time') else None,
            ship_country=data.get('ship_country'),
            contract_no=data.get('contract_no'),
            order_no=data.get('order_no'),
            machine_no=data.get('machine_no'),
            machine_name=data.get('machine_name', '包装机'),
            machine_model=data.get('machine_model'),
            machine_count=data.get('machine_count', 1),
            unit=data.get('unit', 'set'),
            contract_amount=data.get('contract_amount'),
            deposit=data.get('deposit'),
            balance=data.get('balance'),
            tax_rate=data.get('tax_rate', 13.0),
            tax_refund_amount=data.get('tax_refund_amount'),
            currency_amount=data.get('currency_amount'),
            payment_received=data.get('payment_received'),
            machine_cost=data.get('machine_cost'),
            net_profit=data.get('net_profit'),
            proportionate_cost=data.get('proportionate_cost'),
            individual_cost=data.get('individual_cost'),
            gross_profit=data.get('gross_profit'),
            pay_type=data.get('pay_type', 'T/T'),
            commission=data.get('commission'),
            latest_ship_date=datetime.strptime(data.get('latest_ship_date'), '%Y-%m-%d') if data.get('latest_ship_date') else None,
            expected_delivery=datetime.strptime(data.get('expected_delivery'), '%Y-%m-%d') if data.get('expected_delivery') else None,
            order_dept=data.get('order_dept'),
            check_requirement=data.get('check_requirement'),
            attachment_imgs=data.get('attachment_imgs'),
            attachment_videos=data.get('attachment_videos'),
        )
        
        # 生成搜索字段
        new_order.search_field = new_order.generate_search_field()
        
        db.session.add(new_order)
        db.session.flush()  # 先获取订单ID，不提交
        
        # 自动创建关联进度表（初始状态为"下单"）
        new_progress = OrderProgress(
            order_id=new_order.id,
            current_status='下单'
        )
        # 初始化"下单"状态的时间详情
        new_status_detail = ProgressStatusDetail(
            progress_id=new_progress.id,
            status='下单',
            start_time=datetime.now()  # 下单状态开始时间为当前
        )
        db.session.add(new_progress)
        db.session.add(new_status_detail)
        db.session.commit()
        
        return jsonify({'code': 200, 'msg': '订单及进度表创建成功', 'data': {'order_id': new_order.id}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'订单创建失败: {str(e)}'})


@progress_bp.route('/orders', methods=['GET'])
def get_order_list_with_progress():
    """获取订单列表（仅返回非敏感基础数据）"""
    try:
        # 获取分页参数（与order_routes.py保持一致）
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
            result.append({
                'id': order.id,
                'contract_no': order.contract_no,
                'order_no': order.order_no,
                'machine_no': order.machine_no,
                'machine_name': order.machine_name,
                'machine_model': order.machine_model,
                'machine_count': order.machine_count,
                'order_time': order.order_time.strftime('%Y-%m-%d') if order.order_time else None,
                'ship_time': order.ship_time.strftime('%Y-%m-%d') if order.ship_time else None,
                'current_status': order.progress.current_status if order.progress else None
            })
        
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


@progress_bp.route('/orders/<order_id>/progress', methods=['DELETE'])
def delete_order_progress(order_id):
    """删除订单进度及所有相关数据"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'})
        
        progress = order.progress
        if not progress:
            return jsonify({'code': 404, 'msg': '订单进度不存在'})
        
        # 删除进度项及其关联的媒体文件
        for item in progress.items:
            for media in item.media_files:
                # 删除实际媒体文件
                try:
                    if os.path.exists(media.file_url.lstrip('/')):
                        os.remove(media.file_url.lstrip('/'))
                except:
                    pass  # 文件删除失败不影响记录删除
                db.session.delete(media)
            db.session.delete(item)
        
        # 删除状态详情记录
        for status_detail in progress.status_details:
            db.session.delete(status_detail)
        
        # 删除进度表本身
        db.session.delete(progress)
        db.session.commit()
        
        return jsonify({'code': 200, 'msg': '订单进度删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'删除订单进度失败: {str(e)}'})


@progress_bp.route('/orders/<order_id>/progress/status', methods=['DELETE'])
def clear_progress_status(order_id):
    """删除当前状态详情及在该状态下创建的进度项"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'})
        
        progress = order.progress
        if not progress:
            return jsonify({'code': 404, 'msg': '订单进度不存在'})
        
        # 如果没有当前状态值，尝试获取最新的状态详情作为当前要删除的状态
        current_status = progress.current_status
        if not current_status and progress.status_details:
            # 获取最新的状态详情
            latest_status_detail = progress.status_details[-1]  # 最后一个通常是最新状态
            current_status = latest_status_detail.status
        
        if not current_status:
            return jsonify({'code': 400, 'msg': '当前没有状态可删除'})
        
        # 查找当前状态的详情记录
        current_status_detail = next((detail for detail in progress.status_details if detail.status == current_status), None)
        if not current_status_detail:
            return jsonify({'code': 404, 'msg': '当前状态详情不存在'})
        
        # 找到当前状态详情的开始时间
        status_start_time = current_status_detail.start_time
        status_end_time = current_status_detail.expected_complete_time  # 如果没有预期完成时间，使用实际完成时间
        if not status_end_time:
            status_end_time = current_status_detail.actual_complete_time  # 如果也没有实际完成时间，使用当前时间
        if not status_end_time:
            status_end_time = datetime.now()
        
        # 删除在该状态时间段内创建的进度项
        items_to_delete = []
        for item in progress.items:
            # 检查进度项的创建时间是否在当前状态期间
            if status_start_time <= item.create_time <= status_end_time:
                items_to_delete.append(item)
        
        # 删除找到的进度项及其关联的媒体文件
        for item in items_to_delete:
            for media in item.media_files:
                # 删除实际媒体文件
                try:
                    if os.path.exists(media.file_url.lstrip('/')):
                        os.remove(media.file_url.lstrip('/'))
                except:
                    pass  # 文件删除失败不影响记录删除
                db.session.delete(media)
            db.session.delete(item)
        
        # 删除当前状态的详情记录
        db.session.delete(current_status_detail)
        
        # 更新当前状态：如果删除的是当前状态，则清空current_status；否则不改变
        if progress.current_status == current_status:
            # 找到删除后的最新状态作为当前状态
            remaining_status_details = [detail for detail in progress.status_details if detail.id != current_status_detail.id]
            if remaining_status_details:
                # 设置为剩余状态中的最新一个
                new_current_status = remaining_status_details[-1].status
                progress.current_status = new_current_status
            else:
                progress.current_status = None
        
        db.session.commit()
        return jsonify({'code': 200, 'msg': '当前状态详情及关联进度项已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'删除当前状态详情失败: {str(e)}'})