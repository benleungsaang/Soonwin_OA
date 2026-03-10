from flask import Blueprint, request, jsonify
from extensions import db
from app.models.order import Order
from app.models.employee import Employee
from app.models.machine_new import MachineNew  # 导入MachineNew模型
from app.models.simple_permission import get_user_role_from_token
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_ORDER
from app.utils.auth_utils import get_user_id_from_token
from app.models.business_operation_log import BusinessOperationLog, add_order_log
from app.models.data_change_stats import DataChangeStats
from datetime import datetime, timedelta
import json
from decimal import Decimal
import jwt
from config import Config

# 从expense模型导入相关类
from app.models.expense import AnnualTarget, Expense, ExpenseAllocation, ExpenseCalculationRecord, IndividualExpense

# 创建蓝图
order_bp = Blueprint('order', __name__)
def get_current_user():
    """获取当前用户信息的辅助函数"""
    emp_id = get_user_id_from_token()
    user_role = get_user_role_from_token()
    user_name = "system"  # 默认名称

    # 尝试从数据库获取用户信息以获取真实姓名
    if emp_id:
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if employee:
            user_name = employee.name

    # 创建模拟用户对象
    current_user = type('User', (), {
        'emp_id': emp_id,
        'user_role': user_role,
        'name': user_name
    })()

    return current_user

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

def create_order_log(order_id, operation_type, operator_id, details="", order_obj=None):
    """创建订单操作日志，不包含统计信息"""
    # 获取客户名称
    customer_name = None
    if order_obj:
        customer_name = order_obj.customer_name
    elif order_id:
        # 如果没有传入对象但有 order_id，则查询获取客户名称
        order = Order.query.get(order_id)
        if order:
            customer_name = order.customer_name

    # 将客户名称等操作相关信息整合到 details 中
    details_dict = json.loads(details) if details else {}
    details_dict.update({
        "customer_name": customer_name
    })

    # 使用新的通用日志函数
    add_order_log(
        order_id=order_id,
        operation_type=operation_type,
        operator_id=operator_id,
        details=details_dict
    )

def convert_machine_ids_to_models(machine_ids_str):
    """
    将机器ID字符串转换为机器型号字符串
    :param machine_ids_str: 逗号分隔的机器ID字符串，例如 "1,2,3"
    :return: 逗号分隔的机器型号字符串，例如 "ModelA,ModelB,ModelC"
    """
    if not machine_ids_str:
        return ""

    try:
        # 解析ID列表
        machine_ids = [int(id.strip()) for id in machine_ids_str.split(",") if id.strip().isdigit()]

        # 查询数据库获取机器型号
        machines = MachineNew.query.filter(MachineNew.id.in_(machine_ids)).all()

        # 将机器型号组成字符串返回
        machine_models = [machine.model for machine in machines if machine.model]
        return ",".join(machine_models)
    except Exception as e:
        print(f"转换机器ID到型号时出错: {str(e)}")
        return machine_ids_str  # 如果转换失败，返回原始ID字符串


