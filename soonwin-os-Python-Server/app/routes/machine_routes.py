from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
import os
import json
from .. import db
from ..models.machine import Machine, PartType
from ..models.machine_new import MachineNew
from ..utils.json_utils import import_json_data, export_json_data
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_MACHINE_MANAGE, ROUTE_MACHINE_LIST, ROUTE_UPLOAD_MANAGE
from app.models.simple_permission import get_user_role_from_token
import uuid

machine_bp = Blueprint('machine_bp', __name__, url_prefix='/api')

# @machine_bp.route('/machines', methods=['GET'])
# @route_permission(ROUTE_MACHINE_LIST)
# def get_machines():
#     """获取所有机器列表"""
#     try:
#         page = request.args.get('page', 1, type=int)
#         per_page = request.args.get('per_page', 10, type=int)

#         # 使用通用函数检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         # 过滤掉已删除的机器
#         query = Machine.query.filter_by(is_deleted=0)
#         pagination = query.paginate(
#             page=page, per_page=per_page, error_out=False
#         )
#         machines = pagination.items

#         # 根据用户权限处理数据
#         machine_data = []
#         for machine in machines:
#             machine_dict = machine.to_dict()
#             if not is_admin:
#                 # 非管理员用户不显示原始价格
#                 machine_dict.pop('original_price', None)
#             machine_data.append(machine_dict)

#         return jsonify({
#             'success': True,
#             'data': {
#                 'machines': machine_data,
#                 'total': pagination.total,
#                 'pages': pagination.pages,
#                 'current_page': page
#             }
#         })
#     except Exception as e:
#         current_app.logger.error(f"获取机器列表失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/machines/<string:model>', methods=['GET'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def get_machine(model):
#     """根据型号获取单个机器"""
#     try:
#         # 使用通用函数检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         machine = Machine.query.filter_by(model=model).first()
#         if not machine:
#             return jsonify({'success': False, 'message': '机器型号不存在'}), 404

#         # 根据用户权限处理数据
#         machine_dict = machine.to_dict()
#         if not is_admin:
#             # 非管理员用户不显示原始价格
#             machine_dict.pop('original_price', None)

#         return jsonify({
#             'success': True,
#             'data': machine_dict
#         })
#     except Exception as e:
#         current_app.logger.error(f"获取机器信息失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/machines', methods=['POST'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def create_machine():
#     """创建新机器"""
#     try:
#         # 检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         data = request.get_json()

#         # 检查机器型号是否已存在
#         existing_machine = Machine.query.filter_by(model=data.get('model')).first()
#         if existing_machine:
#             return jsonify({'success': False, 'message': '机器型号已存在'}), 400

#         # 处理自定义属性
#         custom_attrs = data.get('custom_attrs')
#         if isinstance(custom_attrs, dict):
#             import json as json_module
#             custom_attrs = json_module.dumps(custom_attrs, ensure_ascii=False)

#         # 处理数值字段类型转换
#         added_count = data.get('added_count', 0)
#         if added_count is not None:
#             try:
#                 added_count = int(added_count)
#             except:
#                 current_app.logger.warning(f"added_count 转换失败: {added_count}")
#                 added_count = 0

#         original_price = data.get('original_price')
#         if original_price is not None:
#             try:
#                 from decimal import Decimal
#                 original_price = Decimal(str(original_price))
#             except:
#                 current_app.logger.warning(f"original_price 转换失败: {original_price}")
#                 original_price = None

#         show_price = data.get('show_price')
#         if show_price is not None:
#             try:
#                 from decimal import Decimal
#                 show_price = Decimal(str(show_price))
#             except:
#                 current_app.logger.warning(f"show_price 转换失败: {show_price}")
#                 show_price = None

