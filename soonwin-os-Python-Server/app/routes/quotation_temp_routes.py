from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
import json
from decimal import Decimal
from .. import db
from ..models.quotation_temp import QuotationTemp
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_QUOTATION_MANAGE
from app.models.simple_permission import get_user_role_from_token
from app.utils.auth_utils import get_user_id_from_token
from app.models.employee import Employee

quotation_temp_bp = Blueprint('quotation_temp', __name__, url_prefix='/api')

def get_current_user():
    """获取当前用户信息的辅助函数"""
    emp_id = get_user_id_from_token()
    user_role = get_user_role_from_token()

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

@quotation_temp_bp.route('/quotation-temp', methods=['GET'])
@route_permission(ROUTE_QUOTATION_MANAGE)
def get_quotation_temps():
    """
    获取临时报价列表，支持分页和筛选
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)  # 搜索关键词

        # 获取当前用户信息
        current_user = get_current_user()
        is_admin = current_user.user_role == 'admin'

        # 构建查询
        query = QuotationTemp.query

        # 管理员可以获取全部报价单，普通用户只能获取自己创建的和公开的报价单
        if not is_admin:
            query = query.filter(
                (QuotationTemp.creator_id == current_user.emp_id) |
                (QuotationTemp.is_public == 1)
            )

        # 如果有搜索参数，则在order_mark中进行模糊搜索
        if search:
            query = query.filter(QuotationTemp.order_mark.like(f'%{search}%'))

        # 应用分页和排序
        pagination = query.order_by(QuotationTemp.create_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        temps = pagination.items

        # 序列化数据
        temp_data = [temp.to_dict() for temp in temps]

        return jsonify({
            'success': True,
            'data': {
                'quotation_temps': temp_data,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        })
    except Exception as e:
        current_app.logger.error(f"获取临时报价列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@quotation_temp_bp.route('/quotation-temp-list', methods=['GET'])
@route_permission(ROUTE_QUOTATION_MANAGE)
def get_quotation_temp_list():
    """
    获取临时报价列表（只返回关键字段），支持分页和筛选
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)  # 搜索关键词

        # 获取当前用户信息
        current_user = get_current_user()
        is_admin = current_user.user_role == 'admin'

        # 构建查询
        query = QuotationTemp.query

        # 管理员可以获取全部报价单，普通用户只能获取自己创建的和公开的报价单
        if not is_admin:
            query = query.filter(
                (QuotationTemp.creator_id == current_user.emp_id) |
                (QuotationTemp.is_public == 1)
            )

        # 如果有搜索参数，则在order_mark中进行模糊搜索
        if search:
            query = query.filter(QuotationTemp.order_mark.like(f'%{search}%'))

        # 应用分页和排序（按更新时间降序，最新的在前）
        pagination = query.order_by(QuotationTemp.update_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        temps = pagination.items

        # 序列化数据（只包含必要的字段）
        temp_data = []
        for temp in temps:
            item = {
                'order_id': temp.id,
                'order_mark': temp.order_mark,
                'total_amount': float(temp.total_amount) if temp.total_amount else 0.0,
                'update_time': temp.update_time.strftime('%Y-%m-%d %H:%M:%S') if temp.update_time else None,
                'currency_info': temp.currency_info,
                'is_public': temp.is_public,
                'creator_id': temp.creator_id
            }
            # 只有管理员才能看到creator_id
            # if is_admin:
            #     item['creator_id'] = temp.creator_id
            temp_data.append(item)

        return jsonify({
            'success': True,
            'data': {
                'quotation_temps': temp_data,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        })
    except Exception as e:
        current_app.logger.error(f"获取临时报价列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@quotation_temp_bp.route('/quotation-temp', methods=['POST'])
@route_permission(ROUTE_QUOTATION_MANAGE)
def create_quotation_temp():
    """
    创建临时报价，直接创建新报价单
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400

        # 获取当前用户
        current_user = get_current_user()

        # 直接创建新订单（允许同名）
        new_temp = QuotationTemp(
            order_mark=data.get('order_mark'),
            machine_list=json.dumps(data.get('machine_list', [])),
            temp_params=json.dumps(data.get('temp_params', [])),
            total_amount=data.get('total_amount', 0),
            creator_id=current_user.emp_id,
            remark=data.get('remark', ''),
            is_public=data.get('is_public', 0),
            currency_info=json.dumps(data.get('currency_info')) if data.get('currency_info') else None
        )

        db.session.add(new_temp)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '临时报价创建成功',
            'data': new_temp.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建临时报价失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@quotation_temp_bp.route('/quotation-temp/<id>', methods=['GET'])
@route_permission(ROUTE_QUOTATION_MANAGE)
def get_quotation_temp(id):
    """
    获取单个临时报价详情
    """
    try:
        # 尝试将ID解析为整数（数据库ID）
        try:
            int_id = int(id)
            temp = QuotationTemp.query.filter_by(id=int_id).first()
        except ValueError:
            # 如果不是数字，则作为order_mark处理（兼容临时ID）
            temp = QuotationTemp.query.filter_by(order_mark=id).first()

        if not temp:
            return jsonify({'success': False, 'message': '临时报价不存在'}), 404

        # 获取当前用户
        current_user = get_current_user()
        is_admin = current_user.user_role == 'admin'

        # 检查权限：管理员可以查看所有，普通用户只能查看自己创建的或公开的
        if not is_admin and temp.creator_id != current_user.emp_id and temp.is_public != 1:
            return jsonify({'success': False, 'message': '无权限访问该临时报价'}), 403

        return jsonify({
            'success': True,
            'data': temp.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"获取临时报价详情失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@quotation_temp_bp.route('/quotation-temp/<id>', methods=['PUT'])
@route_permission(ROUTE_QUOTATION_MANAGE)
def update_quotation_temp(id):
    """
    更新临时报价信息，如果找不到订单则创建新订单
    """
    try:
        # 尝试将ID解析为整数（数据库ID）
        try:
            int_id = int(id)
            temp = QuotationTemp.query.filter_by(id=int_id).first()
        except ValueError:
            # 如果不是数字，则作为order_mark处理（兼容临时ID）
            temp = QuotationTemp.query.filter_by(order_mark=id).first()

        if not temp:
            # 如果找不到订单，调用创建新订单的逻辑
            return create_quotation_temp()

        # 获取当前用户
        current_user = get_current_user()

        # 检查权限：管理员可以修改所有，普通用户只能修改自己创建的
        if current_user.user_role != 'admin' and temp.creator_id != current_user.emp_id:
            return jsonify({'success': False, 'message': '无权限修改该临时报价'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400

        # 更新临时报价字段
        if 'machine_list' in data:
            temp.machine_list = json.dumps(data['machine_list'])
        if 'order_mark' in data:
            temp.order_mark = data['order_mark']
        if 'remark' in data:
            temp.remark = data['remark']
        if 'temp_params' in data:
            temp.temp_params = json.dumps(data['temp_params'])
        if 'total_amount' in data:
            temp.total_amount = data['total_amount']
        if 'currency_info' in data:
            temp.currency_info = json.dumps(data['currency_info'])
        if 'is_public' in data:
            temp.is_public = data['is_public']

        temp.update_time = datetime.now()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '临时报价更新成功',
            'data': temp.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新临时报价失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@quotation_temp_bp.route('/quotation-temp/<id>', methods=['DELETE'])
@route_permission(ROUTE_QUOTATION_MANAGE)
def delete_quotation_temp(id):
    """
    删除临时报价
    """
    try:
        temp = QuotationTemp.query.filter_by(id=id).first()
        if not temp:
            return jsonify({'success': False, 'message': '临时报价不存在'}), 404

        # 获取当前用户
        current_user = get_current_user()

        # 检查权限：管理员可以删除所有，普通用户只能删除自己创建的
        if current_user.user_role != 'admin' and temp.creator_id != current_user.emp_id:
            return jsonify({'success': False, 'message': '无权限删除该临时报价'}), 403

        # 删除临时报价
        db.session.delete(temp)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '临时报价删除成功'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除临时报价失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500