def serialize_order(order, include_expense_allocations=False, is_admin=False, fields=None):
    order_dict = order.to_dict()
    # 定义敏感字段列表
    sensitive_fields = ['machine_cost', 'proportionate_cost', 'net_profit', 'gross_profit']

    # 根据用户权限控制敏感字段
    if not is_admin:
        for field in sensitive_fields:
            if field in order_dict:
                order_dict[field] = 0.0

    # 对于管理员，添加creator_id字段
    if is_admin and hasattr(order, 'creator_id'):
        order_dict['creator_id'] = order.creator_id

    # 如果需要包含费用分摊信息
    if include_expense_allocations and is_admin:
        # 计算该订单的费用分摊总额
        from app.models.expense import ExpenseAllocation
        total_expense_allocation = db.session.query(
            db.func.sum(ExpenseAllocation.allocated_amount)
        ).filter(ExpenseAllocation.order_id == order.id).scalar() or 0.0

        order_dict['total_expense_allocation'] = float(total_expense_allocation)
        # 重新计算净利，减去费用分摊
        order_dict['net_profit_with_expense'] = order_dict['gross_profit'] - order_dict['proportionate_cost'] - order_dict['individual_cost'] - order_dict['total_expense_allocation']

    # 控制询盘信息的显示 - 非管理员不能看到敏感的询盘信息
    if 'inquiry' in order_dict and order_dict['inquiry']:
        original_inquiry = order_dict['inquiry']
        if is_admin:
            # 管理员可以看到完整信息
            safe_inquiry = original_inquiry
        else:
            # 非管理员只能看到非敏感字段
            safe_inquiry = {}

            # 只保留非敏感字段
            non_sensitive_inquiry_fields = [
                'id', 'area', 'inquiry_date', 'inquiry_source', 'company_name',
                'packaging_product', 'machine_type', 'search_field',
                'create_time', 'update_time'
            ]

            for field in non_sensitive_inquiry_fields:
                if field in original_inquiry:
                    safe_inquiry[field] = original_inquiry[field]

            # 设置creator相关字段为隐藏
            safe_inquiry['creator_id'] = '***'
            safe_inquiry['creator_name'] = '***'
            safe_inquiry['creator_role'] = '***'

        # 替换询盘信息
        order_dict['inquiry'] = safe_inquiry

    # 如果指定了字段列表，则只返回这些字段
    if fields:
        field_list = [f.strip() for f in fields.split(',')]
        # 确保ID字段总是被包含
        if 'id' not in field_list:
            field_list.insert(0, 'id')
        filtered_dict = {}
        for field in field_list:
            if field in order_dict:
                filtered_dict[field] = order_dict[field]
        return filtered_dict

    # 如果没有指定字段列表，根据用户权限返回字段
    # 对于管理员，返回所有字段
    # 对于非管理员，敏感字段已经设置为0.0，这里返回完整的字典
    return order_dict

