from flask import Blueprint, request, jsonify
from extensions import db
from app.models.order_list import OrderList
from app.models.employee import Employee
from datetime import datetime, timedelta
import json
from decimal import Decimal

# 创建蓝图
order_bp = Blueprint('order', __name__)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

def serialize_order(order, include_expense_allocations=False):
    """将订单对象转换为字典格式"""
    order_dict = {
        'id': order.id,
        'is_new': order.is_new,
        'area': order.area,
        'customer_name': order.customer_name,
        'customer_type': order.customer_type,
        'order_time': order.order_time.strftime('%Y-%m-%d') if order.order_time else None,
        'ship_time': order.ship_time.strftime('%Y-%m-%d') if order.ship_time else None,
        'ship_country': order.ship_country,
        'contract_no': order.contract_no,
        'order_no': order.order_no,
        'machine_no': order.machine_no,
        'machine_name': order.machine_name,
        'machine_model': order.machine_model,
        'machine_count': order.machine_count,
        'unit': order.unit,
        'contract_amount': float(order.contract_amount) if order.contract_amount else 0.0,
        'deposit': float(order.deposit) if order.deposit else 0.0,
        'balance': float(order.balance) if order.balance else 0.0,
        'tax_refund_amount': float(order.tax_refund_amount) if order.tax_refund_amount else 0.0,
        'currency_amount': float(order.currency_amount) if order.currency_amount else 0.0,
        'payment_received': float(order.payment_received) if order.payment_received else 0.0,
        'direct_cost': float(order.direct_cost) if order.direct_cost else 0.0,
        'commission': float(order.commission) if order.commission else 0.0,
        'allocated_cost': float(order.allocated_cost) if order.allocated_cost else 0.0,
        'custom_income': float(order.custom_income) if order.custom_income else 0.0,
        'custom_expense': float(order.custom_expense) if order.custom_expense else 0.0,
        'gross_profit': float(order.gross_profit) if order.gross_profit else 0.0,
        'net_profit': float(order.net_profit) if order.net_profit else 0.0,
        'pay_type': order.pay_type,
        'latest_ship_date': order.latest_ship_date.strftime('%Y-%m-%d') if order.latest_ship_date else None,
        'expected_delivery': order.expected_delivery.strftime('%Y-%m-%d') if order.expected_delivery else None,
        'order_dept': order.order_dept,
        'check_requirement': order.check_requirement,
        'attachment_imgs': order.attachment_imgs,
        'attachment_videos': order.attachment_videos,
        'create_time': order.create_time.strftime('%Y-%m-%d %H:%M:%S') if order.create_time else None,
        'update_time': order.update_time.strftime('%Y-%m-%d %H:%M:%S') if order.update_time else None
    }
    
    # 如果需要包含费用分摊信息
    if include_expense_allocations:
        # 计算该订单的费用分摊总额
        from app.models.expense import ExpenseAllocation
        total_expense_allocation = db.session.query(
            db.func.sum(ExpenseAllocation.allocated_amount)
        ).filter(ExpenseAllocation.order_id == order.id).scalar() or 0.0
        
        order_dict['total_expense_allocation'] = float(total_expense_allocation)
        # 重新计算净利，减去费用分摊
        order_dict['net_profit_with_expense'] = order_dict['gross_profit'] - order_dict['allocated_cost'] - order_dict['total_expense_allocation']
    
    return order_dict

