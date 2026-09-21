"""Warehouse editor API."""

import json
from datetime import date, datetime

from flask import Blueprint, jsonify, request

from extensions import db
from app.constants.simple_permission_constants import ROUTE_WAREHOUSE_MANAGE
from app.models.business_operation_log import BusinessOperationLog
from app.models.employee import Employee
from app.models.warehouse import WarehouseItem, WarehouseMap, WarehouseObject
from app.utils.auth_utils import get_user_id_from_token, get_user_role_from_token, require_admin
from app.utils.simple_auth_utils import route_permission


warehouse_bp = Blueprint('warehouse', __name__, url_prefix='/api/warehouse')

ITEM_FIELDS = {
    'name', 'x_mm', 'y_mm', 'length_mm', 'width_mm', 'height_mm',
    'rotation', 'owner_group', 'color', 'remark', 'stocked_date',
}
OBJECT_FIELDS = {
    'name', 'type', 'x_mm', 'y_mm', 'length_mm', 'width_mm', 'rotation',
    'show_text', 'pattern', 'blocks_cargo', 'color',
}
OBJECT_TYPES = {'COLUMN', 'WALL', 'RESTRICTED', 'EQUIPMENT', 'PASSAGE', 'OTHER'}
OWNER_GROUPS = {'OVERSEAS', 'OTHER'}
ITEM_STATUSES = {'ACTIVE', 'SHIPPED'}


def _employee(uid):
    return Employee.query.filter_by(emp_id=uid).first() if uid else None


def _date_value(value, field_name):
    if value in (None, ''):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f'{field_name} 必须是 YYYY-MM-DD') from exc


def _int_value(value, field_name, positive=False):
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{field_name} 必须是整数') from exc
    if positive and value <= 0:
        raise ValueError(f'{field_name} 必须大于 0')
    return value


def _rotation(value):
    value = _int_value(value, 'rotation') % 360
    if value not in (0, 90, 180, 270):
        raise ValueError('rotation 只支持 0/90/180/270')
    return value


def _item_dict(item, employee_names=None):
    employee_names = employee_names or {}
    return {
        'id': item.id,
        'map_id': item.map_id,
        'name': item.name,
        'x_mm': item.x_mm,
        'y_mm': item.y_mm,
        'length_mm': item.length_mm,
        'width_mm': item.width_mm,
        'height_mm': item.height_mm,
        'rotation': item.rotation,
        'owner_group': item.owner_group,
        'color': item.color,
        'status': item.status,
        'stocked_date': item.stocked_date.isoformat() if item.stocked_date else None,
        'stocked_by': item.stocked_by,
        'stocked_by_name': employee_names.get(item.stocked_by),
        'remark': item.remark,
        'shipped_date': item.shipped_date.isoformat() if item.shipped_date else None,
        'shipped_at': item.shipped_at.isoformat() if item.shipped_at else None,
        'shipped_by': item.shipped_by,
        'shipped_by_name': employee_names.get(item.shipped_by),
        'shipped_remark': item.shipped_remark,
    }


def _object_dict(obj):
    return {
        'id': obj.id,
        'map_id': obj.map_id,
        'name': obj.name,
        'type': obj.type,
        'x_mm': obj.x_mm,
        'y_mm': obj.y_mm,
        'length_mm': obj.length_mm,
        'width_mm': obj.width_mm,
        'rotation': obj.rotation,
        'show_text': bool(obj.show_text),
        'pattern': obj.pattern,
        'blocks_cargo': bool(obj.blocks_cargo),
        'color': obj.color,
    }


def _map_dict(warehouse_map):
    return {
        'id': warehouse_map.id,
        'name': warehouse_map.name,
        'width_mm': warehouse_map.width_mm,
        'length_mm': warehouse_map.length_mm,
        'grid_columns': warehouse_map.grid_columns,
        'grid_rows': warehouse_map.grid_rows,
        'revision': warehouse_map.revision,
        'active': bool(warehouse_map.active),
        'created_at': warehouse_map.created_at.isoformat() if warehouse_map.created_at else None,
        'updated_at': warehouse_map.updated_at.isoformat() if warehouse_map.updated_at else None,
    }


def _snapshot(warehouse_map, include_shipped=False):
    items = WarehouseItem.query.filter_by(map_id=warehouse_map.id, is_deleted=0)
    if not include_shipped:
        items = items.filter_by(status='ACTIVE')
    items = items.order_by(WarehouseItem.id.asc()).all()
    employee_ids = {x for item in items for x in (item.stocked_by, item.shipped_by) if x}
    employee_names = {
        employee.emp_id: employee.name
        for employee in Employee.query.filter(Employee.emp_id.in_(employee_ids)).all()
    } if employee_ids else {}
    objects = WarehouseObject.query.filter_by(
        map_id=warehouse_map.id, is_deleted=0
    ).order_by(WarehouseObject.id.asc()).all()
    return {
        'map': _map_dict(warehouse_map),
        'items': [_item_dict(item, employee_names) for item in items],
        'objects': [_object_dict(obj) for obj in objects],
        'revision': warehouse_map.revision,
    }


