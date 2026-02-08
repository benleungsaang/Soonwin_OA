"""权限管理相关路由"""
from flask import Blueprint, request, jsonify
from app.utils.auth_utils import require_admin, require_auth, require_module_permission, is_admin_user
from app.models.permission import RolePermission
from app.constants.permission_constants import MODULE_PERMISSION_MANAGE, ALL_MODULES
from extensions import db
import uuid

permission_bp = Blueprint('permission', __name__, url_prefix="/api/permission")

@permission_bp.route('/list', methods=['GET'])
@require_module_permission(MODULE_PERMISSION_MANAGE, 'view')
def get_permissions():
    """获取权限配置 - 如果指定角色，则返回该角色的所有权限（包括未设置的模块），否则返回所有已存在的权限"""
    try:
        # 获取查询参数
        role_name = request.args.get('role_name')
        module_name = request.args.get('module_name')
        
        # 如果指定了角色名，返回该角色的所有可能模块（包括未设置的）
        if role_name:
            # 获取该角色的所有现有权限
            existing_permissions = RolePermission.query.filter_by(role_name=role_name).all()
            existing_perms_dict = {perm.module_name: perm for perm in existing_permissions}
            
            # 为所有可能的模块创建权限对象
            all_module_permissions = []
            for module in ALL_MODULES:
                if module in existing_perms_dict:
                    # 如果该模块已有权限配置，使用现有配置
                    perm = existing_perms_dict[module]
                    all_module_permissions.append({
                        "id": perm.id,
                        "role_name": perm.role_name,
                        "role_description": perm.role_description,
                        "module_name": perm.module_name,
                        "can_view": perm.can_view,
                        "can_edit": perm.can_edit,
                        "can_delete": perm.can_delete,
                        "create_time": perm.create_time.isoformat() if perm.create_time else None,
                        "update_time": perm.update_time.isoformat() if perm.update_time else None
                    })
                else:
                    # 如果该模块没有权限配置，创建默认的未设置权限对象
                    all_module_permissions.append({
                        "id": "",
                        "role_name": role_name,
                        "role_description": "",
                        "module_name": module,
                        "can_view": False,
                        "can_edit": False,
                        "can_delete": False,
                        "create_time": None,
                        "update_time": None
                    })
            
            return jsonify({
                "code": 200,
                "msg": "success",
                "data": all_module_permissions
            })
        
        # 否则按原逻辑返回所有已存在的权限
        query = RolePermission.query
        if module_name:
            query = query.filter_by(module_name=module_name)
        
        permissions = query.all()

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": [perm.to_dict() for perm in permissions]
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取权限列表失败: {str(e)}",
            "data": None
        }), 500