@order_bp.route('/orders', methods=['GET'])
def get_orders():
    """获取订单列表，支持分页和筛选"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        # 获取筛选参数
        customer_name = request.args.get('customer_name')
        order_no = request.args.get('order_no')
        machine_name = request.args.get('machine_name')
        area = request.args.get('area')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        is_new = request.args.get('is_new', type=int)
        ship_country = request.args.get('ship_country')
        order_dept = request.args.get('order_dept')
        pay_type = request.args.get('pay_type')
        customer_type = request.args.get('customer_type')
        order_status = request.args.get('order_status')  # 可以是 'unshipped', 'shipped', 'completed' 等

        # 构建查询
        query = OrderList.query

        # 应用筛选条件
        if customer_name:
            query = query.filter(OrderList.customer_name.contains(customer_name))
        if order_no:
            query = query.filter(OrderList.order_no.contains(order_no))
        if machine_name:
            query = query.filter(OrderList.machine_name.contains(machine_name))
        if area:
            query = query.filter(OrderList.area.contains(area))
        if is_new is not None:
            query = query.filter(OrderList.is_new == is_new)
        if ship_country:
            query = query.filter(OrderList.ship_country.contains(ship_country))
        if order_dept:
            query = query.filter(OrderList.order_dept.contains(order_dept))
        if pay_type:
            query = query.filter(OrderList.pay_type.contains(pay_type))
        if customer_type:
            query = query.filter(OrderList.customer_type.contains(customer_type))
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(OrderList.order_time >= start_datetime)
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(OrderList.order_time < end_datetime)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        orders = query.order_by(OrderList.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 检查是否需要包含费用分摊信息
        include_expense_allocations = request.args.get('include_expense_allocations', 'false').lower() == 'true'
        
        # 序列化订单数据
        orders_list = [serialize_order(order, include_expense_allocations=include_expense_allocations) for order in orders]

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

        # 创建订单记录
        new_order = OrderList(
            is_new=data.get('is_new'),
            area=data.get('area'),
            customer_name=data.get('customer_name'),
            customer_type=data.get('customer_type'),
            order_time=datetime.strptime(data.get('order_time'), '%Y-%m-%d').date() if data.get('order_time') else None,
            ship_time=datetime.strptime(data.get('ship_time'), '%Y-%m-%d').date() if data.get('ship_time') else None,
            ship_country=data.get('ship_country'),
            contract_no=data.get('contract_no'),
            order_no=data.get('order_no'),
            machine_no=data.get('machine_no'),
            machine_name=data.get('machine_name'),
            machine_model=data.get('machine_model'),
            machine_count=data.get('machine_count'),
            unit=data.get('unit'),
            contract_amount=data.get('contract_amount'),
            deposit=data.get('deposit'),
            balance=data.get('balance'),
            tax_refund_amount=data.get('tax_refund_amount'),
            currency_amount=data.get('currency_amount'),
            payment_received=data.get('payment_received'),
            direct_cost=data.get('direct_cost'),
            commission=data.get('commission'),
            allocated_cost=data.get('allocated_cost'),
            custom_income=data.get('custom_income', 0),
            custom_expense=data.get('custom_expense', 0),
            gross_profit=data.get('gross_profit'),
            net_profit=data.get('net_profit'),
            pay_type=data.get('pay_type'),
            latest_ship_date=datetime.strptime(data.get('latest_ship_date'), '%Y-%m-%d').date() if data.get('latest_ship_date') else None,
            expected_delivery=datetime.strptime(data.get('expected_delivery'), '%Y-%m-%d').date() if data.get('expected_delivery') else None,
            order_dept=data.get('order_dept'),
            check_requirement=data.get('check_requirement'),
            attachment_imgs=data.get('attachment_imgs'),
            attachment_videos=data.get('attachment_videos')
        )
        db.session.add(new_order)
        db.session.commit()

        # 序列化创建的订单
        order_data = serialize_order(new_order)

        import json
        from flask import Response
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
def get_order(order_id):
    """获取单个订单详情"""
    try:
        order = OrderList.query.get_or_404(order_id)
        order_data = serialize_order(order)

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
def update_order(order_id):
    """更新订单信息"""
    try:
        order = OrderList.query.get_or_404(order_id)
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 更新订单字段
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
        if 'machine_model' in data: order.machine_model = data['machine_model']
        if 'machine_count' in data: order.machine_count = data['machine_count']
        if 'unit' in data: order.unit = data['unit']
        if 'contract_amount' in data: order.contract_amount = data['contract_amount']
        if 'deposit' in data: order.deposit = data['deposit']
        if 'balance' in data: order.balance = data['balance']
        if 'tax_refund_amount' in data: order.tax_refund_amount = data['tax_refund_amount']
        if 'currency_amount' in data: order.currency_amount = data['currency_amount']
        if 'payment_received' in data: order.payment_received = data['payment_received']
        if 'direct_cost' in data: order.direct_cost = data['direct_cost']
        if 'commission' in data: order.commission = data['commission']
        if 'allocated_cost' in data: order.allocated_cost = data['allocated_cost']
        if 'custom_income' in data: order.custom_income = data['custom_income']
        if 'custom_expense' in data: order.custom_expense = data['custom_expense']
        if 'gross_profit' in data: order.gross_profit = data['gross_profit']
        if 'net_profit' in data: order.net_profit = data['net_profit']
        if 'pay_type' in data: order.pay_type = data['pay_type']
        if 'latest_ship_date' in data and data['latest_ship_date']: order.latest_ship_date = datetime.strptime(data['latest_ship_date'], '%Y-%m-%d').date()
        if 'expected_delivery' in data and data['expected_delivery']: order.expected_delivery = datetime.strptime(data['expected_delivery'], '%Y-%m-%d').date()
        if 'order_dept' in data: order.order_dept = data['order_dept']
        if 'check_requirement' in data: order.check_requirement = data['check_requirement']
        if 'attachment_imgs' in data: order.attachment_imgs = data['attachment_imgs']
        if 'attachment_videos' in data: order.attachment_videos = data['attachment_videos']

        db.session.commit()
        order_data = serialize_order(order)

        import json
        from flask import Response
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
def delete_order(order_id):
    """删除订单"""
    try:
        order = OrderList.query.get_or_404(order_id)
        db.session.delete(order)
        db.session.commit()

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
def get_order_statistics():
    """获取订单统计信息"""
    try:
        # 计算总订单数
        total_orders = db.session.query(db.func.count(OrderList.id)).scalar()
        # 计算总金额
        total_amount = db.session.query(db.func.sum(OrderList.contract_amount)).scalar() or 0.0
        # 计算总毛利
        total_gross_profit = db.session.query(db.func.sum(OrderList.gross_profit)).scalar() or 0.0
        # 计算总净利
        total_net_profit = db.session.query(db.func.sum(OrderList.net_profit)).scalar() or 0.0

        statistics_data = {
            'total_orders': total_orders,
            'total_amount': float(total_amount),
            'total_gross_profit': float(total_gross_profit),
            'total_net_profit': float(total_net_profit)
        }

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
def get_order_expense_summary():
    """获取订单费用分摊汇总信息"""
    try:
        # 获取查询参数中的年份
        target_year = request.args.get('year', type=int)
        if not target_year:
            target_year = datetime.now().year  # 默认为当前年份

        # 计算该年度的订单总数
        total_orders = db.session.query(db.func.count(OrderList.id)).filter(
            db.extract('year', OrderList.create_time) == target_year
        ).scalar() or 0

        # 计算该年度的订单总金额
        total_contract_amount = db.session.query(
            db.func.sum(OrderList.contract_amount)
        ).filter(
            db.extract('year', OrderList.create_time) == target_year
        ).scalar() or 0.0

        # 计算该年度的总毛利
        total_gross_profit = db.session.query(
            db.func.sum(OrderList.gross_profit)
        ).filter(
            db.extract('year', OrderList.create_time) == target_year
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

        summary_data = {
            'year': target_year,
            'total_orders': total_orders,
            'total_contract_amount': float(total_contract_amount),
            'total_gross_profit': float(total_gross_profit),
            'total_expense_allocation': float(total_expense_allocation),
            'net_profit_estimate': float(total_gross_profit) - float(total_expense_allocation),
            'last_updated': latest_calc.calculation_time.strftime('%Y-%m-%d %H:%M:%S') if latest_calc else '未计算',
            'calculation_status': latest_calc.status if latest_calc else '未计算'
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