def _audit(uid, operation_type, biz_id, details):
    db.session.add(BusinessOperationLog(
        module='warehouse',
        biz_id=str(biz_id),
        operation_type=operation_type,
        operator_id=uid,
        operation_details=json.dumps(details, ensure_ascii=False),
    ))


def _validate_map_data(data):
    allowed = {'name', 'width_mm', 'length_mm', 'grid_columns', 'grid_rows', 'active'}
    unknown = set(data) - allowed
    if unknown:
        raise ValueError(f'不支持的地图字段: {sorted(unknown)}')
    for key in ('width_mm', 'length_mm', 'grid_columns', 'grid_rows'):
        if key in data:
            data[key] = _int_value(data[key], key, positive=True)
    if 'name' in data:
        data['name'] = str(data['name']).strip()
        if not data['name']:
            raise ValueError('地图名称不能为空')
    if 'active' in data:
        data['active'] = 1 if data['active'] else 0
    return data


def _validate_item_data(data, require_all=False):
    unknown = set(data) - ITEM_FIELDS - {'id', '_client_id'}
    if unknown:
        raise ValueError(f'不支持的货物字段: {sorted(unknown)}')
    required = {'name', 'x_mm', 'y_mm', 'length_mm', 'width_mm', 'height_mm', 'owner_group'}
    if require_all and not required.issubset(data):
        raise ValueError(f'新增货物缺少字段: {sorted(required - set(data))}')
    for key in ('x_mm', 'y_mm'):
        if key in data:
            data[key] = _int_value(data[key], key)
    for key in ('length_mm', 'width_mm', 'height_mm'):
        if key in data:
            data[key] = _int_value(data[key], key, positive=True)
    if 'rotation' in data:
        data['rotation'] = _rotation(data['rotation'])
    if 'owner_group' in data and data['owner_group'] not in OWNER_GROUPS:
        raise ValueError('owner_group 只支持 OVERSEAS/OTHER')
    if 'stocked_date' in data:
        data['stocked_date'] = _date_value(data['stocked_date'], 'stocked_date')
    if 'name' in data:
        data['name'] = str(data['name']).strip()
        if not data['name']:
            raise ValueError('货物名称不能为空')
    return data


def _validate_object_data(data, require_all=False):
    unknown = set(data) - OBJECT_FIELDS - {'id', '_client_id'}
    if unknown:
        raise ValueError(f'不支持的障碍物字段: {sorted(unknown)}')
    required = {'name', 'type', 'x_mm', 'y_mm', 'length_mm', 'width_mm'}
    if require_all and not required.issubset(data):
        raise ValueError(f'新增障碍物缺少字段: {sorted(required - set(data))}')
    for key in ('x_mm', 'y_mm'):
        if key in data:
            data[key] = _int_value(data[key], key)
    for key in ('length_mm', 'width_mm'):
        if key in data:
            data[key] = _int_value(data[key], key, positive=True)
    if 'rotation' in data:
        data['rotation'] = _rotation(data['rotation'])
    if 'type' in data and data['type'] not in OBJECT_TYPES:
        raise ValueError(f'type 只支持: {sorted(OBJECT_TYPES)}')
    for key in ('show_text', 'blocks_cargo'):
        if key in data:
            data[key] = 1 if data[key] else 0
    if 'name' in data:
        data['name'] = str(data['name']).strip()
        if not data['name']:
            raise ValueError('障碍物名称不能为空')
    return data


@warehouse_bp.route('/maps', methods=['GET'])
@route_permission(ROUTE_WAREHOUSE_MANAGE)
def list_maps():
    try:
        maps = WarehouseMap.query.filter_by(active=1).order_by(WarehouseMap.id.asc()).all()
        return jsonify({'success': True, 'data': [_map_dict(item) for item in maps]})
    except Exception as exc:
        print(f'[warehouse] 获取楼层失败: {exc}')
        return jsonify({'success': False, 'message': '获取楼层失败'}), 500


