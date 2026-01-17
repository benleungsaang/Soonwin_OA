from flask import Blueprint, request, jsonify
from extensions import db
from app.models.order_inspection import OrderInspection, InspectionItem
from app.models.order import Order
from app.models.employee import Employee
from datetime import datetime
import json
from decimal import Decimal

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

def calculate_inspection_progress(inspection_id):
    """计算验收进度"""
    total_items = db.session.query(db.func.count(InspectionItem.id)).filter(
        InspectionItem.inspection_id == inspection_id,
        InspectionItem.item_type == 'sub'
    ).scalar() or 0

    completed_items = db.session.query(db.func.count(InspectionItem.id)).filter(
        InspectionItem.inspection_id == inspection_id,
        InspectionItem.item_type == 'sub',
        InspectionItem.inspection_result.in_(['normal', 'not_applicable'])
    ).scalar() or 0

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
            parent_dict['completed_children'] = len([child for child in child_items if child.parent_id == parent.id and child.inspection_result in ['normal', 'not_applicable']])
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
            parent_dict['completed_children'] = len([child for child in child_items if child.parent_id == parent.id and child.inspection_result in ['normal', 'not_applicable']])
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
            parent_dict['completed_children'] = len([child for child in child_items if child.parent_id == parent.id and child.inspection_result in ['normal', 'not_applicable']])
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
                # 如果是父项，还需删除其所有子项
                if item.item_type == 'parent':
                    child_items = InspectionItem.query.filter_by(parent_id=item.id, inspection_id=inspection_id).all()
                    for child in child_items:
                        db.session.delete(child)
                        deleted_items.append(child)
                
                db.session.delete(item)
                deleted_items.append(item)
        
        # 然后，创建所有新项目并获取它们的ID
        temp_to_real_id_map = {}  # 临时ID到真实ID的映射
        created_item_lookup = {}  # 用于查找已创建的项目
        
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
            db.session.add(new_item)
            db.session.flush()  # 获取新创建项目的ID
            created_items.append(new_item)
            
            # 记录临时ID到真实ID的映射（如果原ID不是None，即为前端生成的临时ID）
            if item_id is not None:
                temp_to_real_id_map[item_id] = new_item.id
            
            # 记录创建的项目，便于后续设置parent_id
            created_item_lookup[(new_item.item_name, new_item.item_category, new_item.item_type)] = new_item
        
        # 更新项目的parent_id关系（对于新建项目）
        for item_data in items_to_create:
            # 找到对应的已创建项目
            created_item = created_item_lookup.get((item_data.get('item_name', ''), 
                                                   item_data.get('item_category', ''), 
                                                   item_data.get('item_type', 'sub')))
            
            if created_item:
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
                item.description = item_data.get('description', item.description)
                item.sort_order = item_data.get('sort_order', item.sort_order)
                updated_items.append(item)

        db.session.commit()

        # 重新计算进度
        calculate_inspection_progress(inspection_id)

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
                "total_deleted": len(deleted_items)
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