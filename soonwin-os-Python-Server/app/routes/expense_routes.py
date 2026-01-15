from flask import Blueprint, request, jsonify
from extensions import db
from app.models.expense import Expense, ExpenseAllocation, ExpenseCalculationRecord, AnnualTarget, IndividualExpense
from app.models.order import Order
from app.utils.auth_utils import require_admin
from datetime import datetime, date, timedelta
import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def serialize_expense(expense):
    """将费用对象转换为字典格式"""
    return {
        'id': expense.id,
        'name': expense.name,
        'amount': float(expense.amount) if expense.amount else 0.0,
        'expense_type': expense.expense_type,
        'target_year': expense.target_year,
        'remark': expense.remark,
        'create_time': expense.create_time.strftime('%Y-%m-%d %H:%M:%S') if expense.create_time else None,
        'update_time': expense.update_time.strftime('%Y-%m-%d %H:%M:%S') if expense.update_time else None
    }


def serialize_expense_allocation(allocation):
    """将费用分摊对象转换为字典格式"""
    return {
        'id': allocation.id,
        'expense_id': allocation.expense_id,
        'order_id': allocation.order_id,
        'allocated_amount': float(allocation.allocated_amount) if allocation.allocated_amount else 0.0,
        'create_time': allocation.create_time.strftime('%Y-%m-%d %H:%M:%S') if allocation.create_time else None
    }


def serialize_calculation_record(record):
    """将费用计算记录对象转换为字典格式"""
    return {
        'id': record.id,
        'calculation_time': record.calculation_time.strftime('%Y-%m-%d %H:%M:%S') if record.calculation_time else None,
        'target_year': record.target_year,
        'status': record.status,
        'remark': record.remark
    }


def serialize_annual_target(annual_target):
    """将年度目标对象转换为字典格式"""
    return {
        'id': annual_target.id,
        'target_year': annual_target.target_year,
        'target_amount': float(annual_target.target_amount) if annual_target.target_amount else 0.0,
        'create_time': annual_target.create_time.strftime('%Y-%m-%d %H:%M:%S') if annual_target.create_time else None,
        'update_time': annual_target.update_time.strftime('%Y-%m-%d %H:%M:%S') if annual_target.update_time else None
    }


def serialize_individual_expense(individual_expense):
    """将个别费用对象转换为字典格式"""
    return {
        'id': individual_expense.id,
        'order_id': individual_expense.order_id,
        'name': individual_expense.name,
        'amount': float(individual_expense.amount) if individual_expense.amount else 0.0,
        'remark': individual_expense.remark,
        'create_time': individual_expense.create_time.strftime('%Y-%m-%d %H:%M:%S') if individual_expense.create_time else None,
        'update_time': individual_expense.update_time.strftime('%Y-%m-%d %H:%M:%S') if individual_expense.update_time else None
    }


# 创建蓝图
expense_bp = Blueprint('expense', __name__)


@expense_bp.route('/expenses', methods=['GET'])
@require_admin
def get_expenses():
    """获取费用列表，支持分页和筛选"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 获取筛选参数
        name = request.args.get('name')
        target_year = request.args.get('target_year', type=int)
        expense_type = request.args.get('expense_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 构建查询
        query = Expense.query

        # 应用筛选条件
        if name:
            query = query.filter(Expense.name.contains(name))
        if target_year:
            query = query.filter(Expense.target_year == target_year)
        if expense_type:
            query = query.filter(Expense.expense_type == expense_type)
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Expense.create_time >= start_datetime)
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Expense.create_time < end_datetime)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        expenses = query.order_by(Expense.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 序列化费用数据
        expenses_list = [serialize_expense(expense) for expense in expenses]

        # 返回统一格式的数据
        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取费用列表成功",
            "data": {
                "list": expenses_list,
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
            "msg": f"获取费用列表失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/expenses', methods=['POST'])
@require_admin
def create_expense():
    """创建费用记录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 创建费用记录
        new_expense = Expense(
            name=data.get('name'),
            amount=data.get('amount'),
            expense_type=data.get('expense_type', '全面分摊'),
            target_year=data.get('target_year'),
            remark=data.get('remark')
        )
        db.session.add(new_expense)
        db.session.commit()

        # 序列化创建的费用记录
        expense_data = serialize_expense(new_expense)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "费用创建成功",
            "data": expense_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建费用失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/expenses/<int:expense_id>', methods=['GET'])
