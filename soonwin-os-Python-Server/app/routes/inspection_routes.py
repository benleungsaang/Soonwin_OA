from flask import Blueprint, request, jsonify
from extensions import db
from app.models.order_inspection import OrderInspection, InspectionItem
from app.models.order import Order
from app.models.employee import Employee
from datetime import datetime
import json
from decimal import Decimal
import requests
import os
import random
import re

def sanitize_filename(filename):
    """清理文件名，移除不安全字符"""
    if not filename:
        return "unknown"
    # 移除不安全字符，只保留字母数字、下划线、连字符和点
    sanitized = re.sub(r'[^\w\-_.]', '_', filename)
    # 限制长度
    return sanitized[:100] if sanitized else "unknown"

# 创建蓝图
inspection_bp = Blueprint('inspection', __name__)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

def check_user_role(user_id, required_role='admin'):
    """检查用户角色"""
    user = Employee.query.get(user_id)
    if not user:
        return False
    return user.user_role == required_role

def move_photos_if_needed(item, contract_no, token):
    """移动图片到正式位置"""
    if not item.photo_path or not getattr(item, '_photo_needs_move', False):
        return item.photo_path

    # 检查检查项的验收记录以获取合同号
    inspection = OrderInspection.query.get(item.inspection_id)
    order = Order.query.get(inspection.order_id) if inspection else None
    contract_no = sanitize_filename(order.contract_no if order and order.contract_no else 'unknown')

    # 检查检查项的父项以获取类别
    parent_item = None
    if item.parent_id:
        parent_item = InspectionItem.query.get(item.parent_id)
    
    item_category = sanitize_filename(parent_item.item_category if parent_item and parent_item.item_category else item.item_category or 'default_category')
    item_name = sanitize_filename(item.item_name or 'default_item')
    
    # 分割多个图片路径
    photo_paths = [path.strip() for path in item.photo_path.split(',') if path.strip()]
    updated_paths = []
    
    # 调用移动API处理每个图片
    for photo_path in photo_paths:
        if not photo_path:
            continue
            
        # 生成目标路径
        import time
        timestamp = int(time.time() * 1000)  # 毫秒时间戳
        unique_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
        
        # 获取文件扩展名
        file_extension = os.path.splitext(photo_path)[1] if os.path.splitext(photo_path)[1] else '.jpg'
        
        target_filename = f"{contract_no}_{item_category}_{item_name}_{unique_id}_{timestamp}{file_extension}"
        target_path = f"assets/OrderInspection/{contract_no}/{target_filename}"
        
        # 调用移动API
        try:
            move_url = f"http://192.168.30.70:5000/api/upload/move"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            payload = {
                'source_path': photo_path,
                'target_path': target_path
            }
            
            response = requests.post(move_url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    # 移动成功，使用新路径
                    updated_path = result.get('data', {}).get('target_path', target_path)
                    updated_paths.append(updated_path)
                    print(f"图片移动成功: {photo_path} -> {updated_path}")
                else:
                    # 移动失败，保留原路径
                    updated_paths.append(photo_path)
                    print(f"图片移动失败: {photo_path}, 错误: {result.get('msg', '未知错误')}")
            else:
                # 移动失败，保留原路径
                updated_paths.append(photo_path)
                print(f"图片移动API调用失败: {photo_path}, HTTP状态码: {response.status_code}")
        except Exception as e:
            print(f"移动图片异常 {photo_path}: {str(e)}")
            # 移动失败，保留原路径
            updated_paths.append(photo_path)
    
    return ','.join(updated_paths) if updated_paths else None


def calculate_inspection_progress(inspection_id):
    """计算验收进度"""
    total_items = db.session.query(db.func.count(InspectionItem.id)).filter(
        InspectionItem.inspection_id == inspection_id,
        InspectionItem.item_type == 'sub'
    ).scalar() or 0

    # 手动计算完成项，以精确控制哪些状态算作完成
    all_sub_items = InspectionItem.query.filter(
        InspectionItem.inspection_id == inspection_id,
        InspectionItem.item_type == 'sub'
    ).all()
    
    completed_items = 0
    for item in all_sub_items:
        if item.inspection_result == 'normal' and item.photo_path:
            # 正常状态且有照片
            completed_items += 1
        elif item.inspection_result == 'defect' and item.photo_path and item.description:
            # 不正常状态且有照片和描述
            completed_items += 1
        elif item.inspection_result == 'not_applicable':
            # 无此项状态
            completed_items += 1
        # pending 和 其他状态不算完成

    progress = 0
    if total_items > 0:
        progress = int((completed_items / total_items) * 100)

    # 更新验收记录的进度信息
    inspection = OrderInspection.query.get(inspection_id)
    if inspection:
        inspection.total_items = total_items
        inspection.completed_items = completed_items
        inspection.inspection_progress = progress
        if progress == 100:
            inspection.inspection_status = 'completed'
        elif completed_items > 0:
            inspection.inspection_status = 'in_progress'
        else:
            inspection.inspection_status = 'pending'

        db.session.commit()

    return progress, completed_items, total_items


@inspection_bp.route('/inspection-orders', methods=['GET'])
def get_inspection_orders():
    """获取需要验收的订单列表（仅返回必要字段）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 获取筛选参数
        order_no = request.args.get('order_no')
        contract_no = request.args.get('contract_no')
        machine_name = request.args.get('machine_name')
        machine_model = request.args.get('machine_model')

        # 构建基础查询
        base_query = db.session.query(Order)
        
        # 应用筛选条件
        if order_no:
            base_query = base_query.filter(Order.order_no.contains(order_no))
        if contract_no:
            base_query = base_query.filter(Order.contract_no.contains(contract_no))
        if machine_name:
            base_query = base_query.filter(Order.machine_name.contains(machine_name))
        if machine_model:
            base_query = base_query.filter(Order.machine_model.contains(machine_model))

        # 计算总数
        total = base_query.count()

        # 应用分页和排序
        orders = base_query.order_by(Order.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 获取每个订单的验收进度信息
        orders_list = []
        for order in orders:
            # 获取该订单的验收记录
            inspection = OrderInspection.query.filter_by(order_id=order.id).first()
            
            order_dict = {
                "id": order.id,
                "contract_no": order.contract_no,
                "order_no": order.order_no,
                "machine_no": order.machine_no,
                "machine_name": order.machine_name,
                "machine_model": order.machine_model,
                "machine_count": order.machine_count,
                "order_time": order.order_time.strftime('%Y-%m-%d') if order.order_time else None,
                "ship_time": order.ship_time.strftime('%Y-%m-%d') if order.ship_time else None,
                "inspection_id": inspection.id if inspection else None,
                "inspection_progress": inspection.inspection_progress if inspection else 0,
                "completed_items": inspection.completed_items if inspection else 0,
                "total_items": inspection.total_items if inspection else 0,
            }
            orders_list.append(order_dict)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取订单验收列表成功",
            "data": {
                "list": orders_list,
                "total": total,
                "page": page,
                "size": size
            }
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取订单验收列表失败: {str(e)}",
            "data": None
        }), 500


@inspection_bp.route('/inspections', methods=['GET'])
def get_inspections():
    """获取验收列表"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 获取筛选参数
        order_no = request.args.get('order_no')
        contract_no = request.args.get('contract_no')
        machine_name = request.args.get('machine_name')
        machine_model = request.args.get('machine_model')
        inspection_status = request.args.get('inspection_status')

        # 构建查询
        query = db.session.query(OrderInspection, Order).join(Order, OrderInspection.order_id == Order.id)

        # 应用筛选条件
        if order_no:
            query = query.filter(Order.order_no.contains(order_no))
        if contract_no:
            query = query.filter(Order.contract_no.contains(contract_no))
        if machine_name:
            query = query.filter(Order.machine_name.contains(machine_name))
        if machine_model:
            query = query.filter(Order.machine_model.contains(machine_model))
        if inspection_status:
            query = query.filter(OrderInspection.inspection_status == inspection_status)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        results = query.order_by(OrderInspection.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 序列化数据
        inspections_list = []
        for inspection, order in results:
            inspection_dict = inspection.to_dict()
            # 更新进度信息
            inspection_dict['inspection_progress'] = inspection.inspection_progress
            inspection_dict['completed_items'] = inspection.completed_items
            inspection_dict['total_items'] = inspection.total_items
            inspections_list.append(inspection_dict)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取验收列表成功",
            "data": {
                "list": inspections_list,
                "total": total,
                "page": page,
                "size": size
            }
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取验收列表失败: {str(e)}",
            "data": None
        }), 500