#         # 定义字段映射，用于动态创建实例
#         field_values = {
#             'model': data.get('model'),
#             'original_model': data.get('original_model'),
#             'packing_speed': data.get('packing_speed'),
#             'general_power': data.get('general_power'),
#             'power_supply': data.get('power_supply'),
#             'air_source': data.get('air_source'),
#             'machine_weight': data.get('machine_weight'),
#             'dimensions': data.get('dimensions'),
#             'package_material': data.get('package_material'),
#             'image': data.get('image'),
#             'added_count': added_count,
#             'original_price': original_price,
#             'show_price': show_price,
#             'custom_attrs': custom_attrs
#         }

#         machine = Machine(**field_values)

#         db.session.add(machine)
#         db.session.commit()

#         # 根据用户权限处理返回数据
#         machine_dict = machine.to_dict()
#         if not is_admin:
#             # 非管理员用户不显示原始价格（虽然这里不会执行，但保持代码一致性）
#             machine_dict.pop('original_price', None)

#         return jsonify({
#             'success': True,
#             'message': '机器创建成功',
#             'data': machine_dict
#         })
#     except Exception as e:
#         db.session.rollback()
#         current_app.logger.error(f"创建机器失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/machines/<string:model>', methods=['PUT'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def update_machine(model):
#     """更新机器信息"""
#     try:
#         machine = Machine.query.filter_by(model=model).first()
#         if not machine:
#             return jsonify({'success': False, 'message': '机器型号不存在'}), 404

#         # 检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         data = request.get_json()

#         # 处理数值字段类型转换
#         if 'original_price' in data and data['original_price'] is not None:
#             try:
#                 from decimal import Decimal
#                 data['original_price'] = Decimal(str(data['original_price']))
#             except:
#                 current_app.logger.warning(f"original_price 转换失败: {data['original_price']}")

#         if 'show_price' in data and data['show_price'] is not None:
#             try:
#                 from decimal import Decimal
#                 data['show_price'] = Decimal(str(data['show_price']))
#             except:
#                 current_app.logger.warning(f"show_price 转换失败: {data['show_price']}")

#         if 'added_count' in data and data['added_count'] is not None:
#             try:
#                 data['added_count'] = int(data['added_count'])
#             except:
#                 current_app.logger.warning(f"added_count 转换失败: {data['added_count']}")

#         # 定义需要批量更新的普通字段列表
#         update_fields = [
#             'original_model', 'packing_speed', 'general_power', 'power_supply',
#             'air_source', 'machine_weight', 'dimensions', 'package_material',
#             'image', 'added_count', 'original_price', 'show_price'
#         ]

#         # 批量更新普通字段
#         for field in update_fields:
#             if field in data:
#                 setattr(machine, field, data[field])

#         # 单独处理需要特殊逻辑的字段（如 custom_attrs）
#         if 'custom_attrs' in data:
#             custom_attrs = data['custom_attrs']
#             if isinstance(custom_attrs, dict):
#                 import json as json_module
#                 custom_attrs = json_module.dumps(custom_attrs, ensure_ascii=False)
#             machine.custom_attrs = custom_attrs

#         db.session.commit()

#         # 根据用户权限处理返回数据
#         machine_dict = machine.to_dict()
#         if not is_admin:
#             # 非管理员用户不显示原始价格（虽然这里不会执行，但保持代码一致性）
#             machine_dict.pop('original_price', None)

#         return jsonify({
#             'success': True,
#             'message': '机器更新成功',
#             'data': machine_dict
#         })
#     except Exception as e:
#         db.session.rollback()
#         current_app.logger.error(f"更新机器失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/machines/<string:model>', methods=['DELETE'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def delete_machine(model):
#     """逻辑删除机器（归档）"""
#     try:
#         machine = Machine.query.filter_by(model=model).first()
#         if not machine:
#             return jsonify({'success': False, 'message': '机器型号不存在'}), 404

#         # 设置逻辑删除标记
#         machine.is_deleted = 1
#         machine.delete_time = datetime.utcnow()

#         db.session.commit()

#         return jsonify({
#             'success': True,
#             'message': '机器已归档（逻辑删除）'
#         })
#     except Exception as e:
#         db.session.rollback()
#         current_app.logger.error(f"归档机器失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/parts', methods=['GET'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def get_parts():
#     """获取所有部件列表"""
#     try:
#         page = request.args.get('page', 1, type=int)
#         per_page = request.args.get('per_page', 10, type=int)