@warehouse_bp.route('/maps', methods=['POST'])
@require_admin
def create_map():
    try:
        data = _validate_map_data(request.get_json(silent=True) or {})
        required = {'name', 'width_mm', 'length_mm', 'grid_columns', 'grid_rows'}
        if not required.issubset(data):
            return jsonify({'success': False, 'message': f'缺少字段: {sorted(required - set(data))}'}), 400
        data['active'] = data.get('active', 1)
        warehouse_map = WarehouseMap(**data, revision=1)
        db.session.add(warehouse_map)
        db.session.flush()
        uid = get_user_id_from_token()
        _audit(uid, 'create', warehouse_map.id, {'entity': 'map', 'name': warehouse_map.name})
        db.session.commit()
        return jsonify({'success': True, 'data': _map_dict(warehouse_map)}), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        print(f'[warehouse] 创建楼层失败: {exc}')
        return jsonify({'success': False, 'message': '创建楼层失败'}), 500


@warehouse_bp.route('/maps/<int:map_id>', methods=['GET'])
@route_permission(ROUTE_WAREHOUSE_MANAGE)
def get_map(map_id):
    warehouse_map = WarehouseMap.query.filter_by(id=map_id, active=1).first()
    if not warehouse_map:
        return jsonify({'success': False, 'message': '楼层不存在'}), 404
    try:
        return jsonify({'success': True, 'data': _snapshot(warehouse_map)})
    except Exception as exc:
        print(f'[warehouse] 获取楼层快照失败: {exc}')
        return jsonify({'success': False, 'message': '获取楼层快照失败'}), 500


@warehouse_bp.route('/maps/<int:map_id>/shipments', methods=['GET'])
@route_permission(ROUTE_WAREHOUSE_MANAGE)
def list_shipments(map_id):
    warehouse_map = WarehouseMap.query.filter_by(id=map_id, active=1).first()
    if not warehouse_map:
        return jsonify({'success': False, 'message': '楼层不存在'}), 404
    try:
        items = WarehouseItem.query.filter_by(
            map_id=map_id, is_deleted=0, status='SHIPPED'
        ).order_by(WarehouseItem.shipped_at.desc(), WarehouseItem.id.desc()).all()
        employee_ids = {x for item in items for x in (item.stocked_by, item.shipped_by) if x}
        names = {
            employee.emp_id: employee.name
            for employee in Employee.query.filter(Employee.emp_id.in_(employee_ids)).all()
        } if employee_ids else {}
        return jsonify({'success': True, 'data': [_item_dict(item, names) for item in items]})
    except Exception as exc:
        print(f'[warehouse] 获取出库记录失败: {exc}')
        return jsonify({'success': False, 'message': '获取出库记录失败'}), 500


def _save_items(warehouse_map, payload, uid, id_map, changes):
    item_payload = payload.get('items') or {}
    if not isinstance(item_payload, dict):
        raise ValueError('items 必须是对象')

    for raw in item_payload.get('created') or []:
        data = _validate_item_data(dict(raw), require_all=True)
        client_id = data.pop('_client_id', None)
        data.pop('id', None)
        data['rotation'] = data.get('rotation', 0)
        data['color'] = data.get('color') or '#4d96ff'
        data['status'] = 'ACTIVE'
        data['stocked_by'] = uid
        item = WarehouseItem(map_id=warehouse_map.id, **data)
        db.session.add(item)
        db.session.flush()
        if client_id is not None:
            id_map[str(client_id)] = item.id
        changes.append({'type': 'create', 'entity': 'item', 'id': item.id})

    for raw in item_payload.get('updated') or []:
        data = _validate_item_data(dict(raw))
        item_id = data.pop('id', None)
        data.pop('_client_id', None)
        item = WarehouseItem.query.filter_by(id=item_id, map_id=warehouse_map.id, is_deleted=0).first()
        if not item:
            raise ValueError(f'货物不存在: {item_id}')
        if item.status == 'SHIPPED':
            raise ValueError('已出库货物不能直接修改，请先恢复')
        for key, value in data.items():
            setattr(item, key, value)
        changes.append({'type': 'update', 'entity': 'item', 'id': item.id})

    for item_id in item_payload.get('deleted') or []:
        item = WarehouseItem.query.filter_by(id=item_id, map_id=warehouse_map.id, is_deleted=0).first()
        if not item:
            raise ValueError(f'货物不存在: {item_id}')
        item.is_deleted = 1
        item.deleted_at = datetime.now()
        changes.append({'type': 'delete', 'entity': 'item', 'id': item.id})

    for raw in item_payload.get('outbound') or []:
        raw = dict(raw)
        item_id = raw.get('id')
        item = WarehouseItem.query.filter_by(id=item_id, map_id=warehouse_map.id, is_deleted=0).first()
        if not item:
            raise ValueError(f'货物不存在: {item_id}')
        if item.status == 'SHIPPED':
            continue
        if item.owner_group == 'OTHER':
            raise ValueError('OTHER 货物不允许出库')
        item.status = 'SHIPPED'
        item.shipped_date = _date_value(raw.get('shipped_date') or date.today().isoformat(), 'shipped_date')
        item.shipped_at = datetime.now()
        item.shipped_by = uid
        item.shipped_remark = str(raw.get('shipped_remark') or '').strip()
        changes.append({'type': 'outbound', 'entity': 'item', 'id': item.id})

    for item_id in item_payload.get('restore') or []:
        item = WarehouseItem.query.filter_by(id=item_id, map_id=warehouse_map.id, is_deleted=0).first()
        if not item:
            raise ValueError(f'货物不存在: {item_id}')
        if item.status == 'SHIPPED':
            item.status = 'ACTIVE'
            changes.append({'type': 'restore', 'entity': 'item', 'id': item.id})


