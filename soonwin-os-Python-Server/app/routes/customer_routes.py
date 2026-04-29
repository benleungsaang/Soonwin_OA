"""
客户信息管理相关路由
用于管理客户信息，支持从询盘或订单记录导入
"""

from flask import Blueprint, request, jsonify, Response
from extensions import db
from app.models.customer import Customer
from app.models.inquiry import Inquiry
from app.models.order_record import OrderRecord
from app.utils.simple_auth_utils import route_permission
from app.utils.auth_utils import get_user_id_from_token, get_user_role_from_token
from datetime import datetime
import json
from decimal import Decimal

customer_bp = Blueprint('customer', __name__)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def get_current_user():
    """获取当前用户"""
    emp_id = get_user_id_from_token()
    return emp_id


def is_admin():
    """检查是否为管理员"""
    role = get_user_role_from_token()
    return role == 'admin'


# ========== 客户管理API ==========

@customer_bp.route('/customers', methods=['GET'])
@route_permission('customer_manage')
def get_customers():
    """获取客户列表"""
    try:
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        search = request.args.get('search', '', type=str)
        creator_id = get_current_user()

        query = Customer.query

        # 业务员只能查看自己创建的客户，管理员可查看所有
        if not is_admin():
            query = query.filter(Customer.creator_id == creator_id)

        # 搜索筛选
        if search:
            query = query.filter(Customer.search_field.contains(search))

        total = query.count()
        customers = query.order_by(Customer.create_time.desc()).offset((page - 1) * size).limit(size).all()

        response_data = {
            "code": 200,
            "msg": "获取客户列表成功",
            "data": {
                "list": [c.to_dict() for c in customers],
                "total": total,
                "page": page,
                "size": size
            }
        }
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取客户列表失败: {str(e)}", "data": None}), 500


@customer_bp.route('/customers', methods=['POST'])
@route_permission('customer_manage')
def create_customer():
    """创建客户"""
    try:
        data = request.get_json()
        creator_id = get_current_user()

        customer = Customer(
            company_name=data.get('company_name'),
            contact_person=data.get('contact_person'),
            phone=data.get('phone'),
            email=data.get('email'),
            area=data.get('area'),
            customer_type=data.get('customer_type'),
            source=data.get('source', 'manual'),
            source_id=data.get('source_id'),
            remark=data.get('remark'),
            creator_id=creator_id
        )
        customer.update_search_field()

        db.session.add(customer)
        db.session.commit()

        response_data = {"code": 200, "msg": "客户创建成功", "data": customer.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"创建客户失败: {str(e)}", "data": None}), 500


@customer_bp.route('/customers/<int:customer_id>', methods=['GET'])
@route_permission('customer_manage')
def get_customer(customer_id):
    """获取客户详情"""
    try:
        customer = Customer.query.get_or_404(customer_id)

        # 业务员只能查看自己创建的客户
        if not is_admin() and customer.creator_id != get_current_user():
            return jsonify({"code": 403, "msg": "无权限访问该客户", "data": None}), 403

        response_data = {"code": 200, "msg": "获取客户详情成功", "data": customer.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取客户详情失败: {str(e)}", "data": None}), 500


@customer_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@route_permission('customer_manage')
def update_customer(customer_id):
    """更新客户"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        data = request.get_json()

        # 业务员只能修改自己创建的客户
        if not is_admin() and customer.creator_id != get_current_user():
            return jsonify({"code": 403, "msg": "无权限修改该客户", "data": None}), 403

        if 'company_name' in data:
            customer.company_name = data['company_name']
        if 'contact_person' in data:
            customer.contact_person = data['contact_person']
        if 'phone' in data:
            customer.phone = data['phone']
        if 'email' in data:
            customer.email = data['email']
        if 'area' in data:
            customer.area = data['area']
        if 'customer_type' in data:
            customer.customer_type = data['customer_type']
        if 'remark' in data:
            customer.remark = data['remark']

        customer.update_time = datetime.now()
        customer.update_search_field()
        db.session.commit()

        response_data = {"code": 200, "msg": "客户更新成功", "data": customer.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新客户失败: {str(e)}", "data": None}), 500


@customer_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@route_permission('customer_manage')
def delete_customer(customer_id):
    """删除客户"""
    try:
        customer = Customer.query.get_or_404(customer_id)

        # 业务员只能删除自己创建的客户
        if not is_admin() and customer.creator_id != get_current_user():
            return jsonify({"code": 403, "msg": "无权限删除该客户", "data": None}), 403

        # 解除关联的询盘和订单记录的 customer_id
        Inquiry.query.filter_by(customer_id=customer_id).update({'customer_id': None})
        OrderRecord.query.filter_by(customer_id=customer_id).update({'customer_id': None})

        db.session.delete(customer)
        db.session.commit()

        return jsonify({"code": 200, "msg": "客户删除成功", "data": None})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除客户失败: {str(e)}", "data": None}), 500


@customer_bp.route('/customers/<int:customer_id>/simple', methods=['GET'])
@route_permission('customer_manage')
def get_customer_simple(customer_id):
    """获取客户简单信息（用于快速展示）"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        response_data = {"code": 200, "msg": "获取成功", "data": customer.to_simple_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取客户简单信息失败: {str(e)}", "data": None}), 500