#         # 使用通用函数检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         pagination = PartType.query.paginate(
#             page=page, per_page=per_page, error_out=False
#         )
#         parts = pagination.items

#         # 根据用户权限处理数据
#         parts_data = []
#         for part in parts:
#             part_dict = part.to_dict()
#             if not is_admin:
#                 # 非管理员用户不显示原始价格
#                 part_dict.pop('original_price', None)
#             parts_data.append(part_dict)

#         return jsonify({
#             'success': True,
#             'data': {
#                 'parts': parts_data,
#                 'total': pagination.total,
#                 'pages': pagination.pages,
#                 'current_page': page
#             }
#         })
#     except Exception as e:
#         current_app.logger.error(f"获取部件列表失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/parts/<int:part_type_id>', methods=['GET'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def get_part(part_type_id):
#     """根据ID获取单个部件"""
#     try:
#         # 使用通用函数检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         part = PartType.query.filter_by(part_type_id=part_type_id).first()
#         if not part:
#             return jsonify({'success': False, 'message': '部件类型不存在'}), 404

#         # 根据用户权限处理数据
#         part_dict = part.to_dict()
#         if not is_admin:
#             # 非管理员用户不显示原始价格
#             part_dict.pop('original_price', None)

#         return jsonify({
#             'success': True,
#             'data': part_dict
#         })
#     except Exception as e:
#         current_app.logger.error(f"获取部件信息失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/parts', methods=['POST'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def create_part():
#     """创建新部件"""
#     try:
#         # 检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         data = request.get_json()

#         # 检查部件型号是否已存在
#         existing_part = PartType.query.filter_by(part_model=data.get('part_model')).first()
#         if existing_part:
#             return jsonify({'success': False, 'message': '部件型号已存在'}), 400

#         # 处理数值字段类型转换
#         original_price = data.get('original_price')
#         if original_price is not None:
#             try:
#                 from decimal import Decimal
#                 original_price = Decimal(str(original_price))
#             except:
#                 current_app.logger.warning(f"original_price 转换失败: {original_price}")
#                 original_price = None

#         show_price = data.get('show_price')
#         if show_price is not None:
#             try:
#                 from decimal import Decimal
#                 show_price = Decimal(str(show_price))
#             except:
#                 current_app.logger.warning(f"show_price 转换失败: {show_price}")
#                 show_price = None

#         # 定义字段映射，用于动态创建实例
#         field_values = {
#             'part_model': data.get('part_model'),
#             'original_price': original_price,
#             'show_price': show_price,
#             'image': data.get('image')
#         }

#         part = PartType(**field_values)

#         db.session.add(part)
#         db.session.commit()

#         # 根据用户权限处理返回数据
#         part_dict = part.to_dict()
#         if not is_admin:
#             # 非管理员用户不显示原始价格（虽然这里不会执行，但保持代码一致性）
#             part_dict.pop('original_price', None)

#         return jsonify({
#             'success': True,
#             'message': '部件创建成功',
#             'data': part_dict
#         })
#     except Exception as e:
#         db.session.rollback()
#         current_app.logger.error(f"创建部件失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/parts/<int:part_type_id>', methods=['PUT'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def update_part(part_type_id):
#     """更新部件信息"""
#     try:
#         part = PartType.query.filter_by(part_type_id=part_type_id).first()
#         if not part:
#             return jsonify({'success': False, 'message': '部件类型不存在'}), 404

#         # 检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         data = request.get_json()

#         # 检查部件型号是否需要更新且是否已存在
#         if 'part_model' in data:
#             # 检查新部件型号是否已存在
#             existing_part = PartType.query.filter_by(part_model=data['part_model']).first()
#             if existing_part and existing_part.part_type_id != part_type_id:
#                 return jsonify({'success': False, 'message': '部件型号已存在'}), 400
#             part.part_model = data['part_model']