@order_bp.route('/orders', methods=['GET'])
@route_permission(ROUTE_ORDER)
def get_orders():
    """获取订单列表，支持分页和筛选"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        # 获取筛选参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')  # 添加搜索参数
        fields = request.args.get('fields')  # 添加字段参数

        # 获取当前用户信息
        current_user = get_current_user()

        # 构建查询
        query = Order.query

        # 检查是否为管理员，如果不是管理员则只查询自己创建的数据
        if current_user.user_role != 'admin':
            query = query.filter(Order.creator_id == current_user.emp_id)

        # 如果有搜索参数，则使用search_field进行全文搜索
        if search:
            query = query.filter(Order.search_field.contains(search))

        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.order_time >= start_datetime)
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.order_time < end_datetime)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        orders = query.order_by(Order.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 检查是否需要包含费用分摊信息
        include_expense_allocations = request.args.get('include_expense_allocations', 'false').lower() == 'true'

        # 获取当前用户信息以确定是否为管理员
        is_admin = current_user and current_user.user_role == 'admin'

        # 序列化订单数据，支持字段过滤
        orders_list = [serialize_order(order, include_expense_allocations=include_expense_allocations, is_admin=is_admin, fields=fields) for order in orders]

        # 返回统一格式的数据，与打卡记录API保持一致
        import json
        response_data = {
            "code": 200,
            "msg": "获取订单列表成功",
            "data": {
                "list": orders_list,
                "total": total,
                "page": page,
                "size": size
            }
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        from flask import Response
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取订单列表失败: {str(e)}",
            "data": None
        }), 500

@order_bp.route('/orders', methods=['POST'])
@route_permission(ROUTE_ORDER)
def create_order():
    """创建新订单"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 验证是否提供了关联的询盘ID
        inquiry_id = data.get('inquiry_id')
        if not inquiry_id:
            return jsonify({
                "code": 400,
                "msg": "必须选择一个关联的询盘",
                "data": None
            }), 400

        # 验证询盘是否存在
        from app.models.inquiry import Inquiry
        inquiry = Inquiry.query.get(inquiry_id)
        if not inquiry:
            return jsonify({
                "code": 400,
                "msg": "指定的询盘不存在",
                "data": None
            }), 400

        # 检查询盘是否已经关联了订单
        if inquiry.has_associated_orders():
            return jsonify({
                "code": 400,
                "msg": "该询盘已关联订单，不能重复关联",
                "data": None
            }), 400

        # 获取当前用户
        current_user = get_current_user()

        # 处理机器型号字段 - 如果传入的是机器ID，则转换为对应的型号
        machine_model_value = data.get('machine_model')
        if machine_model_value and isinstance(machine_model_value, str) and machine_model_value.isdigit():
            # 如果是纯数字，可能是单个机器ID
            machine_model_value = convert_machine_ids_to_models(machine_model_value)
        elif machine_model_value and isinstance(machine_model_value, str) and ',' in machine_model_value:
            # 如果包含逗号，可能是多个ID
            machine_model_value = convert_machine_ids_to_models(machine_model_value)

        # 创建订单记录
        new_order = Order(
            is_new=data.get('is_new'),
            area=data.get('area', ''),
            customer_name=data.get('customer_name', ''),
            customer_type=data.get('customer_type', ''),
            order_time=datetime.strptime(data.get('order_time'), '%Y-%m-%d').date() if data.get('order_time') else None,
            ship_time=datetime.strptime(data.get('ship_time'), '%Y-%m-%d').date() if data.get('ship_time') else None,
            ship_country=data.get('ship_country'),
            contract_no=data.get('contract_no', ''),
            order_no=data.get('order_no'),
            machine_no=data.get('machine_no'),
            machine_name=data.get('machine_name', '包装机'),
            machine_model=machine_model_value,
            machine_count=data.get('machine_count', 1),
            unit=data.get('unit', 'set'),
            contract_amount=data.get('contract_amount', 0),
            deposit=data.get('deposit', 0),
            balance=data.get('balance', 0),
            tax_rate=data.get('tax_rate', 13.0),
            tax_refund_amount=data.get('tax_refund_amount', 0),
            currency_amount=data.get('currency_amount', 0),
            payment_received=data.get('payment_received', 0),
            machine_cost=data.get('machine_cost', 0),
            net_profit=data.get('net_profit', 0),
            proportionate_cost=data.get('proportionate_cost', 0),
            individual_cost=data.get('individual_cost', 0),
            gross_profit=data.get('gross_profit', 0),
            pay_type=data.get('pay_type', 'T/T'),
            commission=data.get('commission', 0),
            latest_ship_date=datetime.strptime(data.get('latest_ship_date'), '%Y-%m-%d').date() if data.get('latest_ship_date') else None,
            expected_delivery=datetime.strptime(data.get('expected_delivery'), '%Y-%m-%d').date() if data.get('expected_delivery') else None,
            order_dept=data.get('order_dept'),
            check_requirement=data.get('check_requirement'),
            attachment_imgs=data.get('attachment_imgs'),
            attachment_videos=data.get('attachment_videos'),
            creator_id=current_user.emp_id,  # 添加创建者ID
            inquiry_id=inquiry_id  # 添加关联的询盘ID
        )
        db.session.add(new_order)
        db.session.commit()

        # 更新搜索字段
        new_order.search_field = new_order.generate_search_field()
        db.session.commit()

        # 增加订单新增统计数据
        DataChangeStats.increment_stats('order', 'new', 1)
        DataChangeStats.increment_stats('order', 'total', 1)

        # 导入json模块
        import json
        from flask import Response

        # 创建操作日志
        # 记录完整的订单数据
        order_data = new_order.to_dict()
        full_details = {
            "action": "create",
            "user": current_user.name,
            "order_data": order_data
        }

        create_order_log(
            order_id=new_order.id,
            operation_type='create',
            operator_id=current_user.emp_id,
            details=json.dumps(full_details, ensure_ascii=False),
            order_obj=new_order
        )

        # 获取当前用户信息以确定是否为管理员
        is_admin = current_user and current_user.user_role == 'admin'

        # 序列化创建的订单
        order_data = serialize_order(new_order, is_admin=is_admin)

        response_data = {
            "code": 200,
            "msg": "订单创建成功",
            "data": order_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建订单失败: {str(e)}",
            "data": None
        }), 500

@order_bp.route('/orders/<int:order_id>', methods=['GET'])
@route_permission(ROUTE_ORDER)
def get_order(order_id):
    """获取单个订单详情"""
    try:
        order = Order.query.get_or_404(order_id)

        # 获取当前用户
        current_user = get_current_user()

        # 检查权限：管理员可以查看所有，普通用户只能查看自己创建的
        if current_user.user_role != 'admin' and order.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限访问该订单",
                "data": None
            }), 403

        # 获取字段过滤参数
        fields = request.args.get('fields')
        # 获取当前用户信息以确定是否为管理员
        is_admin = current_user and current_user.user_role == 'admin'

        order_data = serialize_order(order, is_admin=is_admin, fields=fields)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取订单详情成功",
            "data": order_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取订单详情失败: {str(e)}",
            "data": None
        }), 500