@inspection_bp.route('/inspections', methods=['POST'])
def create_inspection():
    """创建验收记录"""
    return ''



@inspection_bp.route('/inspections/<int:inspection_id>', methods=['GET'])
def get_inspection_detail(inspection_id):
    """获取验收详情"""
    try:
        inspection = OrderInspection.query.get_or_404(inspection_id)

        # 获取检查项
        items = InspectionItem.query.filter_by(inspection_id=inspection_id).order_by(InspectionItem.sort_order, InspectionItem.create_time).all()

        # 序列化数据
        inspection_dict = inspection.to_dict()

        # 按层级组织检查项
        parent_items = [item for item in items if item.item_type == 'parent']
        child_items = [item for item in items if item.item_type == 'sub']

        # 为每个父项添加子项
        for parent in parent_items:
            parent_dict = parent.to_dict()
            parent_dict['children'] = [child.to_dict() for child in child_items if child.parent_id == parent.id]
            parent_dict['completed_children'] = len([child for child in child_items if child.parent_id == parent.id and child.inspection_result in ['normal', 'defect', 'not_applicable']])
            parent_dict['total_children'] = len([child for child in child_items if child.parent_id == parent.id])
            parent_dict['progress'] = 0
            if parent_dict['total_children'] > 0:
                parent_dict['progress'] = int((parent_dict['completed_children'] / parent_dict['total_children']) * 100)
            parent.serialized_data = parent_dict

        items_list = [item.serialized_data if hasattr(item, 'serialized_data') else item.to_dict() for item in parent_items]
        # 添加没有父项的子项（如果有的话）
        for child in child_items:
            if child.parent_id is None:
                items_list.append(child.to_dict())

        inspection_dict['items'] = items_list

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取验收详情成功",
            "data": inspection_dict
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取验收详情失败: {str(e)}",
            "data": None
        }), 500


