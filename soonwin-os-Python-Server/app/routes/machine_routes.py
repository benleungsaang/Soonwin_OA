from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
import os
import json
import uuid
from PIL import Image
from .. import db
from ..models.machine_new import MachineNew
from ..utils.json_utils import import_json_data, export_json_data
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_MACHINE_MANAGE, ROUTE_UPLOAD_MANAGE
from app.models.simple_permission import get_user_role_from_token
from app.models.employee import Employee  # 导入Employee模型
from app.utils.auth_utils import get_user_id_from_token  # 从auth_utils导入get_user_id_from_token函数
from ..utils.upload_utils import process_image_with_variants

machine_bp = Blueprint('machine_bp', __name__, url_prefix='/api')


def process_machine_image(file_path, base_save_dir):
    """
    从文件路径处理机器图片，生成300x300的缩略图
    :param file_path: 文件路径
    :param base_save_dir: 基础存储目录
    :return: 缩略图路径
    """
    # 获取文件信息
    ext = os.path.splitext(file_path)[1].lower()[1:]  # 去掉点号
    file_prefix = os.path.splitext(os.path.basename(file_path))[0]

    # 打开原图并获取基础信息
    img = Image.open(file_path)
    original_width, original_height = img.size
    print(f'Processing machine image: {original_width}x{original_height}')

    # 生成300x300缩略图
    # 保持宽高比，最大尺寸限制为300x300
    max_size = 300
    scale = min(max_size / original_width, max_size / original_height)
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)

    # 调整图片大小
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 生成缩略图路径
    thumb_file_path = os.path.join(os.path.dirname(file_path), f"{file_prefix}_thumb.{ext}")
    resized_img.save(thumb_file_path, quality=60)

    # 返回相对于基础目录的路径
    relative_path = os.path.relpath(thumb_file_path, base_save_dir).replace('\\', '/')
    print(f'Generated thumbnail: {relative_path}')

    return relative_path


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

        # 获取当前用户的emp_id
        creator_id = get_user_id_from_token()

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

        # 获取图片路径
        image_path = data.get('image')

        # 创建机器对象
        machine = MachineNew(
            model=data.get('model'),
            original_model=data.get('original_model'),
            machine_weight=data.get('machine_weight'),
            dimensions=data.get('dimensions'),
            general_power=data.get('general_power'),
            power_supply=data.get('power_supply'),
            image=image_path,  # 使用处理后的图片路径
            added_count=added_count,
            show_price=show_price,
            original_price=original_price,
            machine_type=machine_type,
            remark=data.get('remark'),
            brand=data.get('brand'),
            custom_attrs=custom_attrs,
            creator=creator_id  # 添加创建者信息
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
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        data = request.get_json()

        # 从数据中移除自动生成的字段，避免更新时间相关的字段
        update_data = {k: v for k, v in data.items()
                       if k not in ['create_time', 'update_time', 'search_key']}

        # 使用新的update_machine方法处理更新逻辑
        success, message, updated_machine = MachineNew.update_machine(id, update_data, db.session)

        if success:
            # 根据用户权限决定是否包含价格字段
            include_price = is_admin
            machine_dict = updated_machine.to_dict(include_price=include_price)

            return jsonify({
                'success': True,
                'message': message,
                'data': machine_dict
            })
        else:
            return jsonify({'success': False, 'message': message}), 500
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

        # 获取当前用户的emp_id
        creator_id = get_user_id_from_token()

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

        # 使用通用JSON工具导入数据，并传递创建者ID
        result = import_json_data('machine_new', data, creator_id=creator_id)

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

        # 保存新文件（原始图片）
        file_path = os.path.join(machine_thumb_dir, unique_filename)
        file.save(file_path)

        # 生成缩略图
        thumb_path = process_machine_image(file_path, os.path.join(base_path, 'assets', 'Media'))

        # 如果原图路径不是默认图片，尝试删除原图和原缩略图
        if machine.image and not machine.image.endswith('sample.png'):
            try:
                old_file_path = os.path.join(base_path, machine.image)
                if os.path.exists(old_file_path) and os.path.isfile(old_file_path):
                    os.remove(old_file_path)

                # 尝试删除对应的缩略图文件（如果存在）
                old_thumb_path = old_file_path.rsplit('.', 1)[0] + '_thumb.' + old_file_path.rsplit('.', 1)[1]
                if os.path.exists(old_thumb_path) and os.path.isfile(old_thumb_path):
                    os.remove(old_thumb_path)
            except Exception as e:
                current_app.logger.warning(f"删除原缩略图失败: {str(e)}")

        # 更新机器的图片路径为原始图片路径（不是缩略图路径）
        machine.image = os.path.relpath(file_path, base_path).replace('\\', '/')
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
                'new_thumb_path': thumb_path,  # 返回缩略图路径供前端使用
                'original_path': os.path.relpath(file_path, base_path).replace('\\', '/')  # 返回原始图片路径
            }
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"上传缩略图失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@machine_bp.route('/machines_new/upload-thumb', methods=['POST'])
@route_permission(ROUTE_UPLOAD_MANAGE)
def upload_machine_thumb_generic():
    """通用上传缩略图接口，用于新增设备时上传缩略图"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

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

        # 生成唯一文件名 - 使用UUID确保唯一性
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"machine_{uuid.uuid4().hex[:8]}.{file_ext}"

        # 保存新文件
        file_path = os.path.join(machine_thumb_dir, unique_filename)
        file.save(file_path)

        # 生成缩略图
        thumb_path = process_machine_image(file_path, os.path.join(base_path, 'assets', 'Media'))

        return jsonify({
            'success': True,
            'message': '缩略图上传成功',
            'data': {
                'thumb_path': thumb_path,
                'original_path': os.path.relpath(file_path, base_path).replace('\\', '/')
            }
        })
    except Exception as e:
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


@machine_bp.route('/machines_new/clear-all', methods=['DELETE'])
@route_permission(ROUTE_MACHINE_MANAGE)
def clear_all_machines():
    """清空所有机器数据（包括正常和已删除的）"""
    try:
        # 获取所有机器（包括已删除的）
        all_machines = MachineNew.query.all()

        if not all_machines:
            return jsonify({
                'success': True,
                'message': '没有数据需要清空'
            })

        base_path = os.path.join(current_app.root_path, '..')

        # 删除所有关联的缩略图文件
        for machine in all_machines:
            try:
                if machine.image and not machine.image.endswith('sample.png'):
                    image_path = os.path.join(base_path, machine.image)
                    if os.path.exists(image_path) and os.path.isfile(image_path):
                        os.remove(image_path)
            except Exception as e:
                current_app.logger.warning(f"删除缩略图文件失败: {str(e)}")

        # 清空数据库表
        for machine in all_machines:
            db.session.delete(machine)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'已清空所有数据，删除了 {len(all_machines)} 台设备'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"清空所有数据失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