@order_bp.route('/orders/<int:order_id>', methods=['PUT'])
@route_permission(ROUTE_ORDER)
def update_order(order_id):
    """更新订单信息"""
    try:
        order = Order.query.get_or_404(order_id)

        # 获取当前用户
        current_user = get_current_user()

        # 检查权限：管理员可以修改所有，普通用户只能修改自己创建的
        if current_user.user_role != 'admin' and order.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限修改该订单",
                "data": None
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 如果提供了询盘ID，验证其存在性
        if 'inquiry_id' in data:
            inquiry_id = data['inquiry_id']
            if inquiry_id:
                from app.models.inquiry import Inquiry
                inquiry = Inquiry.query.get(inquiry_id)
                if not inquiry:
                    return jsonify({
                        "code": 400,
                        "msg": "指定的询盘不存在",
                        "data": None
                    }), 400

                # 检查询盘是否已经关联了订单（除了当前订单外）
                if inquiry.has_associated_orders():
                    # 检查是否是当前订单的询盘ID
                    existing_orders = Order.query.filter_by(inquiry_id=inquiry_id).all()
                    if len(existing_orders) > 0:
                        # 如果此询盘已关联其他订单，则不允许关联
                        for existing_order in existing_orders:
                            if existing_order.id != order_id:
                                return jsonify({
                                    "code": 400,
                                    "msg": "该询盘已关联其他订单，不能重复关联",
                                    "data": None
                                }), 400

                order.inquiry_id = inquiry_id
            else:
                # 如果传入空值，清除关联
                order.inquiry_id = None

        # 记录修改前的数据
        old_data = order.to_dict()

        # 处理机器型号字段 - 如果传入的是机器ID，则转换为对应的型号
        if 'machine_model' in data:
            machine_model_value = data['machine_model']
            if machine_model_value and isinstance(machine_model_value, str) and machine_model_value.isdigit():
                # 如果是纯数字，可能是单个机器ID
                machine_model_value = convert_machine_ids_to_models(machine_model_value)
            elif machine_model_value and isinstance(machine_model_value, str) and ',' in machine_model_value:
                # 如果包含逗号，可能是多个ID
                machine_model_value = convert_machine_ids_to_models(machine_model_value)
            order.machine_model = machine_model_value
        else:
            # 如果没有提供machine_model，则不更新此字段
            pass

        # 更新订单字段（排除machine_model，因为已经单独处理）
        if 'is_new' in data: order.is_new = data['is_new']
        if 'area' in data: order.area = data['area']
        if 'customer_name' in data: order.customer_name = data['customer_name']
        if 'customer_type' in data: order.customer_type = data['customer_type']
        if 'order_time' in data and data['order_time']: order.order_time = datetime.strptime(data['order_time'], '%Y-%m-%d').date()
        if 'ship_time' in data and data['ship_time']: order.ship_time = datetime.strptime(data['ship_time'], '%Y-%m-%d').date()
        if 'ship_country' in data: order.ship_country = data['ship_country']
        if 'contract_no' in data: order.contract_no = data['contract_no']
        if 'order_no' in data: order.order_no = data['order_no']
        if 'machine_no' in data: order.machine_no = data['machine_no']
        if 'machine_name' in data: order.machine_name = data['machine_name']
        if 'machine_count' in data: order.machine_count = data['machine_count']
        if 'unit' in data: order.unit = data['unit']
        if 'contract_amount' in data: order.contract_amount = data['contract_amount']
        if 'deposit' in data: order.deposit = data['deposit']
        if 'balance' in data: order.balance = data['balance']
        if 'tax_rate' in data: order.tax_rate = data['tax_rate']
        if 'tax_refund_amount' in data: order.tax_refund_amount = data['tax_refund_amount']
        if 'currency_amount' in data: order.currency_amount = data['currency_amount']
        if 'payment_received' in data: order.payment_received = data['payment_received']
        if 'machine_cost' in data: order.machine_cost = data['machine_cost']
        if 'net_profit' in data: order.net_profit = data['net_profit']
        if 'proportionate_cost' in data: order.proportionate_cost = data['proportionate_cost']
        if 'individual_cost' in data: order.individual_cost = data['individual_cost']
        if 'gross_profit' in data: order.gross_profit = data['gross_profit']
        if 'pay_type' in data: order.pay_type = data['pay_type']
        if 'commission' in data: order.commission = data['commission']
        if 'latest_ship_date' in data and data['latest_ship_date']: order.latest_ship_date = datetime.strptime(data['latest_ship_date'], '%Y-%m-%d').date()
        if 'expected_delivery' in data and data['expected_delivery']: order.expected_delivery = datetime.strptime(data['expected_delivery'], '%Y-%m-%d').date()
        if 'order_dept' in data: order.order_dept = data['order_dept']
        if 'check_requirement' in data: order.check_requirement = data['check_requirement']
        if 'attachment_imgs' in data: order.attachment_imgs = data['attachment_imgs']
        if 'attachment_videos' in data: order.attachment_videos = data['attachment_videos']

        # 更新搜索字段
        order.search_field = order.generate_search_field()
        db.session.commit()

        # 导入json模块
        import json
        from flask import Response

        # 创建操作日志
        # 记录修改的字段
        updated_fields = {}
        for field in ['is_new', 'area', 'customer_name', 'customer_type', 'order_time', 'ship_time',
                     'ship_country', 'contract_no', 'order_no', 'machine_no', 'machine_name',
                     'machine_model', 'machine_count', 'unit', 'contract_amount', 'deposit',
                     'balance', 'tax_rate', 'tax_refund_amount', 'currency_amount', 'payment_received',
                     'machine_cost', 'net_profit', 'proportionate_cost', 'individual_cost', 'gross_profit',
                     'pay_type', 'commission', 'latest_ship_date', 'expected_delivery', 'order_dept',
                     'check_requirement', 'attachment_imgs', 'attachment_videos', 'inquiry_id']:
            if field in data:
                old_value = old_data.get(field)
                new_value = data[field]
                # 特殊处理日期字段
                if field in ['order_time', 'ship_time', 'latest_ship_date', 'expected_delivery']:
                    if data[field]:
                        new_value = datetime.strptime(data[field], '%Y-%m-%d').date().strftime('%Y-%m-%d')
                updated_fields[field] = {'old': old_value, 'new': new_value}

        details = {
            "action": "update",
            "user": current_user.name,
            "updated_fields": updated_fields
        }

        create_order_log(
            order_id=order.id,
            operation_type='update',
            operator_id=current_user.emp_id,
            details=json.dumps(details, ensure_ascii=False),
            order_obj=order
        )

        # 获取当前用户信息以确定是否为管理员
        current_user = get_current_user()
        is_admin = current_user and current_user.user_role == 'admin'

        order_data = serialize_order(order, is_admin=is_admin)

        response_data = {
            "code": 200,
            "msg": "订单更新成功",
            "data": order_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新订单失败: {str(e)}",
            "data": None
        }), 500