@customer_bp.route('/customers/<int:customer_id>/records', methods=['GET'])
@route_permission('customer_manage')
def get_customer_records(customer_id):
    """获取客户关联的询盘和订单记录"""
    try:
        customer = Customer.query.get_or_404(customer_id)

        # 业务员只能查看自己创建的客户的关联记录
        if not is_admin() and customer.creator_id != get_current_user():
            return jsonify({"code": 403, "msg": "无权限访问该客户", "data": None}), 403

        # 查找关联的询盘
        inquiries = Inquiry.query.filter_by(customer_id=customer_id).all()

        # 查找关联的订单记录
        order_records = OrderRecord.query.filter_by(customer_id=customer_id).all()

        response_data = {
            "code": 200,
            "msg": "获取关联记录成功",
            "data": {
                "inquiries": [i.to_dict() for i in inquiries],
                "order_records": [r.to_dict() for r in order_records]
            }
        }
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取关联记录失败: {str(e)}", "data": None}), 500


# ========== 从询盘/订单记录导入 ==========

@customer_bp.route('/customers/import-from-inquiry', methods=['POST'])
@route_permission('customer_manage')
def import_customer_from_inquiry():
    """从询盘导入客户信息（同时回写 customer_id 到询盘）"""
    try:
        data = request.get_json()
        inquiry_id = data.get('inquiry_id')
        creator_id = get_current_user()

        inquiry = Inquiry.query.get_or_404(inquiry_id)

        # 创建客户记录
        customer = Customer(
            company_name=inquiry.company_name,
            contact_person=inquiry.contact_person,
            phone=inquiry.phone,
            email=inquiry.email,
            area=inquiry.area,
            source='inquiry',
            source_id=inquiry_id,
            creator_id=creator_id
        )
        customer.update_search_field()

        db.session.add(customer)
        db.session.flush()  # 获取 customer.id

        # 回写 customer_id 到询盘
        inquiry.customer_id = customer.id

        db.session.commit()

        response_data = {"code": 200, "msg": "从询盘导入客户成功", "data": customer.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"从询盘导入客户失败: {str(e)}", "data": None}), 500


@customer_bp.route('/customers/import-from-order-record', methods=['POST'])
@route_permission('customer_manage')
def import_customer_from_order_record():
    """从订单记录导入客户信息（同时回写 customer_id 到订单记录）"""
    try:
        data = request.get_json()
        order_record_id = data.get('order_record_id')
        creator_id = get_current_user()

        order_record = OrderRecord.query.get_or_404(order_record_id)

        # 创建客户记录（从订单记录中提取客户相关信息）
        customer = Customer(
            company_name=order_record.order_remark_name or order_record.order_no,
            contact_person='',  # 订单记录没有联系人字段
            phone='',
            email='',
            area='',
            source='order_record',
            source_id=order_record_id,
            creator_id=creator_id
        )
        customer.update_search_field()

        db.session.add(customer)
        db.session.flush()  # 获取 customer.id

        # 回写 customer_id 到订单记录
        order_record.customer_id = customer.id

        db.session.commit()

        response_data = {"code": 200, "msg": "从订单记录导入客户成功", "data": customer.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"从订单记录导入客户失败: {str(e)}", "data": None}), 500


# ========== 在询盘/订单记录中直接创建客户（回写到源记录）==========