@require_admin
def get_expense(expense_id):
    """获取单个费用详情"""
    try:
        expense = Expense.query.get_or_404(expense_id)
        expense_data = serialize_expense(expense)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取费用详情成功",
            "data": expense_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取费用详情失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
@require_admin
def update_expense(expense_id):
    """更新费用记录"""
    try:
        expense = Expense.query.get_or_404(expense_id)
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 更新费用字段
        if 'name' in data: expense.name = data['name']
        if 'amount' in data: expense.amount = data['amount']
        if 'expense_type' in data: expense.expense_type = data['expense_type']
        if 'target_year' in data: expense.target_year = data['target_year']
        if 'remark' in data: expense.remark = data['remark']

        db.session.commit()
        expense_data = serialize_expense(expense)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "费用更新成功",
            "data": expense_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新费用失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
@require_admin
def delete_expense(expense_id):
    """删除费用记录"""
    try:
        expense = Expense.query.get_or_404(expense_id)

        # 删除相关的费用分摊记录
        ExpenseAllocation.query.filter_by(expense_id=expense_id).delete()

        db.session.delete(expense)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "费用删除成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除费用失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/expense-allocations', methods=['GET'])
@require_admin
def get_expense_allocations():
    """获取费用分摊列表"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 获取筛选参数
        expense_id = request.args.get('expense_id', type=int)
        order_id = request.args.get('order_id', type=int)
        target_year = request.args.get('target_year', type=int)

        # 构建查询
        query = ExpenseAllocation.query

        # 关联Expense表以进行年份筛选
        if target_year:
            query = query.join(Expense).filter(Expense.target_year == target_year)
        if expense_id:
            query = query.filter(ExpenseAllocation.expense_id == expense_id)
        if order_id:
            query = query.filter(ExpenseAllocation.order_id == order_id)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        allocations = query.order_by(ExpenseAllocation.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 序列化费用分摊数据
        allocations_list = [serialize_expense_allocation(allocation) for allocation in allocations]

        # 返回统一格式的数据
        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取费用分摊列表成功",
            "data": {
                "list": allocations_list,
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
            "msg": f"获取费用分摊列表失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/expense-calculation-records', methods=['GET'])
@require_admin
def get_calculation_records():
    """获取费用计算记录列表"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 获取筛选参数
        target_year = request.args.get('target_year', type=int)
        status = request.args.get('status')

        # 构建查询
        query = ExpenseCalculationRecord.query

        # 应用筛选条件
        if target_year:
            query = query.filter(ExpenseCalculationRecord.target_year == target_year)
        if status:
            query = query.filter(ExpenseCalculationRecord.status == status)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        records = query.order_by(ExpenseCalculationRecord.calculation_time.desc()).offset((page - 1) * size).limit(size).all()

        # 序列化计算记录数据
        records_list = [serialize_calculation_record(record) for record in records]

        # 返回统一格式的数据
        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取费用计算记录列表成功",
            "data": {
                "list": records_list,
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
            "msg": f"获取费用计算记录列表失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/calculate-expense-allocations', methods=['POST'])
@require_admin
def calculate_expense_allocations():
    """计算费用分摊 - 按订单金额比例分摊到指定年度的所有订单"""
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

        # 删除该年份的现有分摊记录
        expense_ids = db.session.query(Expense.id).filter(Expense.target_year == target_year).subquery()
        db.session.query(ExpenseAllocation).filter(ExpenseAllocation.expense_id.in_(expense_ids)).delete(synchronize_session=False)

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
        orders = Order.query.filter(
            db.extract('year', Order.create_time) == target_year
        ).all()

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

        # 对每个费用进行分摊计算
        for expense in expenses:
            expense_amount = float(expense.amount) if expense.amount else 0.0

            # 对每个订单进行分摊
            for order in orders:
                order_amount = float(order.contract_amount) if order.contract_amount else 0.0
                if order_amount > 0:
                    # 按订单金额比例分摊：(当前订单合同金额 / 摊分总额) * 摊分总额
                    # 实际上是：(当前订单合同金额 / 摊分总额) * expense_amount
                    allocated_amount = (order_amount / allocation_base) * expense_amount

                    # 创建费用分摊记录
                    allocation = ExpenseAllocation(
                        expense_id=expense.id,
                        order_id=order.id,
                        allocated_amount=allocated_amount
                    )
                    db.session.add(allocation)

        # 创建计算记录
        calc_record = ExpenseCalculationRecord(
            calculation_time=datetime.now(),
            target_year=target_year,
            status='completed',
            remark=f'成功为{len(expenses)}笔费用分摊到{len(orders)}个订单'
        )
        db.session.add(calc_record)
        
        # 更新每个订单的proportionate_cost字段
        for order in orders:
            order_amount = float(order.contract_amount) if order.contract_amount else 0.0
            if allocation_base > 0:
                # 计算该订单的摊分费用总和
                order_total_expense = sum(
                    (order_amount / allocation_base) * float(expense.amount) if expense.amount else 0.0
                    for expense in expenses
                )
                
                # 更新订单的摊分费用字段
                order.proportionate_cost = order_total_expense
            else:
                order.proportionate_cost = 0.0

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
            "msg": "费用分摊计算完成",
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
            remark=f'费用分摊计算失败: {str(e)}'
        )
        db.session.add(calc_record)
        db.session.commit()

        return jsonify({
            "code": 500,
            "msg": f"费用分摊计算失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/get-yearly-expense-summary/<int:year>', methods=['GET'])
@require_admin
def get_yearly_expense_summary(year):
    """获取指定年份的费用汇总信息"""
    try:
        # 获取该年份的总开支（正数）和总收入（负数的绝对值）
        total_expenses_query = db.session.query(
            db.func.sum(Expense.amount)
        ).filter(
            Expense.target_year == year,
            Expense.expense_type == '全面分摊'
        )

        total_expenses = total_expenses_query.scalar() or 0.0

        # 分别计算总开支和总收入
        total_expenses_raw = db.session.query(Expense.amount).filter(
            Expense.target_year == year,
            Expense.expense_type == '全面分摊'
        ).all()

        total_expenditure = sum(amount for amount, in total_expenses_raw if amount < 0)  # 总开支
        total_income = sum(amount for amount, in total_expenses_raw if amount > 0)  # 总收入

        # 获取该年份的订单数量
        total_orders = db.session.query(
            db.func.count(Order.id)
        ).filter(
            db.extract('year', Order.create_time) == year
        ).scalar() or 0

        # 获取该年份的订单总金额
        total_order_amount = db.session.query(
            db.func.sum(Order.contract_amount)
        ).filter(
            db.extract('year', Order.create_time) == year
        ).scalar() or 0.0

        # 获取最近一次计算记录
        latest_calc = ExpenseCalculationRecord.query.filter(
            ExpenseCalculationRecord.target_year == year
        ).order_by(ExpenseCalculationRecord.calculation_time.desc()).first()

        # 获取年度目标
        annual_target_record = AnnualTarget.query.filter_by(target_year=year).first()
        annual_target = float(annual_target_record.target_amount) if annual_target_record else 10000000.00

        summary_data = {
            "year": year,
            "total_expenses": float(total_expenses),
            "total_expenditure": float(total_expenditure),
            "total_income": float(total_income),
            "total_orders": total_orders,
            "total_order_amount": float(total_order_amount),
            "latest_calculation": serialize_calculation_record(latest_calc) if latest_calc else None,
            "annual_target": annual_target
        }

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": f"获取{year}年费用汇总成功",
            "data": summary_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取费用汇总失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/annual-targets', methods=['GET'])
@require_admin
def get_annual_targets():
    """获取年度目标列表"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 获取筛选参数
        target_year = request.args.get('target_year', type=int)

        # 构建查询
        query = AnnualTarget.query

        # 应用筛选条件
        if target_year:
            query = query.filter(AnnualTarget.target_year == target_year)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        annual_targets = query.order_by(AnnualTarget.target_year.desc()).offset((page - 1) * size).limit(size).all()

        # 序列化数据
        annual_targets_list = [serialize_annual_target(target) for target in annual_targets]

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取年度目标列表成功",
            "data": {
                "list": annual_targets_list,
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
            "msg": f"获取年度目标列表失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/annual-targets', methods=['POST'])
@require_admin
def create_annual_target():
    """创建年度目标"""
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

        # 检查是否已存在该年份的年度目标
        existing_target = AnnualTarget.query.filter_by(target_year=target_year).first()
        if existing_target:
            return jsonify({
                "code": 400,
                "msg": f"年份 {target_year} 的年度目标已存在",
                "data": None
            }), 400

        # 创建年度目标记录
        new_target = AnnualTarget(
            target_year=target_year,
            target_amount=data.get('target_amount', 10000000.00)
        )
        db.session.add(new_target)
        db.session.commit()

        # 序列化创建的年度目标记录
        target_data = serialize_annual_target(new_target)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "年度目标创建成功",
            "data": target_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建年度目标失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/annual-targets/<int:target_id>', methods=['PUT'])
@require_admin
def update_annual_target(target_id):
    """更新年度目标"""
    try:
        annual_target = AnnualTarget.query.get_or_404(target_id)
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 更新年度目标字段
        if 'target_year' in data: 
            annual_target.target_year = data['target_year']
        if 'target_amount' in data: 
            annual_target.target_amount = data['target_amount']

        db.session.commit()
        target_data = serialize_annual_target(annual_target)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "年度目标更新成功",
            "data": target_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新年度目标失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/annual-targets/<int:target_id>', methods=['GET'])
@require_admin
def get_annual_target(target_id):
    """获取单个年度目标详情"""
    try:
        annual_target = AnnualTarget.query.get_or_404(target_id)
        target_data = serialize_annual_target(annual_target)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取年度目标详情成功",
            "data": target_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取年度目标详情失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/annual-targets/year/<int:target_year>', methods=['GET'])
@require_admin
def get_annual_target_by_year(target_year):
    """根据年份获取年度目标"""
    try:
        annual_target = AnnualTarget.query.filter_by(target_year=target_year).first()
        if not annual_target:
            # 如果没有找到对应年份的年度目标，则使用默认值创建
            annual_target = AnnualTarget(
                target_year=target_year,
                target_amount=10000000.00
            )
            db.session.add(annual_target)
            db.session.commit()

        target_data = serialize_annual_target(annual_target)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": f"获取{target_year}年年度目标成功",
            "data": target_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取年度目标失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/annual-targets/year/<int:target_year>', methods=['PUT'])
@require_admin
def update_annual_target_by_year(target_year):
    """根据年份更新年度目标"""
    try:
        annual_target = AnnualTarget.query.filter_by(target_year=target_year).first()
        if not annual_target:
            # 如果没有找到对应年份的年度目标，则创建
            annual_target = AnnualTarget(
                target_year=target_year,
                target_amount=request.get_json().get('target_amount', 10000000.00)
            )
            db.session.add(annual_target)
        else:
            # 更新现有记录
            data = request.get_json()
            if data and 'target_amount' in data:
                annual_target.target_amount = data['target_amount']

        db.session.commit()
        target_data = serialize_annual_target(annual_target)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": f"{target_year}年年度目标更新成功",
            "data": target_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新年度目标失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/individual-expenses', methods=['GET'])
@require_admin
def get_individual_expenses():
    """获取个别费用列表"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 获取筛选参数
        order_id = request.args.get('order_id', type=int)
        name = request.args.get('name')

        # 构建查询
        query = IndividualExpense.query

        # 应用筛选条件
        if order_id:
            query = query.filter(IndividualExpense.order_id == order_id)
        if name:
            query = query.filter(IndividualExpense.name.contains(name))

        # 计算总数
        total = query.count()

        # 应用分页和排序
        individual_expenses = query.order_by(IndividualExpense.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 序列化数据
        expenses_list = [serialize_individual_expense(expense) for expense in individual_expenses]

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取个别费用列表成功",
            "data": {
                "list": expenses_list,
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
            "msg": f"获取个别费用列表失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/individual-expenses', methods=['POST'])
@require_admin
def create_individual_expense():
    """创建个别费用"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        order_id = data.get('order_id')
        if not order_id:
            return jsonify({
                "code": 400,
                "msg": "必须指定订单ID",
                "data": None
            }), 400

        # 检查订单是否存在
        from app.models.order import Order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                "code": 400,
                "msg": f"订单ID {order_id} 不存在",
                "data": None
            }), 400

        # 创建个别费用记录
        new_expense = IndividualExpense(
            order_id=order_id,
            name=data.get('name'),
            amount=data.get('amount'),
            remark=data.get('remark')
        )
        db.session.add(new_expense)
        db.session.commit()

        # 序列化创建的个别费用记录
        expense_data = serialize_individual_expense(new_expense)

        # 更新订单的individual_cost字段
        update_order_individual_cost(order_id)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "个别费用创建成功",
            "data": expense_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建个别费用失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/individual-expenses/<int:expense_id>', methods=['PUT'])
@require_admin
def update_individual_expense(expense_id):
    """更新个别费用"""
    try:
        individual_expense = IndividualExpense.query.get_or_404(expense_id)
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 更新个别费用字段
        if 'name' in data: 
            individual_expense.name = data['name']
        if 'amount' in data: 
            individual_expense.amount = data['amount']
        if 'remark' in data: 
            individual_expense.remark = data['remark']

        db.session.commit()
        expense_data = serialize_individual_expense(individual_expense)

        # 更新订单的individual_cost字段
        update_order_individual_cost(individual_expense.order_id)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "个别费用更新成功",
            "data": expense_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新个别费用失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/individual-expenses/<int:expense_id>', methods=['GET'])
@require_admin
def get_individual_expense(expense_id):
    """获取单个别费用详情"""
    try:
        individual_expense = IndividualExpense.query.get_or_404(expense_id)
        expense_data = serialize_individual_expense(individual_expense)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取个别费用详情成功",
            "data": expense_data
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取个别费用详情失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/individual-expenses/<int:expense_id>', methods=['DELETE'])
@require_admin
def delete_individual_expense(expense_id):
    """删除个别费用"""
    try:
        individual_expense = IndividualExpense.query.get_or_404(expense_id)
        order_id = individual_expense.order_id
        
        db.session.delete(individual_expense)
        db.session.commit()

        # 更新订单的individual_cost字段
        update_order_individual_cost(order_id)

        return jsonify({
            "code": 200,
            "msg": "个别费用删除成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除个别费用失败: {str(e)}",
            "data": None
        }), 500


@expense_bp.route('/orders/<int:order_id>/individual-expenses', methods=['GET'])
@require_admin
def get_individual_expenses_by_order(order_id):
    """获取指定订单的个别费用列表"""
    try:
        # 检查订单是否存在
        from app.models.order import Order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                "code": 400,
                "msg": f"订单ID {order_id} 不存在",
                "data": None
            }), 400

        # 获取该订单的所有个别费用
        individual_expenses = IndividualExpense.query.filter_by(order_id=order_id).order_by(IndividualExpense.create_time.desc()).all()

        # 序列化数据
        expenses_list = [serialize_individual_expense(expense) for expense in individual_expenses]

        # 计算个别费用总和
        total_individual_cost = sum(float(expense.amount) if expense.amount else 0.0 for expense in individual_expenses)

        import json
        from flask import Response
        response_data = {
            "code": 200,
            "msg": f"获取订单 {order_id} 的个别费用列表成功",
            "data": {
                "list": expenses_list,
                "total_individual_cost": total_individual_cost,
                "order_id": order_id
            }
        }
        # 使用自定义编码器处理Decimal类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取个别费用列表失败: {str(e)}",
            "data": None
        }), 500


def update_order_individual_cost(order_id):
    """更新订单的individual_cost字段"""
    try:
        # 计算该订单的个别费用总和
        total_individual_cost = db.session.query(
            db.func.sum(IndividualExpense.amount)
        ).filter(IndividualExpense.order_id == order_id).scalar() or 0.0

        # 更新订单的individual_cost字段
        from app.models.order import Order
        order = Order.query.get(order_id)
        if order:
            order.individual_cost = total_individual_cost
            db.session.commit()
    except Exception as e:
        print(f"更新订单 {order_id} 的个别费用总和失败: {str(e)}")
        db.session.rollback()