@order_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@route_permission(ROUTE_ORDER)
def delete_order(order_id):
    """删除订单"""
    try:
        order = Order.query.get_or_404(order_id)

        # 获取当前用户
        current_user = get_current_user()

        # 检查权限：管理员可以删除所有，普通用户只能删除自己创建的
        if current_user.user_role != 'admin' and order.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限删除该订单",
                "data": None
            }), 403

        # 检查订单是否有关联的订单状态记录
        from app.models.order_status import OrderStatus
        order_status = OrderStatus.query.filter_by(order_id=order_id).first()
        if order_status:
            return jsonify({
                "code": 400,
                "msg": "该订单已关联订单状态记录，无法删除",
                "data": None
            }), 400

        # 记录完整订单数据
        order_data = order.to_dict()

        # 记录关联的询盘ID，以便后续处理
        inquiry_id = order.inquiry_id

        # 删除关联的个别费用记录
        from app.models.expense import IndividualExpense
        IndividualExpense.query.filter_by(order_id=order_id).delete(synchronize_session=False)

        # 减少订单总统计数据
        DataChangeStats.increment_stats('order', 'total', -1)

        # 导入json模块
        import json

        # 删除订单
        db.session.delete(order)
        db.session.commit()

        # 创建操作日志
        details = {
            "action": "delete",
            "user": current_user.name,
            "order_data": order_data
        }

        create_order_log(
            order_id=0,  # 删除后订单已不存在，使用0
            operation_type='delete',
            operator_id=current_user.emp_id,
            details=json.dumps(details, ensure_ascii=False),
            order_obj=order  # 传递原订单对象以获取客户名称
        )

        # 如果订单有关联的询盘，在订单删除后处理询盘状态（移除关联）
        if inquiry_id:
            from app.models.inquiry import Inquiry
            inquiry = Inquiry.query.get(inquiry_id)
            if inquiry:
                # 由于数据库会自动处理外键约束，我们先确保没有其他地方引用后再处理关联
                pass

        return jsonify({
            "code": 200,
            "msg": "订单删除成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除订单失败: {str(e)}",
            "data": None
        }), 500

