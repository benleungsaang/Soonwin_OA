from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
import os
import json
from .. import db
from ..models.machine_new import MachineNew
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_QUOTATION_MANAGE
from app.models.simple_permission import get_user_role_from_token

quotation_bp = Blueprint('quotation_bp', __name__, url_prefix='/api')

@quotation_bp.route('/quotation-machines', methods=['GET'])
@route_permission(ROUTE_QUOTATION_MANAGE)
def get_quotation_machines():
    """
    获取用于报价的机器列表，支持排序
    默认按使用次数(added_count)降序排列
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)  # 搜索关键词
        sort_by = request.args.get('sort_by', 'added_count', type=str)  # 排序字段
        order = request.args.get('order', 'desc', type=str)  # 排序方向: asc/desc

        # 使用通用函数检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        # 构建查询
        query = MachineNew.query.filter_by(is_deleted=0)

        # 如果提供搜索关键词，则在search_key中搜索
        if search:
            query = query.filter(MachineNew.search_key.like(f'%{search}%'))

        # 处理排序
        valid_sort_fields = {
            'id': MachineNew.id,
            'model': MachineNew.model,
            'brand': MachineNew.brand,
            'show_price': MachineNew.show_price,
            'added_count': MachineNew.added_count,
            'created_time': MachineNew.id  # 用ID代表创建时间
        }

        # 默认按ID降序排列
        if sort_by in valid_sort_fields:
            sort_column = valid_sort_fields[sort_by]
            if order.lower() == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # 默认按ID降序排列
            query = query.order_by(MachineNew.id.desc())

        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        machines = pagination.items

        # 根据用户权限处理数据
        machine_data = []
        for machine in machines:
            # 根据用户权限决定是否包含价格字段
            include_price = is_admin
            machine_dict = machine.to_dict(include_price=include_price)
            machine_data.append(machine_dict)

        return jsonify({
            'success': True,
            'data': {
                'machines': machine_data,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        })
    except Exception as e:
        current_app.logger.error(f"获取报价机器列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500