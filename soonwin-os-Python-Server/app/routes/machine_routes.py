from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
import os
import json
from .. import db
from ..models.machine import Machine, PartType
from ..utils.json_utils import import_json_data, export_json_data
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_MACHINE_MANAGE
from app.models.simple_permission import get_user_role_from_token
import uuid

machine_bp = Blueprint('machine_bp', __name__, url_prefix='/api')

@machine_bp.route('/machines', methods=['GET'])
@route_permission(ROUTE_MACHINE_MANAGE)
def get_machines():
    """获取所有机器列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 使用通用函数检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        # 过滤掉已删除的机器
        query = Machine.query.filter_by(is_deleted=0)
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        machines = pagination.items
        
        # 根据用户权限处理数据
        machine_data = []
        for machine in machines:
            machine_dict = machine.to_dict()
            if not is_admin:
                # 非管理员用户不显示原始价格
                machine_dict.pop('original_price', None)
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
        current_app.logger.error(f"获取机器列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines/<string:model>', methods=['GET'])
@route_permission(ROUTE_MACHINE_MANAGE)
def get_machine(model):
    """根据型号获取单个机器"""
    try:
        # 使用通用函数检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        machine = Machine.query.filter_by(model=model).first()
        if not machine:
            return jsonify({'success': False, 'message': '机器型号不存在'}), 404
        
        # 根据用户权限处理数据
        machine_dict = machine.to_dict()
        if not is_admin:
            # 非管理员用户不显示原始价格
            machine_dict.pop('original_price', None)
        
        return jsonify({
            'success': True,
            'data': machine_dict
        })
    except Exception as e:
        current_app.logger.error(f"获取机器信息失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines', methods=['POST'])
@route_permission(ROUTE_MACHINE_MANAGE)
def create_machine():
    """创建新机器"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        data = request.get_json()
        
        # 检查机器型号是否已存在
        existing_machine = Machine.query.filter_by(model=data.get('model')).first()
        if existing_machine:
            return jsonify({'success': False, 'message': '机器型号已存在'}), 400
        
        # 处理自定义属性
        custom_attrs = data.get('custom_attrs')
        if isinstance(custom_attrs, dict):
            import json as json_module
            custom_attrs = json_module.dumps(custom_attrs, ensure_ascii=False)
        
        # 处理数值字段类型转换
        added_count = data.get('added_count', 0)
        if added_count is not None:
            try:
                added_count = int(added_count)
            except:
                current_app.logger.warning(f"added_count 转换失败: {added_count}")
                added_count = 0
        
        original_price = data.get('original_price')
        if original_price is not None:
            try:
                from decimal import Decimal
                original_price = Decimal(str(original_price))
            except:
                current_app.logger.warning(f"original_price 转换失败: {original_price}")
                original_price = None
        
        show_price = data.get('show_price')
        if show_price is not None:
            try:
                from decimal import Decimal
                show_price = Decimal(str(show_price))
            except:
                current_app.logger.warning(f"show_price 转换失败: {show_price}")
                show_price = None
        
        # 定义字段映射，用于动态创建实例
        field_values = {
            'model': data.get('model'),
            'original_model': data.get('original_model'),
            'packing_speed': data.get('packing_speed'),
            'general_power': data.get('general_power'),
            'power_supply': data.get('power_supply'),
            'air_source': data.get('air_source'),
            'machine_weight': data.get('machine_weight'),
            'dimensions': data.get('dimensions'),
            'package_material': data.get('package_material'),
            'image': data.get('image'),
            'added_count': added_count,
            'original_price': original_price,
            'show_price': show_price,
            'custom_attrs': custom_attrs
        }
        
        machine = Machine(**field_values)
        
        db.session.add(machine)
        db.session.commit()
        
        # 根据用户权限处理返回数据
        machine_dict = machine.to_dict()
        if not is_admin:
            # 非管理员用户不显示原始价格（虽然这里不会执行，但保持代码一致性）
            machine_dict.pop('original_price', None)
        
        return jsonify({
            'success': True,
            'message': '机器创建成功',
            'data': machine_dict
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建机器失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines/<string:model>', methods=['PUT'])
@route_permission(ROUTE_MACHINE_MANAGE)
def update_machine(model):
    """更新机器信息"""
    try:
        machine = Machine.query.filter_by(model=model).first()
        if not machine:
            return jsonify({'success': False, 'message': '机器型号不存在'}), 404
        
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        data = request.get_json()
        
        # 处理数值字段类型转换
        if 'original_price' in data and data['original_price'] is not None:
            try:
                from decimal import Decimal
                data['original_price'] = Decimal(str(data['original_price']))
            except:
                current_app.logger.warning(f"original_price 转换失败: {data['original_price']}")
        
        if 'show_price' in data and data['show_price'] is not None:
            try:
                from decimal import Decimal
                data['show_price'] = Decimal(str(data['show_price']))
            except:
                current_app.logger.warning(f"show_price 转换失败: {data['show_price']}")
        
        if 'added_count' in data and data['added_count'] is not None:
            try:
                data['added_count'] = int(data['added_count'])
            except:
                current_app.logger.warning(f"added_count 转换失败: {data['added_count']}")
        
        # 定义需要批量更新的普通字段列表
        update_fields = [
            'original_model', 'packing_speed', 'general_power', 'power_supply',
            'air_source', 'machine_weight', 'dimensions', 'package_material',
            'image', 'added_count', 'original_price', 'show_price'
        ]
        
        # 批量更新普通字段
        for field in update_fields:
            if field in data:
                setattr(machine, field, data[field])
        
        # 单独处理需要特殊逻辑的字段（如 custom_attrs）
        if 'custom_attrs' in data:
            custom_attrs = data['custom_attrs']
            if isinstance(custom_attrs, dict):
                import json as json_module
                custom_attrs = json_module.dumps(custom_attrs, ensure_ascii=False)
            machine.custom_attrs = custom_attrs
        
        db.session.commit()
        
        # 根据用户权限处理返回数据
        machine_dict = machine.to_dict()
        if not is_admin:
            # 非管理员用户不显示原始价格（虽然这里不会执行，但保持代码一致性）
            machine_dict.pop('original_price', None)
        
        return jsonify({
            'success': True,
            'message': '机器更新成功',
            'data': machine_dict
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新机器失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines/<string:model>', methods=['DELETE'])
@route_permission(ROUTE_MACHINE_MANAGE)
def delete_machine(model):
    """逻辑删除机器（归档）"""
    try:
        machine = Machine.query.filter_by(model=model).first()
        if not machine:
            return jsonify({'success': False, 'message': '机器型号不存在'}), 404
        
        # 设置逻辑删除标记
        machine.is_deleted = 1
        machine.delete_time = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '机器已归档（逻辑删除）'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"归档机器失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/parts', methods=['GET'])
@route_permission(ROUTE_MACHINE_MANAGE)
def get_parts():
    """获取所有部件列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 使用通用函数检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        pagination = PartType.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        parts = pagination.items
        
        # 根据用户权限处理数据
        parts_data = []
        for part in parts:
            part_dict = part.to_dict()
            if not is_admin:
                # 非管理员用户不显示原始价格
                part_dict.pop('original_price', None)
            parts_data.append(part_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'parts': parts_data,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        })
    except Exception as e:
        current_app.logger.error(f"获取部件列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/parts/<int:part_type_id>', methods=['GET'])
@route_permission(ROUTE_MACHINE_MANAGE)
def get_part(part_type_id):
    """根据ID获取单个部件"""
    try:
        # 使用通用函数检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        part = PartType.query.filter_by(part_type_id=part_type_id).first()
        if not part:
            return jsonify({'success': False, 'message': '部件类型不存在'}), 404
        
        # 根据用户权限处理数据
        part_dict = part.to_dict()
        if not is_admin:
            # 非管理员用户不显示原始价格
            part_dict.pop('original_price', None)
        
        return jsonify({
            'success': True,
            'data': part_dict
        })
    except Exception as e:
        current_app.logger.error(f"获取部件信息失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/parts', methods=['POST'])
@route_permission(ROUTE_MACHINE_MANAGE)
def create_part():
    """创建新部件"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        data = request.get_json()
        
        # 检查部件型号是否已存在
        existing_part = PartType.query.filter_by(part_model=data.get('part_model')).first()
        if existing_part:
            return jsonify({'success': False, 'message': '部件型号已存在'}), 400
        
        # 处理数值字段类型转换
        original_price = data.get('original_price')
        if original_price is not None:
            try:
                from decimal import Decimal
                original_price = Decimal(str(original_price))
            except:
                current_app.logger.warning(f"original_price 转换失败: {original_price}")
                original_price = None
        
        show_price = data.get('show_price')
        if show_price is not None:
            try:
                from decimal import Decimal
                show_price = Decimal(str(show_price))
            except:
                current_app.logger.warning(f"show_price 转换失败: {show_price}")
                show_price = None
        
        # 定义字段映射，用于动态创建实例
        field_values = {
            'part_model': data.get('part_model'),
            'original_price': original_price,
            'show_price': show_price,
            'image': data.get('image')
        }
        
        part = PartType(**field_values)
        
        db.session.add(part)
        db.session.commit()
        
        # 根据用户权限处理返回数据
        part_dict = part.to_dict()
        if not is_admin:
            # 非管理员用户不显示原始价格（虽然这里不会执行，但保持代码一致性）
            part_dict.pop('original_price', None)
        
        return jsonify({
            'success': True,
            'message': '部件创建成功',
            'data': part_dict
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建部件失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/parts/<int:part_type_id>', methods=['PUT'])
@route_permission(ROUTE_MACHINE_MANAGE)
def update_part(part_type_id):
    """更新部件信息"""
    try:
        part = PartType.query.filter_by(part_type_id=part_type_id).first()
        if not part:
            return jsonify({'success': False, 'message': '部件类型不存在'}), 404
        
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        data = request.get_json()
        
        # 检查部件型号是否需要更新且是否已存在
        if 'part_model' in data:
            # 检查新部件型号是否已存在
            existing_part = PartType.query.filter_by(part_model=data['part_model']).first()
            if existing_part and existing_part.part_type_id != part_type_id:
                return jsonify({'success': False, 'message': '部件型号已存在'}), 400
            part.part_model = data['part_model']
        
        # 处理数值字段类型转换
        if 'original_price' in data and data['original_price'] is not None:
            try:
                from decimal import Decimal
                data['original_price'] = Decimal(str(data['original_price']))
            except:
                current_app.logger.warning(f"original_price 转换失败: {data['original_price']}")
        
        if 'show_price' in data and data['show_price'] is not None:
            try:
                from decimal import Decimal
                data['show_price'] = Decimal(str(data['show_price']))
            except:
                current_app.logger.warning(f"show_price 转换失败: {data['show_price']}")
        
        # 定义需要批量更新的普通字段列表
        update_fields = [
            'original_price', 'show_price', 'image'
        ]
        
        # 批量更新普通字段
        for field in update_fields:
            if field in data:
                setattr(part, field, data[field])
        
        db.session.commit()
        
        # 根据用户权限处理返回数据
        part_dict = part.to_dict()
        if not is_admin:
            # 非管理员用户不显示原始价格（虽然这里不会执行，但保持代码一致性）
            part_dict.pop('original_price', None)
        
        return jsonify({
            'success': True,
            'message': '部件更新成功',
            'data': part_dict
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新部件失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/parts/<int:part_type_id>', methods=['DELETE'])
@route_permission(ROUTE_MACHINE_MANAGE)
def delete_part(part_type_id):
    """删除部件"""
    try:
        part = PartType.query.filter_by(part_type_id=part_type_id).first()
        if not part:
            return jsonify({'success': False, 'message': '部件类型不存在'}), 404
        
        db.session.delete(part)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '部件删除成功'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除部件失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/parts/import-json', methods=['POST'])
@route_permission(ROUTE_MACHINE_MANAGE)
def import_parts_json():
    """直接从JSON数据导入部件数据（不需要文件上传）"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '未提供JSON数据'}), 400
        
        # 检查数据是否为列表格式
        if not isinstance(data, list):
            # 如果是单个对象，转换为列表
            if isinstance(data, dict):
                data = [data]
            else:
                return jsonify({'success': False, 'message': 'JSON数据格式错误，应为对象或对象数组'}), 400
        
        # 使用通用JSON工具导入数据
        result = import_json_data('part', data)
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'data': {
                'imported_count': result['imported_count'],
                'failed_count': result['failed_count'],
                'failed_records': result['failed_records']
            }
        })
    except Exception as e:
        current_app.logger.error(f"导入部件JSON数据失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/parts/export-json', methods=['GET'])
@route_permission(ROUTE_MACHINE_MANAGE)
def export_parts_json():
    """导出部件数据为JSON格式"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        # 获取过滤参数
        filters = {}
        # 可以根据需要添加过滤参数处理
        
        # 使用通用JSON工具导出数据
        data = export_json_data('part', filters)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        current_app.logger.error(f"导出部件数据失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines/import', methods=['POST'])
@route_permission(ROUTE_MACHINE_MANAGE)
def import_machines():
    """从JSON文件导入机器数据（保留原有功能）"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未提供文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'}), 400
        
        if not file.filename.lower().endswith('.json'):
            return jsonify({'success': False, 'message': '只支持JSON文件'}), 400
        
        try:
            content = file.read().decode('utf-8')
            data = json.loads(content)
        except json.JSONDecodeError:
            return jsonify({'success': False, 'message': 'JSON文件格式错误'}), 400
        
        # 检查数据是否为列表格式
        if not isinstance(data, list):
            # 如果是单个对象，转换为列表
            if isinstance(data, dict):
                data = [data]
            else:
                return jsonify({'success': False, 'message': 'JSON数据格式错误，应为对象数组'}), 400
        
        # 使用通用JSON工具导入数据
        result = import_json_data('machine', data)
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'data': {
                'imported_count': result['imported_count'],
                'failed_count': result['failed_count'],
                'failed_records': result['failed_records']
            }
        })
    except Exception as e:
        current_app.logger.error(f"导入机器数据失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines/import-json', methods=['POST'])
@route_permission(ROUTE_MACHINE_MANAGE)
def import_machines_json():
    """直接从JSON数据导入机器数据（不需要文件上传）"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '未提供JSON数据'}), 400
        
        # 检查数据是否为列表格式
        if not isinstance(data, list):
            # 如果是单个对象，转换为列表
            if isinstance(data, dict):
                data = [data]
            else:
                return jsonify({'success': False, 'message': 'JSON数据格式错误，应为对象或对象数组'}), 400
        
        # 使用通用JSON工具导入数据
        result = import_json_data('machine', data)
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'data': {
                'imported_count': result['imported_count'],
                'failed_count': result['failed_count'],
                'failed_records': result['failed_records']
            }
        })
    except Exception as e:
        current_app.logger.error(f"导入机器JSON数据失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines/export-json', methods=['GET'])
@route_permission(ROUTE_MACHINE_MANAGE)
def export_machines_json():
    """导出机器数据为JSON格式"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'
        
        # 获取过滤参数
        filters = {}
        # 可以根据需要添加过滤参数处理
        
        # 使用通用JSON工具导出数据
        data = export_json_data('machine', filters)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        current_app.logger.error(f"导出机器数据失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