@order_bp.route('/orders/statistics', methods=['GET'])
@route_permission(ROUTE_ORDER)
def get_order_statistics():
    """获取订单统计信息"""
    try:
        # 获取当前用户信息以确定是否为管理员
        current_user = get_current_user()
        is_admin = current_user and current_user.user_role == 'admin'

        # 构建查询
        query = Order.query

        # 检查是否为管理员，如果不是管理员则只统计自己创建的数据
        if current_user.user_role != 'admin':
            query = query.filter(Order.creator_id == current_user.emp_id)

        # 计算总订单数
        total_orders = query.count()
        # 计算总金额
        total_amount = db.session.query(db.func.sum(Order.contract_amount)).filter(
            Order.creator_id == current_user.emp_id if current_user.user_role != 'admin' else True
        ).scalar() or 0.0

        statistics_data = {
            'total_orders': total_orders,
            'total_amount': float(total_amount)
        }

        # 仅对管理员显示敏感统计信息
        if is_admin:
            # 计算总毛利
            total_gross_profit = db.session.query(
                db.func.sum(Order.gross_profit)
            ).filter(
                Order.creator_id == current_user.emp_id if current_user.user_role != 'admin' else True
            ).scalar() or 0.0
            # 计算总净利
            total_net_profit = db.session.query(
                db.func.sum(Order.net_profit)
            ).filter(
                Order.creator_id == current_user.emp_id if current_user.user_role != 'admin' else True
            ).scalar() or 0.0

            statistics_data.update({
                'total_gross_profit': float(total_gross_profit),
                'total_net_profit': float(total_net_profit)
            })

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取订单统计成功",
            "data": statistics_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取订单统计失败: {str(e)}",
            "data": None
        }), 500


@order_bp.route('/orders/expense-summary', methods=['GET'])
@route_permission(ROUTE_ORDER)
def get_order_expense_summary():
    """获取订单费用分摊汇总信息"""
    try:
        # 获取当前用户信息以确定是否为管理员
        current_user = get_current_user()
        is_admin = current_user and current_user.user_role == 'admin'

        # 获取查询参数中的年份
        target_year = request.args.get('year', type=int)
        if not target_year:
            target_year = datetime.now().year  # 默认为当前年份

        # 构建查询
        query = Order.query
        if current_user.user_role != 'admin':
            query = query.filter(Order.creator_id == current_user.emp_id)

        # 计算该年度的订单总数
        total_orders = query.filter(
            db.extract('year', Order.create_time) == target_year
        ).count()

        # 计算该年度的订单总金额
        total_contract_amount = db.session.query(
            db.func.sum(Order.contract_amount)
        ).filter(
            db.extract('year', Order.create_time) == target_year
        ).filter(
            Order.creator_id == current_user.emp_id if current_user.user_role != 'admin' else True
        ).scalar() or 0.0

        # 计算该年度的总毛利
        total_gross_profit = db.session.query(
            db.func.sum(Order.gross_profit)
        ).filter(
            db.extract('year', Order.create_time) == target_year
        ).filter(
            Order.creator_id == current_user.emp_id if current_user.user_role != 'admin' else True
        ).scalar() or 0.0

        # 计算该年度的费用分摊总金额
        from app.models.expense import Expense, ExpenseAllocation
        total_expense_allocation = db.session.query(
            db.func.sum(ExpenseAllocation.allocated_amount)
        ).join(Expense, ExpenseAllocation.expense_id == Expense.id).filter(
            Expense.target_year == target_year
        ).scalar() or 0.0

        # 计算更新时间（最后计算费用分摊的时间）
        from app.models.expense import ExpenseCalculationRecord
        latest_calc = ExpenseCalculationRecord.query.filter(
            ExpenseCalculationRecord.target_year == target_year
        ).order_by(ExpenseCalculationRecord.calculation_time.desc()).first()

        # 获取年度目标
        annual_target_record = AnnualTarget.query.filter_by(target_year=target_year).first()
        annual_target = float(annual_target_record.target_amount) if annual_target_record else 10000000.00

        summary_data = {
            'year': target_year,
            'total_orders': total_orders,
            'total_contract_amount': float(total_contract_amount),
            'total_gross_profit': float(total_gross_profit),
            'total_expense_allocation': float(total_expense_allocation),
            'net_profit_estimate': float(total_gross_profit) - float(total_expense_allocation),
            'last_updated': latest_calc.calculation_time.strftime('%Y-%m-%d %H:%M:%S') if latest_calc else '未计算',
            'calculation_status': latest_calc.status if latest_calc else '未计算',
            'annual_target': annual_target
        }

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": f"获取{target_year}年订单费用汇总成功",
            "data": summary_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取订单费用汇总失败: {str(e)}",
            "data": None
        }), 500