#         # 处理数值字段类型转换
#         if 'original_price' in data and data['original_price'] is not None:
#             try:
#                 from decimal import Decimal
#                 data['original_price'] = Decimal(str(data['original_price']))
#             except:
#                 current_app.logger.warning(f"original_price 转换失败: {data['original_price']}")

#         if 'show_price' in data and data['show_price'] is not None:
#             try:
#                 from decimal import Decimal
#                 data['show_price'] = Decimal(str(data['show_price']))
#             except:
#                 current_app.logger.warning(f"show_price 转换失败: {data['show_price']}")

#         # 定义需要批量更新的普通字段列表
#         update_fields = [
#             'original_price', 'show_price', 'image'
#         ]

#         # 批量更新普通字段
#         for field in update_fields:
#             if field in data:
#                 setattr(part, field, data[field])

#         db.session.commit()

#         # 根据用户权限处理返回数据
#         part_dict = part.to_dict()
#         if not is_admin:
#             # 非管理员用户不显示原始价格（虽然这里不会执行，但保持代码一致性）
#             part_dict.pop('original_price', None)

#         return jsonify({
#             'success': True,
#             'message': '部件更新成功',
#             'data': part_dict
#         })
#     except Exception as e:
#         db.session.rollback()
#         current_app.logger.error(f"更新部件失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/parts/<int:part_type_id>', methods=['DELETE'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def delete_part(part_type_id):
#     """删除部件"""
#     try:
#         part = PartType.query.filter_by(part_type_id=part_type_id).first()
#         if not part:
#             return jsonify({'success': False, 'message': '部件类型不存在'}), 404

#         db.session.delete(part)
#         db.session.commit()

#         return jsonify({
#             'success': True,
#             'message': '部件删除成功'
#         })
#     except Exception as e:
#         db.session.rollback()
#         current_app.logger.error(f"删除部件失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/parts/import-json', methods=['POST'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def import_parts_json():
#     """直接从JSON数据导入部件数据（不需要文件上传）"""
#     try:
#         data = request.get_json()

#         if not data:
#             return jsonify({'success': False, 'message': '未提供JSON数据'}), 400

#         # 检查数据是否为列表格式
#         if not isinstance(data, list):
#             # 如果是单个对象，转换为列表
#             if isinstance(data, dict):
#                 data = [data]
#             else:
#                 return jsonify({'success': False, 'message': 'JSON数据格式错误，应为对象或对象数组'}), 400

#         # 使用通用JSON工具导入数据
#         result = import_json_data('part', data)

#         return jsonify({
#             'success': result['success'],
#             'message': f"成功处理 {result['total_processed']} 条数据，导入 {result['success_count']} 条，失败 {result['error_count']} 条",
#             'data': {
#                 'imported_count': result['success_count'],
#                 'failed_count': result['error_count'],
#                 'failed_records': result.get('errors', [])
#             }
#         })
#     except Exception as e:
#         current_app.logger.error(f"导入部件JSON数据失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/parts/export-json', methods=['GET'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def export_parts_json():
#     """导出部件数据为JSON格式"""
#     try:
#         # 检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         # 获取过滤参数
#         filters = {}
#         # 可以根据需要添加过滤参数处理

#         # 使用通用JSON工具导出数据
#         data = export_json_data('part', filters)

#         return jsonify({
#             'success': True,
#             'data': data
#         })
#     except Exception as e:
#         current_app.logger.error(f"导出部件数据失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/machines/import', methods=['POST'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def import_machines():
#     """从JSON文件导入机器数据（保留原有功能）"""
#     try:
#         # 检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         if 'file' not in request.files:
#             return jsonify({'success': False, 'message': '未提供文件'}), 400

#         file = request.files['file']
#         if file.filename == '':
#             return jsonify({'success': False, 'message': '未选择文件'}), 400

#         if not file.filename.lower().endswith('.json'):
#             return jsonify({'success': False, 'message': '只支持JSON文件'}), 400