@inspection_bp.route('/inspections/<int:inspection_id>', methods=['PUT'])
def update_inspection(inspection_id):
    """更新验收记录"""
    try:
        inspection = OrderInspection.query.get_or_404(inspection_id)
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 更新验收记录字段
        if 'remarks' in data:
            inspection.remarks = data['remarks']

        db.session.commit()
        inspection_data = inspection.to_dict()

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "验收记录更新成功",
            "data": inspection_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新验收记录失败: {str(e)}",
            "data": None
        }), 500


@inspection_bp.route('/inspections/<int:inspection_id>/items', methods=['GET'])
def get_inspection_items(inspection_id):
    """获取验收检查项列表"""
    try:
        # 获取检查项
        items = InspectionItem.query.filter_by(inspection_id=inspection_id).order_by(InspectionItem.sort_order, InspectionItem.create_time).all()

        # 按层级组织检查项
        parent_items = [item for item in items if item.item_type == 'parent']
        child_items = [item for item in items if item.item_type == 'sub']

        # 为每个父项添加子项
        for parent in parent_items:
            parent_dict = parent.to_dict()
            parent_dict['children'] = [child.to_dict() for child in child_items if child.parent_id == parent.id]
            parent_dict['completed_children'] = len([child for child in child_items if child.parent_id == parent.id and child.inspection_result in ['normal', 'defect', 'not_applicable']])
            parent_dict['total_children'] = len([child for child in child_items if child.parent_id == parent.id])
            parent_dict['progress'] = 0
            if parent_dict['total_children'] > 0:
                parent_dict['progress'] = int((parent_dict['completed_children'] / parent_dict['total_children']) * 100)
            parent.serialized_data = parent_dict

        items_list = [item.serialized_data if hasattr(item, 'serialized_data') else item.to_dict() for item in parent_items]
        # 添加没有父项的子项（如果有的话）
        for child in child_items:
            if child.parent_id is None:
                items_list.append(child.to_dict())

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取检查项列表成功",
            "data": {
                "items": items_list,
                "inspection_id": inspection_id
            }
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取检查项列表失败: {str(e)}",
            "data": None
        }), 500