def _save_objects(warehouse_map, payload, role, changes):
    object_payload = payload.get('objects') or {}
    if not isinstance(object_payload, dict):
        raise ValueError('objects 必须是对象')
    has_changes = any(object_payload.get(key) for key in ('created', 'updated', 'deleted'))
    if has_changes and role != 'admin':
        raise PermissionError('只有管理员可以管理障碍物')

    for raw in object_payload.get('created') or []:
        data = _validate_object_data(dict(raw), require_all=True)
        data.pop('_client_id', None)
        data.pop('id', None)
        data['rotation'] = data.get('rotation', 0)
        obj = WarehouseObject(map_id=warehouse_map.id, **data)
        db.session.add(obj)
        db.session.flush()
        changes.append({'type': 'create', 'entity': 'object', 'id': obj.id})

    for raw in object_payload.get('updated') or []:
        data = _validate_object_data(dict(raw))
        object_id = data.pop('id', None)
        data.pop('_client_id', None)
        obj = WarehouseObject.query.filter_by(id=object_id, map_id=warehouse_map.id, is_deleted=0).first()
        if not obj:
            raise ValueError(f'障碍物不存在: {object_id}')
        for key, value in data.items():
            setattr(obj, key, value)
        changes.append({'type': 'update', 'entity': 'object', 'id': obj.id})

    for object_id in object_payload.get('deleted') or []:
        obj = WarehouseObject.query.filter_by(id=object_id, map_id=warehouse_map.id, is_deleted=0).first()
        if not obj:
            raise ValueError(f'障碍物不存在: {object_id}')
        obj.is_deleted = 1
        obj.deleted_at = datetime.now()
        changes.append({'type': 'delete', 'entity': 'object', 'id': obj.id})


@warehouse_bp.route('/maps/<int:map_id>/save', methods=['PUT'])
@route_permission(ROUTE_WAREHOUSE_MANAGE)
def save_map(map_id):
    warehouse_map = WarehouseMap.query.filter_by(id=map_id, active=1).first()
    if not warehouse_map:
        return jsonify({'success': False, 'message': '楼层不存在'}), 404
    body = request.get_json(silent=True) or {}
    uid = get_user_id_from_token()
    role = get_user_role_from_token()
    if not uid:
        return jsonify({'success': False, 'message': '无法确定当前操作人员'}), 401
    employee = _employee(uid)
    if not employee:
        return jsonify({'success': False, 'message': '当前员工不存在'}), 401
    try:
        base_revision = _int_value(body.get('base_revision'), 'base_revision')
        if warehouse_map.revision != base_revision:
            return jsonify({
                'success': False,
                'message': '楼层已被其他人修改，请重新加载后再保存',
                'current_revision': warehouse_map.revision,
            }), 409

        map_payload = body.get('map') or {}
        map_changed = bool(map_payload)
        if map_changed and role != 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以修改楼层结构'}), 403
        map_payload = _validate_map_data(dict(map_payload))
        changes = []
        id_map = {}
        _save_items(warehouse_map, body, uid, id_map, changes)
        _save_objects(warehouse_map, body, role, changes)
        for key, value in map_payload.items():
            setattr(warehouse_map, key, value)
        if map_changed:
            changes.append({'type': 'update', 'entity': 'map', 'id': warehouse_map.id})

        warehouse_map.revision += 1
        warehouse_map.updated_at = datetime.now()
        for change in changes:
            _audit(uid, change['type'], change['id'], {
                'entity': change['entity'],
                'map_id': warehouse_map.id,
                'save_revision': warehouse_map.revision,
            })
        db.session.commit()
        return jsonify({
            'success': True,
            'data': {
                **_snapshot(warehouse_map),
                'id_map': id_map,
                'changes': changes,
            },
        })
    except PermissionError as exc:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 403
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        print(f'[warehouse] 保存失败: {exc}')
        return jsonify({'success': False, 'message': 'Warehouse 保存失败'}), 500