#         try:
#             content = file.read().decode('utf-8')
#             data = json.loads(content)
#         except json.JSONDecodeError:
#             return jsonify({'success': False, 'message': 'JSON文件格式错误'}), 400

#         # 检查数据是否为列表格式
#         if not isinstance(data, list):
#             # 如果是单个对象，转换为列表
#             if isinstance(data, dict):
#                 data = [data]
#             else:
#                 return jsonify({'success': False, 'message': 'JSON数据格式错误，应为对象数组'}), 400

#         # 使用通用JSON工具导入数据
#         result = import_json_data('machine', data)

#         return jsonify({
#             'success': result['success'],
#             'message': result['message'],
#             'data': {
#                 'imported_count': result['imported_count'],
#                 'failed_count': result['failed_count'],
#                 'failed_records': result['failed_records']
#             }
#         })
#     except Exception as e:
#         current_app.logger.error(f"导入机器数据失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/machines/import-json', methods=['POST'])
# @route_permission(ROUTE_UPLOAD_MANAGE)
# def import_machines_json():
#     """直接从JSON数据导入机器数据（不需要文件上传）"""
#     try:
#         # 检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         data = request.get_json()

#         if not data:
#             return jsonify({'success': False, 'message': '未提供JSON数据'}), 400

#         # 检查数据是否为列表格式
#         if not isinstance(data, list):
#             # 如果是单个对象，转换为列表
#             if isinstance(data, dict):
#                 data = [data]
#             else:
#                 return jsonify({'success': False, 'message': 'JSON数据格式错误，应为对象或对象数组'}), 400

#         # 使用通用JSON工具导入数据
#         result = import_json_data('machine', data)

#         return jsonify({
#             'success': result['success'],
#             'message': f"成功处理 {result['total_processed']} 条数据，导入 {result['success_count']} 条，失败 {result['error_count']} 条",
#             'data': {
#                 'imported_count': result['success_count'],
#                 'failed_count': result['error_count'],
#                 'failed_records': result.get('errors', [])
#             }
#         })
#     except Exception as e:
#         current_app.logger.error(f"导入机器JSON数据失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


# @machine_bp.route('/machines/export-json', methods=['GET'])
# @route_permission(ROUTE_MACHINE_MANAGE)
# def export_machines_json():
#     """导出机器数据为JSON格式"""
#     try:
#         # 检查用户权限
#         user_role = get_user_role_from_token()
#         is_admin = user_role == 'admin'

#         # 获取过滤参数
#         filters = {}
#         # 可以根据需要添加过滤参数处理

#         # 使用通用JSON工具导出数据
#         data = export_json_data('machine', filters)