@inspection_bp.route('/inspections/<int:inspection_id>/items', methods=['POST'])
def create_inspection_item(inspection_id):
    """创建检查项"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 验证验收记录是否存在
        inspection = OrderInspection.query.get(inspection_id)
        if not inspection:
            return jsonify({
                "code": 400,
                "msg": "验收记录不存在",
                "data": None
            }), 400

        # 检查是否为父级项还是子项
        item_type = data.get('item_type', 'sub')
        parent_id = data.get('parent_id')

        # 如果是子项，验证父项是否存在
        if item_type == 'sub' and parent_id:
            parent_item = InspectionItem.query.get(parent_id)
            if not parent_item or parent_item.inspection_id != inspection_id:
                return jsonify({
                    "code": 400,
                    "msg": "父检查项不存在或不属于当前验收记录",
                    "data": None
                }), 400

        # 创建检查项
        new_item = InspectionItem(
            inspection_id=inspection_id,
            parent_id=parent_id,
            item_category=data.get('item_category', ''),
            item_name=data.get('item_name', ''),
            item_type=item_type,
            inspection_result=data.get('inspection_result', 'pending'),
            photo_path=data.get('photo_path'),
            description=data.get('description'),
            sort_order=data.get('sort_order', 0)
        )
        db.session.add(new_item)
        db.session.commit()

        # 重新计算进度
        calculate_inspection_progress(inspection_id)

        item_data = new_item.to_dict()

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "检查项创建成功",
            "data": item_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建检查项失败: {str(e)}",
            "data": None
        }), 500


@inspection_bp.route('/inspections/<int:inspection_id>/items/<int:item_id>', methods=['PUT'])
def update_inspection_item(inspection_id, item_id):
    """更新检查项"""
    try:
        item = InspectionItem.query.filter_by(id=item_id, inspection_id=inspection_id).first_or_404()

        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 更新检查项字段
        if 'item_category' in data: item.item_category = data['item_category']
        if 'item_name' in data: item.item_name = data['item_name']
        if 'inspection_result' in data: item.inspection_result = data['inspection_result']
        if 'photo_path' in data: item.photo_path = data['photo_path']
        if 'description' in data: item.description = data['description']
        if 'sort_order' in data: item.sort_order = data['sort_order']

        db.session.commit()

        # 重新计算进度
        progress, completed_items, total_items = calculate_inspection_progress(inspection_id)

        item_data = item.to_dict()

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "检查项更新成功",
            "data": {
                "item": item_data,
                "progress": progress,
                "completed_items": completed_items,
                "total_items": total_items
            }
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新检查项失败: {str(e)}",
            "data": None
        }), 500


@inspection_bp.route('/inspections/<int:inspection_id>/items/<int:item_id>', methods=['DELETE'])
def delete_inspection_item(inspection_id, item_id):
    """删除检查项"""
    try:
        item = InspectionItem.query.filter_by(id=item_id, inspection_id=inspection_id).first_or_404()

        db.session.delete(item)
        db.session.commit()

        # 重新计算进度
        progress, completed_items, total_items = calculate_inspection_progress(inspection_id)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "检查项删除成功",
            "data": {
                "progress": progress,
                "completed_items": completed_items,
                "total_items": total_items
            }
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除检查项失败: {str(e)}",
            "data": None
        }), 500


@inspection_bp.route('/inspections/<int:inspection_id>/progress', methods=['GET'])
def get_inspection_progress(inspection_id):
    """获取验收进度"""
    try:
        inspection = OrderInspection.query.get_or_404(inspection_id)

        # 重新计算并获取进度
        progress, completed_items, total_items = calculate_inspection_progress(inspection_id)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取验收进度成功",
            "data": {
                "inspection_id": inspection_id,
                "progress": progress,
                "completed_items": completed_items,
                "total_items": total_items,
                "inspection_status": inspection.inspection_status
            }
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取验收进度失败: {str(e)}",
            "data": None
        }), 500


@inspection_bp.route('/inspections/<int:inspection_id>/report', methods=['GET'])
def get_inspection_report(inspection_id):
    """获取验收报告"""
    try:
        inspection = OrderInspection.query.get_or_404(inspection_id)

        # 获取检查项
        items = InspectionItem.query.filter_by(inspection_id=inspection_id).order_by(InspectionItem.sort_order, InspectionItem.create_time).all()

        # 按层级组织检查项
        parent_items = [item for item in items if item.item_type == 'parent']
        child_items = [item for item in items if item.item_type == 'sub']

        # 为每个父项添加子项
        for parent in parent_items:
            parent_dict = parent.to_dict()
            parent_dict['children'] = [child.to_dict() for child in child_items if child.parent_id == parent.id]
            parent_dict['completed_children'] = len([child for child in child_items if child.parent_id == parent.id and child.inspection_result in ['normal', 'defect', 'not_applicable']])
            parent_dict['total_children'] = len([child for child in child_items if child.parent_id == parent.id])
            parent_dict['progress'] = 0
            if parent_dict['total_children'] > 0:
                parent_dict['progress'] = int((parent_dict['completed_children'] / parent_dict['total_children']) * 100)
            parent.serialized_data = parent_dict

        items_list = [item.serialized_data if hasattr(item, 'serialized_data') else item.to_dict() for item in parent_items]
        # 添加没有父项的子项（如果有的话）
        for child in child_items:
            if child.parent_id is None:
                items_list.append(child.to_dict())

        # 序列化验收信息
        inspection_dict = inspection.to_dict()

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取验收报告成功",
            "data": {
                "inspection": inspection_dict,
                "items": items_list,
                "summary": {
                    "total_items": inspection.total_items,
                    "completed_items": inspection.completed_items,
                    "progress": inspection.inspection_progress,
                    "status": inspection.inspection_status
                }
            }
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取验收报告失败: {str(e)}",
            "data": None
        }), 500


@inspection_bp.route('/inspections/<int:inspection_id>/items/batch', methods=['POST'])
def batch_update_inspection_items(inspection_id):
    """批量创建、更新和删除检查项"""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空，且必须包含items字段",
                "data": None
            }), 400

        items_data = data['items']
        inspection = OrderInspection.query.get(inspection_id)
        if not inspection:
            return jsonify({
                "code": 400,
                "msg": "验收记录不存在",
                "data": None
            }), 400

        created_items = []
        updated_items = []
        deleted_items = []
        
        # 分离各种操作类型
        items_to_delete = []
        items_to_create = []
        items_to_update = []
        
        for item_data in items_data:
            item_id = item_data.get('id')
            
            if item_data.get('_toBeDeleted'):
                # 检查是否是本地新建的项目，这种项目不应该发送删除请求
                if item_data.get('is_local_new'):
                    # 本地新建且被删除的项目，无需发送到服务器进行删除操作
                    continue
                else:
                    items_to_delete.append(item_data)
            elif item_data.get('is_local_new') or not item_id:
                items_to_create.append(item_data)
            else:
                items_to_update.append(item_data)
        
        # 首先，处理删除操作
        for item_data in items_to_delete:
            item_id = item_data.get('id')
            item = InspectionItem.query.filter_by(id=item_id, inspection_id=inspection_id).first()
            if item:
                # 如果需要移动照片文件到DeleteFiles
                if item.photo_path and (item_data.get('_photo_needs_delete', False) or item.photo_path):
                    # 分割多个图片路径
                    photo_paths = [path.strip() for path in item.photo_path.split(',') if path.strip()]
                    
                    # 获取授权令牌用于调用移动API
                    auth_header = request.headers.get('Authorization', '')
                    token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''
                    
                    # 移动每个图片文件到DeleteFiles文件夹
                    for photo_path in photo_paths:
                        try:
                            import os
                            filename = os.path.basename(photo_path)
                            delete_folder = "assets/DeleteFiles"
                            
                            # 创建DeleteFiles文件夹如果不存在
                            os.makedirs(delete_folder, exist_ok=True)
                            
                            # 目标路径
                            target_path = f"{delete_folder}/{filename}"
                            
                            # 调用移动API将文件移动到DeleteFiles文件夹
                            move_url = f"http://192.168.30.70:5000/api/upload/move"
                            headers = {
                                'Authorization': f'Bearer {token}',
                                'Content-Type': 'application/json'
                            }
                            payload = {
                                'source_path': photo_path,
                                'target_path': target_path
                            }
                            
                            response = requests.post(move_url, json=payload, headers=headers)
                            if response.status_code == 200:
                                result = response.json()
                                if result.get('code') == 200:
                                    print(f"图片文件已移动到DeleteFiles: {photo_path} -> {target_path}")
                                else:
                                    print(f"图片文件移动失败: {photo_path}, 错误: {result.get('msg', '未知错误')}")
                                    # 移动失败，尝试直接删除
                                    delete_url = f"http://192.168.30.70:5000/api/upload/delete"
                                    delete_payload = {
                                        'path': photo_path
                                    }
                                    delete_response = requests.post(delete_url, json=delete_payload, headers=headers)
                                    if delete_response.status_code == 200:
                                        delete_result = delete_response.json()
                                        if delete_result.get('code') == 200:
                                            print(f"图片文件已删除: {photo_path}")
                                        else:
                                            print(f"图片文件删除失败: {photo_path}, 错误: {delete_result.get('msg', '未知错误')}")
                            else:
                                print(f"图片移动API调用失败: {photo_path}, HTTP状态码: {response.status_code}")
                        except Exception as e:
                            print(f"处理图片文件异常 {photo_path}: {str(e)}")
                
                # 如果是父项，还需删除其所有子项
                if item.item_type == 'parent':
                    child_items = InspectionItem.query.filter_by(parent_id=item.id, inspection_id=inspection_id).all()
                    for child in child_items:
                        # 移动子项的照片文件到DeleteFiles
                        if child.photo_path:
                            # 分割多个图片路径
                            child_photo_paths = [path.strip() for path in child.photo_path.split(',') if path.strip()]
                            
                            # 获取授权令牌用于调用移动API
                            auth_header = request.headers.get('Authorization', '')
                            token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''
                            
                            # 移动每个图片文件到DeleteFiles文件夹
                            for photo_path in child_photo_paths:
                                try:
                                    import os
                                    filename = os.path.basename(photo_path)
                                    delete_folder = "assets/DeleteFiles"
                                    
                                    # 创建DeleteFiles文件夹如果不存在
                                    os.makedirs(delete_folder, exist_ok=True)
                                    
                                    # 目标路径
                                    target_path = f"{delete_folder}/{filename}"
                                    
                                    # 调用移动API将文件移动到DeleteFiles文件夹
                                    move_url = f"http://192.168.30.70:5000/api/upload/move"
                                    headers = {
                                        'Authorization': f'Bearer {token}',
                                        'Content-Type': 'application/json'
                                    }
                                    payload = {
                                        'source_path': photo_path,
                                        'target_path': target_path
                                    }
                                    
                                    response = requests.post(move_url, json=payload, headers=headers)
                                    if response.status_code == 200:
                                        result = response.json()
                                        if result.get('code') == 200:
                                            print(f"子项图片文件已移动到DeleteFiles: {photo_path} -> {target_path}")
                                        else:
                                            print(f"子项图片文件移动失败: {photo_path}, 错误: {result.get('msg', '未知错误')}")
                                            # 移动失败，尝试直接删除
                                            delete_url = f"http://192.168.30.70:5000/api/upload/delete"
                                            delete_payload = {
                                                'path': photo_path
                                            }
                                            delete_response = requests.post(delete_url, json=delete_payload, headers=headers)
                                            if delete_response.status_code == 200:
                                                delete_result = delete_response.json()
                                                if delete_result.get('code') == 200:
                                                    print(f"子项图片文件已删除: {photo_path}")
                                                else:
                                                    print(f"子项图片文件删除失败: {photo_path}, 错误: {delete_result.get('msg', '未知错误')}")
                                    else:
                                        print(f"子项图片移动API调用失败: {photo_path}, HTTP状态码: {response.status_code}")
                                except Exception as e:
                                    print(f"处理子项图片文件异常 {photo_path}: {str(e)}")
                        
                        db.session.delete(child)
                        deleted_items.append(child)
                
                db.session.delete(item)
                deleted_items.append(item)
        
        # 然后，创建所有新项目并获取它们的ID
        temp_to_real_id_map = {}  # 临时ID到真实ID的映射
        created_item_objects = []  # 保存新创建的项目对象及其原始数据
        
        # 先创建所有新项目（不设置parent_id，暂时设置为null）
        for item_data in items_to_create:
            item_id = item_data.get('id')
            
            new_item = InspectionItem(
                inspection_id=inspection_id,
                parent_id=None,  # 暂时设置为null
                item_category=item_data.get('item_category', ''),
                item_name=item_data.get('item_name', ''),
                item_type=item_data.get('item_type', 'sub'),
                inspection_result=item_data.get('inspection_result', 'pending'),
                photo_path=item_data.get('photo_path'),
                description=item_data.get('description'),
                sort_order=item_data.get('sort_order', 0)
            )
            # 检查是否需要移动图片
            new_item._photo_needs_move = item_data.get('_photo_needs_move', False)
            db.session.add(new_item)
            db.session.flush()  # 获取新创建项目的ID
            created_items.append(new_item)
            
            # 记录临时ID到真实ID的映射（如果原ID不是None，即为前端生成的临时ID）
            if item_id is not None:
                temp_to_real_id_map[item_id] = new_item.id
            
            # 保存项目对象和原始数据的映射，用于后续设置parent_id
            created_item_objects.append({
                'original_data': item_data,
                'item_object': new_item
            })
        
        # 更新项目的parent_id关系（对于新建项目）
        # 使用之前保存的对象引用，而不是通过名称等属性查找
        for item_info in created_item_objects:
            item_data = item_info['original_data']
            created_item = item_info['item_object']
            
            parent_id = item_data.get('parent_id')
            if parent_id is not None:
                if parent_id in temp_to_real_id_map:
                    # 如果parent_id是临时ID，替换为真实ID
                    created_item.parent_id = temp_to_real_id_map[parent_id]
                else:
                    # 如果parent_id不是临时ID，直接使用（可能是已存在的项目）
                    created_item.parent_id = parent_id        
        # 处理更新现有项目
        for item_data in items_to_update:
            item_id = item_data.get('id')
            item = InspectionItem.query.filter_by(id=item_id, inspection_id=inspection_id).first()
            if item:
                # 检查parent_id是否需要更新
                parent_id = item_data.get('parent_id')
                if parent_id is not None:
                    if parent_id in temp_to_real_id_map:
                        # 如果parent_id是临时ID，替换为真实ID
                        item.parent_id = temp_to_real_id_map[parent_id]
                    else:
                        item.parent_id = parent_id
                else:
                    item.parent_id = item_data.get('parent_id', item.parent_id)
                
                item.item_category = item_data.get('item_category', item.item_category)
                item.item_name = item_data.get('item_name', item.item_name)
                item.item_type = item_data.get('item_type', item.item_type)
                item.inspection_result = item_data.get('inspection_result', item.inspection_result)
                item.photo_path = item_data.get('photo_path', item.photo_path)
                # 检查是否需要移动图片（通过检查特殊的标记）
                item._photo_needs_move = item_data.get('_photo_needs_move', False)
                item.description = item_data.get('description', item.description)
                item.sort_order = item_data.get('sort_order', item.sort_order)
                updated_items.append(item)

        db.session.commit()
        
        # 获取授权令牌用于调用移动API和删除API
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''
        
        # 处理需要删除的照片文件
        for item_data in items_to_update:
            item_id = item_data.get('id')
            item = InspectionItem.query.filter_by(id=item_id, inspection_id=inspection_id).first()
            if item:
                # 获取需要删除的照片路径列表
                photos_to_delete = item_data.get('photos_to_delete', [])
                for photo_path in photos_to_delete:
                    try:
                        # 构造移动到DeleteFiles的路径
                        import os
                        filename = os.path.basename(photo_path)
                        delete_folder = "assets/DeleteFiles"
                        
                        # 创建DeleteFiles文件夹如果不存在
                        os.makedirs(delete_folder, exist_ok=True)
                        
                        # 目标路径
                        target_path = f"{delete_folder}/{filename}"
                        
                        # 调用移动API将文件移动到DeleteFiles文件夹
                        move_url = f"http://192.168.30.70:5000/api/upload/move"
                        headers = {
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        }
                        payload = {
                            'source_path': photo_path,
                            'target_path': target_path
                        }
                        
                        response = requests.post(move_url, json=payload, headers=headers)
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('code') == 200:
                                print(f"图片文件已移动到DeleteFiles: {photo_path} -> {target_path}")
                                # 从当前项目的photo_path中移除已删除的路径
                                if item.photo_path:
                                    photo_paths = [p.strip() for p in item.photo_path.split(',') if p.strip() and p != photo_path]
                                    item.photo_path = ','.join(photo_paths) if photo_paths else None
                            else:
                                print(f"图片文件移动失败: {photo_path}, 错误: {result.get('msg', '未知错误')}")
                                # 移动失败，尝试直接删除
                                delete_url = f"http://192.168.30.70:5000/api/upload/delete"
                                delete_payload = {
                                    'path': photo_path
                                }
                                delete_response = requests.post(delete_url, json=delete_payload, headers=headers)
                                if delete_response.status_code == 200:
                                    delete_result = delete_response.json()
                                    if delete_result.get('code') == 200:
                                        print(f"图片文件已删除: {photo_path}")
                                        # 从当前项目的photo_path中移除已删除的路径
                                        if item.photo_path:
                                            photo_paths = [p.strip() for p in item.photo_path.split(',') if p.strip() and p != photo_path]
                                            item.photo_path = ','.join(photo_paths) if photo_paths else None
                                    else:
                                        print(f"图片文件删除失败: {photo_path}, 错误: {delete_result.get('msg', '未知错误')}")
                        else:
                            print(f"图片移动API调用失败: {photo_path}, HTTP状态码: {response.status_code}")
                    except Exception as e:
                        print(f"处理图片文件异常 {photo_path}: {str(e)}")

        # 处理图片移动（对新创建的项）
        for item in created_items:
            if item._photo_needs_move and item.photo_path:
                # 移动图片并更新路径
                new_photo_path = move_photos_if_needed(item, None, token)
                item.photo_path = new_photo_path
                # 清除标记
                item._photo_needs_move = False

        # 处理图片移动（对已更新的项）
        for item in updated_items:
            if item._photo_needs_move and item.photo_path:
                # 移动图片并更新路径
                new_photo_path = move_photos_if_needed(item, None, token)
                item.photo_path = new_photo_path
                # 清除标记
                item._photo_needs_move = False

        # 提交图片移动后的更改
        db.session.commit()

        # 重新计算进度
        progress, completed_items, total_items = calculate_inspection_progress(inspection_id)

        # 返回创建、更新和删除的项目信息
        created_items_data = [item.to_dict() for item in created_items]
        updated_items_data = [item.to_dict() for item in updated_items]
        deleted_items_data = [item.to_dict() for item in deleted_items]

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "批量操作成功",
            "data": {
                "created_items": created_items_data,
                "updated_items": updated_items_data,
                "deleted_items": deleted_items_data,
                "total_created": len(created_items),
                "total_updated": len(updated_items),
                "total_deleted": len(deleted_items),
                "progress": progress,
                "completed_items": completed_items,
                "total_items": total_items
            }
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"批量操作失败: {str(e)}",
            "data": None
        }), 500


@inspection_bp.route('/inspections/<int:inspection_id>/clear', methods=['POST'])
def clear_inspection_items(inspection_id):
    """清空验收检查项数据"""
    try:
        # 验证验收记录是否存在
        inspection = OrderInspection.query.get(inspection_id)
        if not inspection:
            return jsonify({
                "code": 400,
                "msg": "验收记录不存在",
                "data": None
            }), 400

        # 获取所有检查项
        items = InspectionItem.query.filter_by(inspection_id=inspection_id).all()

        # 获取授权令牌用于调用删除API
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''

        # 删除所有检查项的图片文件
        for item in items:
            if item.photo_path:
                # 分割多个图片路径
                photo_paths = [path.strip() for path in item.photo_path.split(',') if path.strip()]
                
                # 删除每个图片文件到DeleteFiles文件夹
                for photo_path in photo_paths:
                    try:
                        # 构建移动到DeleteFiles的路径
                        filename = os.path.basename(photo_path)
                        delete_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(photo_path))), 'DeleteFiles')
                        
                        # 确保DeleteFiles文件夹存在
                        os.makedirs(delete_folder, exist_ok=True)
                        
                        # 移动文件到DeleteFiles文件夹
                        source_path = os.path.join('..', '..', photo_path)
                        target_path = os.path.join(delete_folder, filename)
                        
                        # 确保目标目录存在
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        
                        if os.path.exists(source_path):
                            import shutil
                            shutil.move(source_path, target_path)
                            print(f"图片文件已移动到DeleteFiles: {photo_path} -> {target_path}")
                        else:
                            print(f"源文件不存在，尝试直接删除: {source_path}")
                            # 如果文件不存在，可能在其他地方，调用删除API
                            delete_url = f"http://192.168.30.70:5000/api/upload/delete"
                            headers = {
                                'Authorization': f'Bearer {token}',
                                'Content-Type': 'application/json'
                            }
                            payload = {
                                'path': photo_path
                            }
                            
                            response = requests.post(delete_url, json=payload, headers=headers)
                    except Exception as e:
                        print(f"移动或删除图片文件异常 {photo_path}: {str(e)}")

        # 删除所有检查项
        for item in items:
            db.session.delete(item)

        # 重新设置验收记录的进度为0
        inspection.total_items = 0
        inspection.completed_items = 0
        inspection.inspection_progress = 0
        inspection.inspection_status = 'pending'

        db.session.commit()

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "验收检查项已清空",
            "data": {
                "total_deleted": len(items)
            }
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"清空验收检查项失败: {str(e)}",
            "data": None
        }), 500