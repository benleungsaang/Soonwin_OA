"""货柜排布方案路由

提供货柜装货 3D 方案的列表 / 详情 / 创建 / 更新 / 删除接口。
所有人可读，仅作者或管理员可写（修改/删除），创建任意登录用户皆可。
"""
from datetime import datetime
from flask import Blueprint, request, jsonify

from extensions import db
from app.models.container_layout import ContainerLayout
from app.models.employee import Employee
from app.utils.simple_auth_utils import route_permission
from app.utils.auth_utils import get_user_id_from_token, get_user_role_from_token
from app.constants.simple_permission_constants import ROUTE_CONTAINER_LAYOUT_MANAGE

import json

container_layout_bp = Blueprint('container_layout', __name__)


def _current_user_name():
    """从 token 解析当前登录用户名（解析失败时退回 emp_id）"""
    uid = get_user_id_from_token()
    if not uid:
        return '匿名'
    try:
        emp = Employee.query.filter_by(emp_id=uid).first()
        return emp.name if emp else uid
    except Exception:
        return uid


# ============================================================
# 列表 / 搜索
# ============================================================

@container_layout_bp.route('/container-layouts', methods=['GET'])
@route_permission(ROUTE_CONTAINER_LAYOUT_MANAGE)
def list_layouts():
    """获取货柜排布方案列表（分页 + 关键字搜索 + 我的/全部筛选）

    Query:
        page: 页码（默认 1）
        per_page: 每页条数（默认 20）
        search: 关键字，模糊匹配 name 或 author_name
        scope: 'all'（默认）或 'mine'（只看自己）
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = (request.args.get('search', '') or '').strip()
        scope = request.args.get('scope', 'all')

        uid = get_user_id_from_token()
        q = ContainerLayout.query.filter_by(is_deleted=0)

        if scope == 'mine':
            q = q.filter_by(author_id=uid)

        if search:
            like = f'%{search}%'
            q = q.filter(
                db.or_(
                    ContainerLayout.name.like(like),
                    ContainerLayout.author_name.like(like),
                )
            )

        q = q.order_by(ContainerLayout.updated_at.desc())
        pagination = q.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': {
                'items': [r.to_dict(include_data=True, current_user_id=uid)
                          for r in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages,
            }
        })
    except Exception as e:
        print(f'[container_layout] 列表查询失败: {e}')
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'}), 500


# ============================================================
# 创建（仅元数据，无货物也可）
# ============================================================

@container_layout_bp.route('/container-layouts', methods=['POST'])
@route_permission(ROUTE_CONTAINER_LAYOUT_MANAGE)
def create_layout():
    """创建货柜排布方案

    Body:
        name: 方案名（必填，同一作者下唯一）
        data: 完整布局数据（可选；不传则创建空方案，后续在编辑页填充）

    响应 409：当前作者下已有同名方案
    """
    try:
        body = request.get_json(silent=True) or {}
        name = (body.get('name') or '').strip()
        if not name:
            return jsonify({'success': False, 'message': '方案名不能为空'}), 400

        data = body.get('data')
        if data is None:
            # 允许只创建元数据，data 留空待编辑时填充
            data = {
                'version': 2,
                'container': {'name': '40尺普柜', 'l': 12030, 'w': 2350, 'h': 2390},
                'cargos': [],
                'allowOverflow': False,
                'interactionMode': 'direct',
                'colorIndex': 0,
            }

        uid = get_user_id_from_token()
        # 当前作者下唯一性
        if ContainerLayout.query.filter_by(author_id=uid, name=name, is_deleted=0).first():
            return jsonify({
                'success': False,
                'message': f'已存在同名方案「{name}」，请改名后重试',
            }), 409

        layout = ContainerLayout(
            name=name,
            container_json=json.dumps(data, ensure_ascii=False),
            author_id=uid or '',
            author_name=_current_user_name(),
        )
        db.session.add(layout)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': layout.to_dict(include_data=True, current_user_id=uid),
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f'[container_layout] 创建方案失败: {e}')
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'}), 500


# ============================================================
# 详情（所有人可读）
# ============================================================

@container_layout_bp.route('/container-layouts/<int:lid>', methods=['GET'])
@route_permission(ROUTE_CONTAINER_LAYOUT_MANAGE)
def get_layout(lid):
    """获取单个货柜排布方案详情（含完整 JSON 数据）"""
    try:
        layout = ContainerLayout.query.get(lid)
        if not layout or layout.is_deleted:
            return jsonify({'success': False, 'message': '方案不存在'}), 404

        uid = get_user_id_from_token()
        return jsonify({
            'success': True,
            'data': layout.to_dict(include_data=True, current_user_id=uid),
        })
    except Exception as e:
        print(f'[container_layout] 获取详情失败: {e}')
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'}), 500


# ============================================================
# 更新（仅作者或管理员）
# ============================================================

@container_layout_bp.route('/container-layouts/<int:lid>', methods=['PUT'])
@route_permission(ROUTE_CONTAINER_LAYOUT_MANAGE)
def update_layout(lid):
    """更新货柜排布方案

    Body（至少包含其一）:
        data: 新的完整布局 JSON
        name: 新的方案名（仅作者本人可改，重名检测）

    权限：
        - 仅作者本人或 user_role == 'admin' 可调用
        - 403：非作者非管理员
        - 409：改名时新名字已被当前作者的其他方案占用
    """
    try:
        layout = ContainerLayout.query.get(lid)
        if not layout or layout.is_deleted:
            return jsonify({'success': False, 'message': '方案不存在'}), 404

        uid = get_user_id_from_token()
        role = get_user_role_from_token()
        if role != 'admin' and layout.author_id != uid:
            return jsonify({'success': False, 'message': '仅作者或管理员可修改此方案'}), 403

        body = request.get_json(silent=True) or {}

        # 更新布局数据
        if 'data' in body and body['data'] is not None:
            layout.container_json = json.dumps(body['data'], ensure_ascii=False)

        # 改名（仅作者本人可改自己的名字）
        if 'name' in body and body['name']:
            new_name = body['name'].strip()
            if new_name and new_name != layout.name:
                if role == 'admin':
                    # 管理员可改名，但需在新作者下唯一
                    dup = ContainerLayout.query.filter_by(
                        author_id=layout.author_id,
                        name=new_name,
                        is_deleted=0,
                    ).filter(ContainerLayout.id != lid).first()
                else:
                    dup = ContainerLayout.query.filter_by(
                        author_id=layout.author_id,
                        name=new_name,
                        is_deleted=0,
                    ).filter(ContainerLayout.id != lid).first()
                if dup:
                    return jsonify({'success': False, 'message': '该作者下已存在同名方案'}), 409
                layout.name = new_name

        layout.updated_at = datetime.now()
        db.session.commit()

        return jsonify({
            'success': True,
            'data': layout.to_dict(include_data=True, current_user_id=uid),
        })
    except Exception as e:
        db.session.rollback()
        print(f'[container_layout] 更新方案失败: {e}')
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


# ============================================================
# 删除（仅作者或管理员，软删除）
# ============================================================

@container_layout_bp.route('/container-layouts/<int:lid>', methods=['DELETE'])
@route_permission(ROUTE_CONTAINER_LAYOUT_MANAGE)
def delete_layout(lid):
    """软删除货柜排布方案

    权限：仅作者本人或 user_role == 'admin' 可调用
    """
    try:
        layout = ContainerLayout.query.get(lid)
        if not layout or layout.is_deleted:
            return jsonify({'success': False, 'message': '方案不存在'}), 404

        uid = get_user_id_from_token()
        role = get_user_role_from_token()
        if role != 'admin' and layout.author_id != uid:
            return jsonify({'success': False, 'message': '仅作者或管理员可删除此方案'}), 403

        layout.is_deleted = 1
        db.session.commit()

        return jsonify({'success': True, 'message': '方案已删除'})
    except Exception as e:
        db.session.rollback()
        print(f'[container_layout] 删除方案失败: {e}')
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500