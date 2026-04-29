"""
订单记录管理相关路由
用于管理订单记录及其收支明细（收支合并版）
"""

from flask import Blueprint, request, jsonify, Response
from extensions import db
from app.models.order_record import OrderRecord, OrderRecordItem
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_ORDER_RECORD_MANAGE
from app.utils.auth_utils import get_user_id_from_token
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import json
from decimal import Decimal

order_record_bp = Blueprint('order_record', __name__)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def get_current_user():
    """获取当前用户"""
    emp_id = get_user_id_from_token()
    return emp_id


# ========== 订单记录API ==========

@order_record_bp.route('/order-records', methods=['GET'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def get_order_records():
    """获取订单记录列表"""
    try:
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        query = OrderRecord.query.order_by(OrderRecord.create_time.desc())

        total = query.count()
        records = query.offset((page - 1) * size).limit(size).all()

        records_list = [r.to_dict() for r in records]

        response_data = {
            "code": 200,
            "msg": "获取订单记录列表成功",
            "data": {
                "list": records_list,
                "total": total,
                "page": page,
                "size": size
            }
        }
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取订单记录列表失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records', methods=['POST'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def create_order_record():
    """创建订单记录"""
    try:
        data = request.get_json()
        creator_id = get_current_user()

        new_record = OrderRecord(
            order_no=data.get('order_no'),
            order_remark_name=data.get('order_remark_name'),
            order_amount=data.get('order_amount', 0),
            currency=data.get('currency', 'CNY'),
            exchange_rate=data.get('exchange_rate', 1.0),
            order_date=datetime.strptime(data['order_date'], '%Y-%m-%d').date() if data.get('order_date') else None,
            is_completed=data.get('is_completed', False),
            creator_id=creator_id
        )
        db.session.add(new_record)
        db.session.commit()

        response_data = {"code": 200, "msg": "订单记录创建成功", "data": new_record.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"创建订单记录失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/<int:record_id>', methods=['GET'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def get_order_record(record_id):
    """获取订单记录详情（含收支明细）"""
    try:
        record = OrderRecord.query.get_or_404(record_id)
        record_data = record.to_dict(include_relations=True)

        response_data = {"code": 200, "msg": "获取订单记录详情成功", "data": record_data}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取订单记录详情失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/<int:record_id>', methods=['PUT'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def update_order_record(record_id):
    """更新订单记录"""
    try:
        record = OrderRecord.query.get_or_404(record_id)
        data = request.get_json()
        current_user = get_current_user()

        if 'order_no' in data:
            record.order_no = data['order_no']
        if 'order_remark_name' in data:
            record.order_remark_name = data['order_remark_name']
        if 'order_amount' in data:
            record.order_amount = data['order_amount']
        if 'currency' in data:
            record.currency = data['currency']
        if 'exchange_rate' in data:
            record.exchange_rate = data['exchange_rate']
        if 'order_date' in data and data['order_date']:
            record.order_date = datetime.strptime(data['order_date'], '%Y-%m-%d').date()
        if 'is_completed' in data:
            record.is_completed = data['is_completed']

        record.update_time = datetime.now()
        db.session.commit()

        response_data = {"code": 200, "msg": "订单记录更新成功", "data": record.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新订单记录失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/<int:record_id>', methods=['DELETE'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def delete_order_record(record_id):
    """删除订单记录"""
    try:
        record = OrderRecord.query.get_or_404(record_id)
        record.customer_id = None
        db.session.delete(record)
        db.session.commit()
        return jsonify({"code": 200, "msg": "订单记录删除成功", "data": None})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除订单记录失败: {str(e)}", "data": None}), 500


# ========== 收支记录API（合并后统一）==========

@order_record_bp.route('/order-records/<int:record_id>/items', methods=['GET'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def get_items(record_id):
    """获取订单记录的收支列表（可按type过滤）"""
    try:
        item_type = request.args.get('type', None)  # income 或 expense
        query = OrderRecordItem.query.filter_by(order_record_id=record_id)
        if item_type:
            query = query.filter_by(type=item_type)
        items = query.order_by(OrderRecordItem.create_time.desc()).all()
        response_data = {
            "code": 200,
            "msg": "获取收支列表成功",
            "data": [item.to_dict() for item in items]
        }
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取收支列表失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/<int:record_id>/items', methods=['POST'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def create_item(record_id):
    """添加收支记录"""
    try:
        data = request.get_json()
        current_user = get_current_user()

        # screenshots 已经是 JSON 数组，直接存储
        screenshots = data.get('screenshots', [])

        item = OrderRecordItem(
            order_record_id=record_id,
            type=data.get('type', 'income'),  # income 或 expense
            remark=data.get('remark'),
            amount=data.get('amount', 0),
            currency=data.get('currency', 'CNY'),
            exchange_rate=data.get('exchange_rate', 1.0),
            screenshots=json.dumps(screenshots) if screenshots else None,
            record_date=datetime.strptime(data['record_date'], '%Y-%m-%d').date() if data.get('record_date') else None,
            creator_id=current_user
        )
        db.session.add(item)
        db.session.commit()

        response_data = {"code": 200, "msg": "收支记录添加成功", "data": item.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"添加收支记录失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/items/<int:item_id>', methods=['PUT'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def update_item(item_id):
    """更新收支记录"""
    try:
        item = OrderRecordItem.query.get_or_404(item_id)
        data = request.get_json()
        current_user = get_current_user()

        if 'remark' in data:
            item.remark = data['remark']
        if 'amount' in data:
            item.amount = data['amount']
        if 'currency' in data:
            item.currency = data['currency']
        if 'exchange_rate' in data:
            item.exchange_rate = data['exchange_rate']
        if 'record_date' in data:
            item.record_date = datetime.strptime(data['record_date'], '%Y-%m-%d').date() if data['record_date'] else None

        # screenshots 更新：合并策略（新截图追加到现有数组）
        if 'screenshots' in data:
            new_screenshots = data['screenshots']
            if isinstance(new_screenshots, list):
                # 替换模式（编辑时全量提交）
                item.screenshots = json.dumps(new_screenshots) if new_screenshots else None

        item.updater_id = current_user
        item.update_time = datetime.now()
        db.session.commit()

        response_data = {"code": 200, "msg": "收支记录更新成功", "data": item.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新收支记录失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/items/<int:item_id>', methods=['DELETE'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def delete_item(item_id):
    """删除收支记录"""
    try:
        item = OrderRecordItem.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "收支记录删除成功", "data": None})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除收支记录失败: {str(e)}", "data": None}), 500


# ========== 文件上传API ==========

@order_record_bp.route('/order-records/upload-screenshot', methods=['POST'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def upload_screenshot():
    """上传佐证截图（支持多文件）"""
    from app.utils.upload_utils import sanitize_filename
    from datetime import datetime as dt
    import re

    try:
        files_list = []
        if 'files' in request.files:
            files_list = request.files.getlist('files')
        elif 'file' in request.files:
            files_list = [request.files['file']]

        if not files_list or all(f.filename == '' for f in files_list):
            return jsonify({"code": 400, "msg": "未上传文件", "data": None}), 400

        order_id = request.form.get('order_id')
        record_type = request.form.get('record_type', 'unknown')
        remark = request.form.get('remark', '')

        # 确定文件夹名
        if order_id:
            try:
                order = OrderRecord.query.get(int(order_id))
                if order and order.order_no:
                    order_no_clean = re.sub(r'[^\w\-_]', '_', order.order_no)
                    order_timestamp = order.create_time.strftime('%Y%m%d%H%M%S') if order.create_time else dt.now().strftime('%Y%m%d%H%M%S')
                    folder_name = f"{order_no_clean}_{order_timestamp}"
                else:
                    folder_name = f"unknown_{dt.now().strftime('%Y%m%d%H%M%S')}"
            except Exception:
                folder_name = f"unknown_{dt.now().strftime('%Y%m%d%H%M%S')}"
        else:
            folder_name = f"unknown_{dt.now().strftime('%Y%m%d%H%M%S')}"

        safe_remark = re.sub(r'[^\w\-_]', '_', remark)[:50]
        base_save_dir = 'assets/OrderRecords'
        save_dir = os.path.join(base_save_dir, folder_name)
        os.makedirs(save_dir, exist_ok=True)

        uploaded_files = []
        for idx, file in enumerate(files_list):
            if not file or file.filename == '':
                continue

            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            if not ext:
                ext = '.jpg'

            file_timestamp = dt.now().strftime('%Y%m%d%H%M%S%f')
            new_filename = f"{record_type}_{safe_remark}_{file_timestamp}_{idx}{ext}"

            save_path = os.path.join(save_dir, new_filename)
            file.save(save_path)

            relative_path = os.path.relpath(save_path, base_save_dir).replace('\\', '/')
            uploaded_files.append({"path": relative_path, "filename": new_filename, "folder": folder_name})

        if len(uploaded_files) == 1:
            # 单文件返回兼容格式
            return jsonify({
                "code": 200,
                "msg": "文件上传成功",
                "data": uploaded_files[0],
                "path": uploaded_files[0]["path"]
            })
        else:
            # 多文件返回数组
            return jsonify({
                "code": 200,
                "msg": f"{len(uploaded_files)}个文件上传成功",
                "data": uploaded_files
            })
    except Exception as e:
        return jsonify({"code": 500, "msg": f"文件上传失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/delete-screenshot', methods=['POST'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def delete_screenshot():
    """删除佐证截图文件"""
    try:
        data = request.get_json()
        screenshot_path = data.get('path')

        if not screenshot_path:
            return jsonify({"code": 400, "msg": "截图路径不能为空", "data": None}), 400

        full_path = os.path.join('assets/OrderRecords', screenshot_path)
        full_path = os.path.abspath(full_path)

        if not full_path.startswith(os.path.abspath('assets/OrderRecords')):
            return jsonify({"code": 400, "msg": "非法文件路径", "data": None}), 400

        if os.path.exists(full_path):
            os.remove(full_path)
            return jsonify({"code": 200, "msg": "截图删除成功", "data": None})
        else:
            return jsonify({"code": 404, "msg": "文件不存在", "data": None}), 404
    except Exception as e:
        return jsonify({"code": 500, "msg": f"删除截图失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/delete-order-folder', methods=['POST'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def delete_order_folder():
    """删除整个订单文件夹"""
    try:
        import shutil

        data = request.get_json()
        order_id = data.get('order_id')

        if not order_id:
            return jsonify({"code": 400, "msg": "订单ID不能为空", "data": None}), 400

        order = OrderRecord.query.get(int(order_id))
        if not order:
            return jsonify({"code": 404, "msg": "订单不存在", "data": None}), 404

        order_timestamp = order.create_time.strftime('%Y%m%d%H%M%S') if order.create_time else ''
        folder_name = f"{order.order_no}_{order_timestamp}"
        full_folder_path = os.path.join('assets/OrderRecords', folder_name)
        full_folder_path = os.path.abspath(full_folder_path)

        if not full_folder_path.startswith(os.path.abspath('assets/OrderRecords')):
            return jsonify({"code": 400, "msg": "非法文件夹路径", "data": None}), 400

        if os.path.exists(full_folder_path):
            shutil.rmtree(full_folder_path)
            return jsonify({"code": 200, "msg": "订单文件夹删除成功", "data": None})
        else:
            return jsonify({"code": 200, "msg": "文件夹不存在，无需删除", "data": None})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"删除订单文件夹失败: {str(e)}", "data": None}), 500


# ========== 旧API兼容路由（可移除，迁移后不再需要）==========

# 保留旧路由以兼容迁移期间的前端请求，迁移完成后删除
@order_record_bp.route('/order-records/<int:record_id>/incomes', methods=['GET'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def get_incomes_compat(record_id):
    """获取订单记录的收入列表（兼容旧API）"""
    return get_items(record_id)


@order_record_bp.route('/order-records/<int:record_id>/incomes', methods=['POST'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def create_income_compat(record_id):
    """添加收入记录（兼容旧API）"""
    try:
        data = request.get_json()
        current_user = get_current_user()

        # 转换旧格式 screenshot -> screenshots
        screenshots = data.get('screenshots', [])
        if not screenshots and data.get('screenshot'):
            screenshots = [data.get('screenshot')]

        item = OrderRecordItem(
            order_record_id=record_id,
            type='income',
            remark=data.get('remark'),
            amount=data.get('amount', 0),
            currency=data.get('currency', 'CNY'),
            exchange_rate=data.get('exchange_rate', 1.0),
            screenshots=json.dumps(screenshots) if screenshots else None,
            record_date=datetime.strptime(data['record_date'], '%Y-%m-%d').date() if data.get('record_date') else None,
            creator_id=current_user
        )
        db.session.add(item)
        db.session.commit()

        response_data = {"code": 200, "msg": "收入记录添加成功", "data": item.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"添加收入记录失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/incomes/<int:income_id>', methods=['PUT'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def update_income_compat(income_id):
    """更新收入记录（兼容旧API）"""
    try:
        item = OrderRecordItem.query.get_or_404(income_id)
        if item.type != 'income':
            return jsonify({"code": 400, "msg": "该记录不是收入记录", "data": None}), 400
        data = request.get_json()
        current_user = get_current_user()

        if 'remark' in data:
            item.remark = data['remark']
        if 'amount' in data:
            item.amount = data['amount']
        if 'currency' in data:
            item.currency = data['currency']
        if 'exchange_rate' in data:
            item.exchange_rate = data['exchange_rate']
        if 'record_date' in data:
            item.record_date = datetime.strptime(data['record_date'], '%Y-%m-%d').date() if data['record_date'] else None

        # 兼容旧截图字段
        if 'screenshots' in data:
            item.screenshots = json.dumps(data['screenshots']) if data['screenshots'] else None
        elif 'screenshot' in data:
            old = json.loads(item.screenshots) if item.screenshots else []
            if data['screenshot'] and data['screenshot'] not in old:
                old.append(data['screenshot'])
            item.screenshots = json.dumps(old) if old else None

        item.updater_id = current_user
        item.update_time = datetime.now()
        db.session.commit()

        response_data = {"code": 200, "msg": "收入记录更新成功", "data": item.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新收入记录失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/incomes/<int:income_id>', methods=['DELETE'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def delete_income_compat(income_id):
    """删除收入记录（兼容旧API）"""
    try:
        item = OrderRecordItem.query.get_or_404(income_id)
        if item.type != 'income':
            return jsonify({"code": 400, "msg": "该记录不是收入记录", "data": None}), 400
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "收入记录删除成功", "data": None})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除收入记录失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/<int:record_id>/expenses', methods=['GET'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def get_expenses_compat(record_id):
    """获取订单记录的支出列表（兼容旧API）"""
    try:
        expenses = OrderRecordItem.query.filter_by(order_record_id=record_id, type='expense').all()
        response_data = {
            "code": 200,
            "msg": "获取支出列表成功",
            "data": [exp.to_dict() for exp in expenses]
        }
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取支出列表失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/<int:record_id>/expenses', methods=['POST'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def create_expense_compat(record_id):
    """添加支出记录（兼容旧API）"""
    try:
        data = request.get_json()
        current_user = get_current_user()

        screenshots = data.get('screenshots', [])
        if not screenshots and data.get('screenshot'):
            screenshots = [data.get('screenshot')]

        item = OrderRecordItem(
            order_record_id=record_id,
            type='expense',
            remark=data.get('remark'),
            amount=data.get('amount', 0),
            currency=data.get('currency', 'CNY'),
            exchange_rate=data.get('exchange_rate', 1.0),
            screenshots=json.dumps(screenshots) if screenshots else None,
            record_date=datetime.strptime(data['record_date'], '%Y-%m-%d').date() if data.get('record_date') else None,
            creator_id=current_user
        )
        db.session.add(item)
        db.session.commit()

        response_data = {"code": 200, "msg": "支出记录添加成功", "data": item.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"添加支出记录失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/expenses/<int:expense_id>', methods=['PUT'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def update_expense_compat(expense_id):
    """更新支出记录（兼容旧API）"""
    try:
        item = OrderRecordItem.query.get_or_404(expense_id)
        if item.type != 'expense':
            return jsonify({"code": 400, "msg": "该记录不是支出记录", "data": None}), 400
        data = request.get_json()
        current_user = get_current_user()

        if 'remark' in data:
            item.remark = data['remark']
        if 'amount' in data:
            item.amount = data['amount']
        if 'currency' in data:
            item.currency = data['currency']
        if 'exchange_rate' in data:
            item.exchange_rate = data['exchange_rate']
        if 'record_date' in data:
            item.record_date = datetime.strptime(data['record_date'], '%Y-%m-%d').date() if data['record_date'] else None

        if 'screenshots' in data:
            item.screenshots = json.dumps(data['screenshots']) if data['screenshots'] else None
        elif 'screenshot' in data:
            old = json.loads(item.screenshots) if item.screenshots else []
            if data['screenshot'] and data['screenshot'] not in old:
                old.append(data['screenshot'])
            item.screenshots = json.dumps(old) if old else None

        item.updater_id = current_user
        item.update_time = datetime.now()
        db.session.commit()

        response_data = {"code": 200, "msg": "支出记录更新成功", "data": item.to_dict()}
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新支出记录失败: {str(e)}", "data": None}), 500


@order_record_bp.route('/order-records/expenses/<int:expense_id>', methods=['DELETE'])
@route_permission(ROUTE_ORDER_RECORD_MANAGE)
def delete_expense_compat(expense_id):
    """删除支出记录（兼容旧API）"""
    try:
        item = OrderRecordItem.query.get_or_404(expense_id)
        if item.type != 'expense':
            return jsonify({"code": 400, "msg": "该记录不是支出记录", "data": None}), 400
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "支出记录删除成功", "data": None})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除支出记录失败: {str(e)}", "data": None}), 500