#         return jsonify({
#             'success': True,
#             'data': data
#         })
#     except Exception as e:
#         current_app.logger.error(f"导出机器数据失败: {str(e)}")
#         return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new', methods=['GET'])
@route_permission(ROUTE_MACHINE_MANAGE)
def get_machines_new():
    """获取所有新机器列表（支持搜索）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)  # 搜索关键词

        # 使用通用函数检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        # 构建查询
        query = MachineNew.query.filter_by(is_deleted=0).order_by(MachineNew.id.desc())

        # 如果提供搜索关键词，则在search_key中搜索
        if search:
            query = query.filter(MachineNew.search_key.like(f'%{search}%'))

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
        current_app.logger.error(f"获取新机器列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/<int:id>', methods=['GET'])
@route_permission(ROUTE_MACHINE_MANAGE)
def get_machine_new(id):
    """根据ID获取单个新机器"""
    try:
        # 使用通用函数检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        machine = MachineNew.query.filter_by(id=id, is_deleted=0).first()
        if not machine:
            return jsonify({'success': False, 'message': '机器不存在'}), 404

        # 根据用户权限决定是否包含价格字段
        include_price = is_admin
        machine_dict = machine.to_dict(include_price=include_price)

        return jsonify({
            'success': True,
            'data': machine_dict
        })
    except Exception as e:
        current_app.logger.error(f"获取机器信息失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new', methods=['POST'])
@route_permission(ROUTE_UPLOAD_MANAGE)
def create_machine_new():
    """创建新机器"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        data = request.get_json()

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

        machine_type = data.get('machine_type', 0)
        if machine_type is not None:
            try:
                machine_type = int(machine_type)
            except:
                current_app.logger.warning(f"machine_type 转换失败: {machine_type}")
                machine_type = 0

        # 创建机器对象
        machine = MachineNew(
            model=data.get('model'),
            original_model=data.get('original_model'),
            machine_weight=data.get('machine_weight'),
            dimensions=data.get('dimensions'),
            general_power=data.get('general_power'),
            power_supply=data.get('power_supply'),
            image=data.get('image'),
            added_count=added_count,
            show_price=show_price,
            original_price=original_price,
            machine_type=machine_type,
            remark=data.get('remark'),
            brand=data.get('brand'),
            custom_attrs=custom_attrs
        )

        # 自动生成搜索关键词
        machine.search_key = machine._generate_search_key()

        db.session.add(machine)
        db.session.commit()

        # 根据用户权限决定是否包含价格字段
        include_price = is_admin
        machine_dict = machine.to_dict(include_price=include_price)

        return jsonify({
            'success': True,
            'message': '机器创建成功',
            'data': machine_dict
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建新机器失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/<int:id>', methods=['PUT'])
@route_permission(ROUTE_UPLOAD_MANAGE)
def update_machine_new(id):
    """更新新机器信息"""
    try:
        machine = MachineNew.query.filter_by(id=id, is_deleted=0).first()
        if not machine:
            return jsonify({'success': False, 'message': '机器不存在'}), 404

        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        data = request.get_json()

        # 检查机器型号是否需要更新且是否已存在其他机器使用该型号
        if 'model' in data:
            machine.model = data['model']

        # 处理数值字段类型转换
        if 'original_price' in data and data['original_price'] is not None:
            try:
                from decimal import Decimal
                machine.original_price = Decimal(str(data['original_price']))
            except:
                current_app.logger.warning(f"original_price 转换失败: {data['original_price']}")

        if 'show_price' in data and data['show_price'] is not None:
            try:
                from decimal import Decimal
                machine.show_price = Decimal(str(data['show_price']))
            except:
                current_app.logger.warning(f"show_price 转换失败: {data['show_price']}")

        if 'added_count' in data and data['added_count'] is not None:
            try:
                machine.added_count = int(data['added_count'])
            except:
                current_app.logger.warning(f"added_count 转换失败: {data['added_count']}")

        if 'machine_type' in data and data['machine_type'] is not None:
            try:
                machine.machine_type = int(data['machine_type'])
            except:
                current_app.logger.warning(f"machine_type 转换失败: {data['machine_type']}")

        # 定义需要批量更新的普通字段列表
        update_fields = [
            'original_model', 'machine_weight', 'dimensions', 'general_power',
            'power_supply', 'image', 'remark', 'brand'
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

        # 重新生成搜索关键词
        machine.search_key = machine._generate_search_key()

        db.session.commit()

        # 根据用户权限决定是否包含价格字段
        include_price = is_admin
        machine_dict = machine.to_dict(include_price=include_price)

        return jsonify({
            'success': True,
            'message': '机器更新成功',
            'data': machine_dict
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新新机器失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/<int:id>', methods=['DELETE'])
@route_permission(ROUTE_MACHINE_MANAGE)
def delete_machine_new(id):
    """逻辑删除新机器（归档）"""
    try:
        machine = MachineNew.query.filter_by(id=id, is_deleted=0).first()
        if not machine:
            return jsonify({'success': False, 'message': '机器不存在'}), 404

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
        current_app.logger.error(f"归档新机器失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/import-json', methods=['POST'])
@route_permission(ROUTE_UPLOAD_MANAGE)
def import_machines_new_json():
    """直接从JSON数据导入新机器数据（不需要文件上传）"""
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
        result = import_json_data('machine_new', data)

        return jsonify({
            'success': result['success'],
            'message': f"成功处理 {result['total_processed']} 条数据，导入 {result['success_count']} 条，失败 {result['error_count']} 条",
            'data': {
                'imported_count': result['success_count'],
                'failed_count': result['error_count'],
                'failed_records': result.get('errors', [])
            }
        })
    except Exception as e:
        current_app.logger.error(f"导入新机器JSON数据失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/export-json', methods=['GET'])
@route_permission(ROUTE_MACHINE_MANAGE)
def export_machines_new_json():
    """导出新机器数据为JSON格式"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        # 获取过滤参数
        filters = {}
        # 可以根据需要添加过滤参数处理

        # 使用通用JSON工具导出数据
        data = export_json_data('machine_new', filters, is_admin=is_admin)

        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        current_app.logger.error(f"导出新机器数据失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/<int:id>/upload-thumb', methods=['POST'])
@route_permission(ROUTE_UPLOAD_MANAGE)
def upload_machine_thumb(id):
    """为指定设备上传缩略图（替换原有图片）"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        # 验证设备是否存在
        machine = MachineNew.query.filter_by(id=id, is_deleted=0).first()
        if not machine:
            return jsonify({'success': False, 'message': '设备不存在'}), 404

        # 获取上传的文件
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有文件被上传'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'}), 400

        # 验证文件类型（仅允许图片）
        allowed_extensions = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({'success': False, 'message': '仅支持PNG, JPG, JPEG, WEBP, GIF, BMP格式的图片'}), 400

        # 创建上传目录
        base_path = os.path.join(current_app.root_path, '..')
        machine_thumb_dir = os.path.join(base_path, 'assets', 'Media', 'Machine')
        os.makedirs(machine_thumb_dir, exist_ok=True)

        # 生成唯一文件名
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{machine.model}_{uuid.uuid4().hex[:8]}.{file_ext}"

        # 保存新文件
        file_path = os.path.join(machine_thumb_dir, unique_filename)
        file.save(file_path)

        # 获取新文件的相对路径
        relative_path = os.path.relpath(file_path, base_path).replace('\\', '/')

        # 如果原图路径不是默认图片，尝试删除原图
        if machine.image and not machine.image.endswith('sample.png'):
            try:
                old_file_path = os.path.join(base_path, machine.image)
                if os.path.exists(old_file_path) and os.path.isfile(old_file_path):
                    os.remove(old_file_path)
            except Exception as e:
                current_app.logger.warning(f"删除原缩略图失败: {str(e)}")

        # 更新机器的缩略图路径
        machine.image = relative_path
        # 重新生成搜索关键词
        machine.search_key = machine._generate_search_key()

        db.session.commit()

        # 根据用户权限决定是否包含价格字段
        include_price = is_admin
        machine_dict = machine.to_dict(include_price=include_price)

        return jsonify({
            'success': True,
            'message': '缩略图上传成功',
            'data': {
                'machine': machine_dict,
                'new_thumb_path': relative_path
            }
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"上传缩略图失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/recycle-bin', methods=['GET'])
@route_permission(ROUTE_MACHINE_MANAGE)
def get_deleted_machines():
    """获取回收站中的已删除机器列表（支持分页）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # 使用通用函数检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        # 构建查询，只获取已删除的机器，按ID降序排列
        query = MachineNew.query.filter_by(is_deleted=1).order_by(MachineNew.id.desc())

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
        current_app.logger.error(f"获取回收站机器列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/recycle-bin/<int:id>/restore', methods=['PUT'])
@route_permission(ROUTE_MACHINE_MANAGE)
def restore_machine_from_recycle_bin(id):
    """从回收站恢复机器"""
    try:
        # 验证机器是否存在（包括已删除的）
        machine = MachineNew.query.filter_by(id=id, is_deleted=1).first()
        if not machine:
            return jsonify({'success': False, 'message': '机器不存在或已在回收站外'}), 404

        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        # 恢复机器（取消逻辑删除标记）
        machine.is_deleted = 0
        machine.delete_time = None  # 清除删除时间

        db.session.commit()

        # 根据用户权限决定是否包含价格字段
        include_price = is_admin
        machine_dict = machine.to_dict(include_price=include_price)

        return jsonify({
            'success': True,
            'message': '机器恢复成功',
            'data': machine_dict
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"恢复机器失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/recycle-bin/<int:id>/permanent-delete', methods=['DELETE'])
@route_permission(ROUTE_MACHINE_MANAGE)
def permanent_delete_machine_from_recycle_bin(id):
    """从回收站永久删除机器"""
    try:
        # 验证机器是否存在（包括已删除的）
        machine = MachineNew.query.filter_by(id=id, is_deleted=1).first()
        if not machine:
            return jsonify({'success': False, 'message': '机器不存在或已在回收站外'}), 404

        # 如果机器有缩略图文件，尝试删除它
        base_path = os.path.join(current_app.root_path, '..')
        try:
            if machine.image and not machine.image.endswith('sample.png'):
                image_path = os.path.join(base_path, machine.image)
                if os.path.exists(image_path) and os.path.isfile(image_path):
                    os.remove(image_path)
        except Exception as e:
            current_app.logger.warning(f"删除缩略图文件失败: {str(e)}")

        # 从数据库中永久删除机器
        db.session.delete(machine)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '机器已永久删除'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"永久删除机器失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/recycle-bin/batch-permanent-delete', methods=['DELETE'])
@route_permission(ROUTE_MACHINE_MANAGE)
def batch_permanent_delete_machines_from_recycle_bin():
    """批量从回收站永久删除机器"""
    try:
        data = request.get_json()
        if not data or 'ids' not in data:
            return jsonify({'success': False, 'message': '缺少机器ID列表'}), 400

        ids = data['ids']
        if not isinstance(ids, list) or len(ids) == 0:
            return jsonify({'success': False, 'message': '机器ID列表不能为空'}), 400

        # 验证所有ID是否存在且已删除
        machines = MachineNew.query.filter(MachineNew.id.in_(ids), MachineNew.is_deleted == 1).all()

        if len(machines) != len(ids):
            # 检查哪些ID不存在或未被删除
            found_ids = {m.id for m in machines}
            invalid_ids = [id for id in ids if id not in found_ids]
            return jsonify({
                'success': False,
                'message': f'以下机器ID不存在或未在回收站中: {invalid_ids}'
            }), 404

        base_path = os.path.join(current_app.root_path, '..')

        # 删除所有关联的缩略图文件
        for machine in machines:
            try:
                if machine.image and not machine.image.endswith('sample.png'):
                    image_path = os.path.join(base_path, machine.image)
                    if os.path.exists(image_path) and os.path.isfile(image_path):
                        os.remove(image_path)
            except Exception as e:
                current_app.logger.warning(f"删除缩略图文件失败: {str(e)}")

        # 从数据库中批量删除
        for machine in machines:
            db.session.delete(machine)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'成功永久删除了 {len(machines)} 台机器'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量永久删除机器失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/recycle-bin/clear', methods=['DELETE'])
@route_permission(ROUTE_MACHINE_MANAGE)
def clear_recycle_bin():
    """清空整个回收站"""
    try:
        # 获取所有已删除的机器
        deleted_machines = MachineNew.query.filter_by(is_deleted=1).all()

        if not deleted_machines:
            return jsonify({
                'success': True,
                'message': '回收站已经是空的'
            })

        base_path = os.path.join(current_app.root_path, '..')

        # 删除所有关联的缩略图文件
        for machine in deleted_machines:
            try:
                if machine.image and not machine.image.endswith('sample.png'):
                    image_path = os.path.join(base_path, machine.image)
                    if os.path.exists(image_path) and os.path.isfile(image_path):
                        os.remove(image_path)
            except Exception as e:
                current_app.logger.warning(f"删除缩略图文件失败: {str(e)}")

        # 批量删除数据库记录
        for machine in deleted_machines:
            db.session.delete(machine)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'已清空回收站，删除了 {len(deleted_machines)} 台机器'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"清空回收站失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
