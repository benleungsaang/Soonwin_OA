from flask import Blueprint, request, jsonify
from extensions import db
from app.models.expense import Expense, ExpenseAllocation, ExpenseCalculationRecord
from app.models.order_list import OrderList
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

        # 删除该年份的现有分摊记录
        # 修复：使用session.query().filter()而不是query.join().filter()
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
        orders = OrderList.query.filter(
            db.extract('year', OrderList.create_time) == target_year
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
        
        if total_order_amount <= 0:
            # 创建计算记录
            calc_record = ExpenseCalculationRecord(
                calculation_time=datetime.now(),
                target_year=target_year,
                status='completed',
                remark=f'该年份({target_year})订单总金额为0，无法按比例分摊'
            )
            db.session.add(calc_record)
            db.session.commit()
            
            return jsonify({
                "code": 200,
                "msg": f"该年份({target_year})订单总金额为0，无法按比例分摊",
                "data": {
                    "target_year": target_year,
                    "total_expenses": len(expenses),
                    "total_orders": len(orders),
                    "total_order_amount": total_order_amount,
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
                    # 按订单金额比例分摊
                    allocated_amount = (order_amount / total_order_amount) * expense_amount
                    
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
        db.session.commit()

        # 计算订单的总成本
        total_direct_cost = sum(
            float(order.direct_cost) if order.direct_cost else 0.0
            for order in orders
        )
        
        # 计算总净利 (订单金额 - 成本)
        total_net_profit = total_order_amount - total_direct_cost
        
        # 计算总费用
        total_expense_amount = sum(
            float(expense.amount) if expense.amount else 0.0
            for expense in expenses
        )
        
        # 计算总毛利 (净利 - 总费用) 
        total_gross_profit = total_net_profit - total_expense_amount

        return jsonify({
            "code": 200,
            "msg": "费用分摊计算完成",
            "data": {
                "target_year": target_year,
                "total_expenses": len(expenses),
                "total_orders": len(orders),
                "total_order_amount": total_order_amount,
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
        
        total_expenditure = sum(amount for amount, in total_expenses_raw if amount > 0)  # 总开支
        total_income = sum(abs(amount) for amount, in total_expenses_raw if amount < 0)  # 总收入（取绝对值）

        # 获取该年份的订单数量
        total_orders = db.session.query(
            db.func.count(OrderList.id)
        ).filter(
            db.extract('year', OrderList.create_time) == year
        ).scalar() or 0

        # 获取该年份的订单总金额
        total_order_amount = db.session.query(
            db.func.sum(OrderList.contract_amount)
        ).filter(
            db.extract('year', OrderList.create_time) == year
        ).scalar() or 0.0

        # 获取最近一次计算记录
        latest_calc = ExpenseCalculationRecord.query.filter(
            ExpenseCalculationRecord.target_year == year
        ).order_by(ExpenseCalculationRecord.calculation_time.desc()).first()

        summary_data = {
            "year": year,
            "total_expenses": float(total_expenses),
            "total_expenditure": float(total_expenditure),
            "total_income": float(total_income),
            "total_orders": total_orders,
            "total_order_amount": float(total_order_amount),
            "latest_calculation": serialize_calculation_record(latest_calc) if latest_calc else None
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