@permission_bp.route('/all-modules', methods=['GET'])
@require_module_permission(MODULE_PERMISSION_MANAGE, 'view')
def get_all_modules():
    """获取所有可能的权限模块列表"""
    try:
        return jsonify({
            "code": 200,
            "msg": "success",
            "data": {
                "all_modules": ALL_MODULES
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取所有模块列表失败: {str(e)}",
            "data": None
        }), 500


@permission_bp.route('/roles', methods=['GET'])
@require_module_permission(MODULE_PERMISSION_MANAGE, 'view')
def get_roles():
    """获取所有角色列表，只返回不重复的role_name和对应的role_description"""
    try:
        # 获取所有权限记录中的不重复角色名和描述
        permissions = RolePermission.query.with_entities(
            RolePermission.role_name, 
            RolePermission.role_description
        ).distinct().all()
        
        # 提取角色信息
        roles = []
        seen_roles = set()  # 避免重复角色
        
        for perm in permissions:
            role_name = perm.role_name
            role_description = perm.role_description or f"{role_name}角色"
            
            if role_name not in seen_roles:
                roles.append({
                    "role_name": role_name,
                    "role_description": role_description
                })
                seen_roles.add(role_name)
        
        # 添加内置角色（如果不存在）
        builtin_roles = ['admin', 'sales', 'user']
        for builtin_role in builtin_roles:
            if builtin_role not in seen_roles:
                roles.append({
                    "role_name": builtin_role,
                    "role_description": f"{'系统管理员' if builtin_role == 'admin' else '业务员' if builtin_role == 'sales' else '普通用户'}"
                })
                seen_roles.add(builtin_role)
        
        return jsonify({
            "code": 200,
            "msg": "success",
            "data": roles
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取角色列表失败: {str(e)}",
            "data": None
        }), 500


@permission_bp.route('/update', methods=['POST'])
@require_module_permission(MODULE_PERMISSION_MANAGE, 'edit')
def update_permission():
    """更新权限配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        role_name = data.get('role_name')
        module_name = data.get('module_name')
        can_view = data.get('can_view', True)
        can_edit = data.get('can_edit', False)
        can_delete = data.get('can_delete', False)
        role_description = data.get('role_description', None)

        if not role_name or not module_name:
            return jsonify({
                "code": 400,
                "msg": "角色名称和模块名称不能为空",
                "data": None
            }), 400

        # 查找现有权限记录
        permission = RolePermission.query.filter_by(
            role_name=role_name,
            module_name=module_name
        ).first()

        if permission:
            # 更新现有权限
            permission.can_view = can_view
            permission.can_edit = can_edit
            permission.can_delete = can_delete
            if role_description is not None:
                permission.role_description = role_description
        else:
            # 创建新权限记录
            permission = RolePermission(
                id=str(uuid.uuid4()),
                role_name=role_name,
                role_description=role_description,
                module_name=module_name,
                can_view=can_view,
                can_edit=can_edit,
                can_delete=can_delete
            )
            db.session.add(permission)

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "权限更新成功",
            "data": permission.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新权限失败: {str(e)}",
            "data": None
        }), 500


@permission_bp.route('/create-role', methods=['POST'])
@require_module_permission(MODULE_PERMISSION_MANAGE, 'edit')
def create_role():
    """创建新角色并设置默认权限"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        role_name = data.get('role_name')
        role_description = data.get('role_description')

        if not role_name or not role_description:
            return jsonify({
                "code": 400,
                "msg": "角色名称和角色描述不能为空",
                "data": None
            }), 400

        # 检查角色是否已存在
        existing_permission = RolePermission.query.filter_by(role_name=role_name).first()
        if existing_permission:
            return jsonify({
                "code": 400,
                "msg": "角色已存在",
                "data": None
            }), 400

        # 为新角色设置默认权限：照片管理、视频管理、订单状态管理、打卡、展示文件的查看权限
        default_modules = [
            'photo_manage', 'video_manage', 'order_status_manage',
            'punch_manage', 'display_file_manage'
        ]

        for module_name in default_modules:
            permission = RolePermission(
                id=str(uuid.uuid4()),
                role_name=role_name,
                role_description=role_description,
                module_name=module_name,
                can_view=True,
                can_edit=False,
                can_delete=False
            )
            db.session.add(permission)

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "角色创建成功",
            "data": {
                "role_name": role_name,
                "role_description": role_description
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建角色失败: {str(e)}",
            "data": None
        }), 500


@permission_bp.route('/update-role-description', methods=['POST'])
@require_module_permission(MODULE_PERMISSION_MANAGE, 'edit')
def update_role_description():
    """更新角色描述"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        role_name = data.get('role_name')
        role_description = data.get('role_description')

        if not role_name:
            return jsonify({
                "code": 400,
                "msg": "角色名称不能为空",
                "data": None
            }), 400

        if not role_description:
            return jsonify({
                "code": 400,
                "msg": "角色描述不能为空",
                "data": None
            }), 400

        # 更新该角色所有权限记录的描述
        permissions = RolePermission.query.filter_by(role_name=role_name).all()
        if not permissions:
            return jsonify({
                "code": 404,
                "msg": "角色不存在",
                "data": None
            }), 404

        for perm in permissions:
            perm.role_description = role_description

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "角色描述更新成功",
            "data": {
                "role_name": role_name,
                "role_description": role_description
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新角色描述失败: {str(e)}",
            "data": None
        }), 500


@permission_bp.route('/<permission_id>', methods=['DELETE'])
@require_module_permission(MODULE_PERMISSION_MANAGE, 'delete')
def delete_permission(permission_id):
    """删除权限配置"""
    try:
        permission = RolePermission.query.filter_by(id=permission_id).first()
        if not permission:
            return jsonify({
                "code": 404,
                "msg": "权限记录不存在",
                "data": None
            }), 404

        db.session.delete(permission)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "权限删除成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除权限失败: {str(e)}",
            "data": None
        }), 500