@order_bp.route('/orders/update-proportionate-cost', methods=['POST'])
@route_permission(ROUTE_ORDER)
def update_order_proportionate_cost():
    """更新订单摊分费用 - 按订单金额比例分摊到指定年度的所有订单"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        target_year = data.get('target_year')
        if not target_year:
            return jsonify({
                "code": 400,
                "msg": "必须指定目标年份",
                "data": None
            }), 400

        # 获取年度目标
        annual_target_record = AnnualTarget.query.filter_by(target_year=target_year).first()
        if not annual_target_record:
            # 如果没有找到对应年份的年度目标，则使用默认值创建
            annual_target_record = AnnualTarget(
                target_year=target_year,
                target_amount=10000000.00
            )
            db.session.add(annual_target_record)
            db.session.commit()

        annual_target = float(annual_target_record.target_amount) if annual_target_record.target_amount else 10000000.00

        # 获取该年份的所有费用记录
        expenses = Expense.query.filter(Expense.target_year == target_year, Expense.expense_type == '全面分摊').all()

        if not expenses:
            # 创建计算记录
            calc_record = ExpenseCalculationRecord(
                calculation_time=datetime.now(),
                target_year=target_year,
                status='completed',
                remark='该年份没有需要分摊的费用'
            )
            db.session.add(calc_record)
            db.session.commit()

            return jsonify({
                "code": 200,
                "msg": f"该年份({target_year})没有需要分摊的费用",
                "data": {
                    "target_year": target_year,
                    "total_expenses": 0,
                    "total_orders": 0,
                    "calculation_time": calc_record.calculation_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            })

        # 获取该年份的所有订单
        # 获取当前用户信息
        current_user = get_current_user()
        # 如果不是管理员，只处理该用户创建的订单
        orders_query = Order.query.filter(
            db.extract('year', Order.create_time) == target_year
        )
        if current_user.user_role != 'admin':
            orders_query = orders_query.filter(Order.creator_id == current_user.emp_id)

        orders = orders_query.all()

        if not orders:
            # 创建计算记录
            calc_record = ExpenseCalculationRecord(
                calculation_time=datetime.now(),
                target_year=target_year,
                status='completed',
                remark=f'该年份({target_year})没有订单，无法分摊费用'
            )
            db.session.add(calc_record)
            db.session.commit()

            return jsonify({
                "code": 200,
                "msg": f"该年份({target_year})没有订单，无法分摊费用",
                "data": {
                    "target_year": target_year,
                    "total_expenses": len(expenses),
                    "total_orders": 0,
                    "calculation_time": calc_record.calculation_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            })

        # 计算所有订单的总金额
        total_order_amount = sum(
            float(order.contract_amount) if order.contract_amount else 0.0
            for order in orders
        )

        # 计算摊分总额（年度目标和订单总金额中的较大值）
        allocation_base = max(annual_target, total_order_amount)

        if allocation_base <= 0:
            # 创建计算记录
            calc_record = ExpenseCalculationRecord(
                calculation_time=datetime.now(),
                target_year=target_year,
                status='completed',
                remark=f'该年份({target_year})摊分基础金额为0，无法按比例分摊'
            )
            db.session.add(calc_record)
            db.session.commit()

            return jsonify({
                "code": 200,
                "msg": f"该年份({target_year})摊分基础金额为0，无法按比例分摊",
                "data": {
                    "target_year": target_year,
                    "total_expenses": len(expenses),
                    "total_orders": len(orders),
                    "total_order_amount": total_order_amount,
                    "annual_target": annual_target,
                    "allocation_base": allocation_base,
                    "calculation_time": calc_record.calculation_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            })

        # 更新每个订单的proportionate_cost字段
        for order in orders:
            order_amount = float(order.contract_amount) if order.contract_amount else 0.0
            if allocation_base > 0:
                # 计算该订单应分摊的费用总和
                order_total_expense = sum(
                    (order_amount / allocation_base) * float(expense.amount) if expense.amount else 0.0
                    for expense in expenses
                )

                # 更新订单的摊分费用字段
                order.proportionate_cost = order_total_expense
            else:
                order.proportionate_cost = 0.0

        # 创建计算记录
        calc_record = ExpenseCalculationRecord(
            calculation_time=datetime.now(),
            target_year=target_year,
            status='completed',
            remark=f'成功更新{len(orders)}个订单的摊分费用'
        )
        db.session.add(calc_record)
        db.session.commit()

        # 计算订单的总成本
        total_direct_cost = sum(
            float(order.machine_cost) if order.machine_cost else 0.0
            for order in orders
        )

        # 计算总净利 (订单金额 - 成本 - 摊分费用)
        total_net_profit = total_order_amount - total_direct_cost - sum(
            float(expense.amount) if expense.amount else 0.0
            for expense in expenses
        )

        # 计算总费用
        total_expense_amount = sum(
            float(expense.amount) if expense.amount else 0.0
            for expense in expenses
        )

        # 计算总毛利 (订单金额 - 成本)
        total_gross_profit = total_order_amount - total_direct_cost

        return jsonify({
            "code": 200,
            "msg": "订单摊分费用更新完成",
            "data": {
                "target_year": target_year,
                "total_expenses": len(expenses),
                "total_orders": len(orders),
                "total_order_amount": total_order_amount,
                "annual_target": annual_target,
                "allocation_base": allocation_base,
                "total_net_profit": total_net_profit,
                "total_gross_profit": total_gross_profit,
                "total_direct_cost": total_direct_cost,
                "total_expense_amount": total_expense_amount,
                "calculation_time": calc_record.calculation_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        db.session.rollback()
        # 创建失败的计算记录
        calc_record = ExpenseCalculationRecord(
            calculation_time=datetime.now(),
            target_year=target_year if 'target_year' in locals() else data.get('target_year') if 'data' in locals() else 0,
            status='failed',
            remark=f'订单摊分费用更新失败: {str(e)}'
        )
        db.session.add(calc_record)
        db.session.commit()

        return jsonify({
            "code": 500,
            "msg": f"订单摊分费用更新失败: {str(e)}",
            "data": None
        }), 500


@order_bp.route('/order-logs', methods=['GET'])
@route_permission(ROUTE_ORDER)
def get_order_logs():
    """获取订单日志列表（仅管理员）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 获取筛选参数
        operation_type = request.args.get('operation_type')
        operator_name = request.args.get('operator_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 构建查询 - 只查找模块为order的日志
        query = BusinessOperationLog.query.filter(BusinessOperationLog.module == 'order')

        # 应用筛选条件
        if operation_type:
            query = query.filter(BusinessOperationLog.operation_type.contains(operation_type))
        if operator_name:
            query = query.join(Employee).filter(Employee.name.contains(operator_name))
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(BusinessOperationLog.create_time >= start_datetime)
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(BusinessOperationLog.create_time < end_datetime)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        logs = query.order_by(BusinessOperationLog.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 序列化日志数据
        logs_list = [log.to_dict() for log in logs]

        # 从新的统计数据模型获取统计信息
        # 获取订单统计
        order_total_stats = DataChangeStats.query.filter_by(module='order', stats_type='total').first()
        order_new_stats = DataChangeStats.query.filter_by(module='order', stats_type='new').first()

        # 计算订单统计信息
        statistics = {
            "total_orders": order_total_stats.stats_value if order_total_stats else 0,
            "new_orders": order_new_stats.stats_value if order_new_stats else 0,
            # 为前端添加兼容字段
            "total_main": order_total_stats.stats_value if order_total_stats else 0,
            "new_main": order_new_stats.stats_value if order_new_stats else 0,
            "total_sub": 0,  # 订单没有子类型，设为0
            "new_sub": 0,    # 订单没有子类型，设为0
            "monthly_main": 0,  # 月度统计可按需实现
            "monthly_sub": 0    # 月度统计可按需实现
        }

        response_data = {
            "code": 200,
            "msg": "获取订单日志成功",
            "data": {
                "list": logs_list,
                "total": total,
                "page": page,
                "size": size,
                "statistics": statistics
            }
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取订单日志失败: {str(e)}",
            "data": None
        }), 500