@customer_bp.route('/customers/create-from-inquiry/<int:inquiry_id>', methods=['POST'])
@route_permission('customer_manage')
def create_customer_from_inquiry(inquiry_id):
    """从询盘页面直接创建客户（同时回写 customer_id 到询盘）"""
    try:
        data = request.get_json()
        creator_id = get_current_user()

        inquiry = Inquiry.query.get_or_404(inquiry_id)

        # 创建客户记录
        customer = Customer(
            company_name=data.get('company_name') or inquiry.company_name,
            contact_person=data.get('contact_person') or inquiry.contact_person,
            phone=data.get('phone') or inquiry.phone,
            email=data.get('email') or inquiry.email,
            area=data.get('area') or inquiry.area,
            customer_type=data.get('customer_type'),
            source='inquiry',
            source_id=inquiry_id,
            remark=data.get('remark'),
            creator_id=creator_id
        )
        customer.update_search_field()

        db.session.add(customer)
        db.session.flush()  # 获取 customer.id

        # 回写 customer_id 到询盘
        inquiry.customer_id = customer.id

        db.session.commit()

        response_data = {"code": 200, "msg": "创建客户并绑定成功", "data": customer.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"创建客户失败: {str(e)}", "data": None}), 500


@customer_bp.route('/customers/create-from-order-record/<int:order_record_id>', methods=['POST'])
@route_permission('customer_manage')
def create_customer_from_order_record(order_record_id):
    """从订单记录页面直接创建客户（同时回写 customer_id 到订单记录）"""
    try:
        data = request.get_json()
        creator_id = get_current_user()

        order_record = OrderRecord.query.get_or_404(order_record_id)

        # 创建客户记录
        customer = Customer(
            company_name=data.get('company_name') or order_record.order_remark_name or order_record.order_no,
            contact_person=data.get('contact_person') or '',
            phone=data.get('phone') or '',
            email=data.get('email') or '',
            area=data.get('area') or '',
            customer_type=data.get('customer_type'),
            source='order_record',
            source_id=order_record_id,
            remark=data.get('remark'),
            creator_id=creator_id
        )
        customer.update_search_field()

        db.session.add(customer)
        db.session.flush()  # 获取 customer.id

        # 回写 customer_id 到订单记录
        order_record.customer_id = customer.id

        db.session.commit()

        response_data = {"code": 200, "msg": "创建客户并绑定成功", "data": customer.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"创建客户失败: {str(e)}", "data": None}), 500


# ========== 绑定/解绑API ==========

@customer_bp.route('/customers/<int:customer_id>/bind-inquiry', methods=['POST'])
@route_permission('customer_manage')
def bind_inquiry(customer_id):
    """绑定询盘到客户"""
    try:
        data = request.get_json()
        inquiry_id = data.get('inquiry_id')

        inquiry = Inquiry.query.get_or_404(inquiry_id)
        Customer.query.get_or_404(customer_id)

        inquiry.customer_id = customer_id
        db.session.commit()

        response_data = {"code": 200, "msg": "绑定询盘成功", "data": inquiry.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"绑定询盘失败: {str(e)}", "data": None}), 500


@customer_bp.route('/customers/<int:customer_id>/unbind-inquiry', methods=['POST'])
@route_permission('customer_manage')
def unbind_inquiry(customer_id):
    """解除询盘与客户的绑定"""
    try:
        data = request.get_json()
        inquiry_id = data.get('inquiry_id')

        inquiry = Inquiry.query.get_or_404(inquiry_id)
        inquiry.customer_id = None
        db.session.commit()

        response_data = {"code": 200, "msg": "解除绑定成功", "data": inquiry.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"解除绑定失败: {str(e)}", "data": None}), 500


@customer_bp.route('/customers/<int:customer_id>/bind-order-record', methods=['POST'])
@route_permission('customer_manage')
def bind_order_record(customer_id):
    """绑定订单记录到客户"""
    try:
        data = request.get_json()
        order_record_id = data.get('order_record_id')

        order_record = OrderRecord.query.get_or_404(order_record_id)
        Customer.query.get_or_404(customer_id)

        order_record.customer_id = customer_id
        db.session.commit()

        response_data = {"code": 200, "msg": "绑定订单记录成功", "data": order_record.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"绑定订单记录失败: {str(e)}", "data": None}), 500


@customer_bp.route('/customers/<int:customer_id>/unbind-order-record', methods=['POST'])
@route_permission('customer_manage')
def unbind_order_record(customer_id):
    """解除订单记录与客户的绑定"""
    try:
        data = request.get_json()
        order_record_id = data.get('order_record_id')

        order_record = OrderRecord.query.get_or_404(order_record_id)
        order_record.customer_id = None
        db.session.commit()

        response_data = {"code": 200, "msg": "解除绑定成功", "data": order_record.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"解除绑定失败: {str(e)}", "data": None}), 500
