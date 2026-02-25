"""权限管理相关路由"""
from flask import Blueprint, request, jsonify
from app.utils.auth_utils import require_admin, require_auth, require_module_permission, is_admin_user
from app.models.simple_permission import SimpleRole, SimpleRolePermission
from app.constants.simple_permission_constants import ALL_ROUTES
from extensions import db
import uuid

permission_bp = Blueprint('permission', __name__, url_prefix="/api/permission")

@permission_bp.route('/list', methods=['GET'])
@require_module_permission("permission_manage", 'view')
def get_permissions():
    """获取权限配置 - 如果指定角色，则返回该角色的所有权限（包括未设置的路由），否则返回所有已存在的权限"""
    try:
        # 获取查询参数
        role_name = request.args.get('role_name')
        route_name = request.args.get('route_name')
        
        # 如果指定了角色名，返回该角色的所有可能路由（包括未设置的）
        if role_name:
            # 获取该角色的所有现有权限
            existing_permissions = SimpleRolePermission.query.join(SimpleRole).filter(SimpleRole.name == role_name).all()
            existing_perms_dict = {perm.route_name: perm for perm in existing_permissions}
            
            # 为所有可能的路由创建权限对象
            all_route_permissions = []
            for route in ALL_ROUTES:
                if route in existing_perms_dict:
                    # 如果该路由已有权限配置，使用现有配置
                    perm = existing_perms_dict[route]
                    all_route_permissions.append({
                        "id": perm.id,
                        "role_id": perm.role_id,
                        "route_name": perm.route_name
                    })
                else:
                    # 如果该路由没有权限配置，创建默认的未设置权限对象
                    all_route_permissions.append({
                        "id": None,
                        "role_id": None,
                        "route_name": route
                    })
            
            return jsonify({
                "code": 200,
                "msg": "success",
                "data": all_route_permissions
            })
        
        # 否则返回所有已存在的权限
        query = SimpleRolePermission.query
        if route_name:
            query = query.filter_by(route_name=route_name)
        query = query.join(SimpleRole)
        
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
@require_module_permission("permission_manage", 'view')
def get_all_modules():
    """获取所有可能的权限模块列表（改为获取所有路由）"""
    try:
        return jsonify({
            "code": 200,
            "msg": "success",
            "data": {
                "all_routes": ALL_ROUTES  # 改为返回所有路由
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取所有路由列表失败: {str(e)}",
            "data": None
        }), 500


@permission_bp.route('/roles', methods=['GET'])
@require_module_permission("permission_manage", 'view')
def get_roles():
    """获取所有角色列表"""
    try:
        # 获取所有角色
        roles = SimpleRole.query.all()
        
        # 提取角色信息
        role_list = []
        for role in roles:
            role_list.append({
                "role_name": role.name,
                "role_description": role.remark
            })

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": role_list
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取角色列表失败: {str(e)}",
            "data": None
        }), 500


@permission_bp.route('/update', methods=['POST'])
@require_module_permission("permission_manage", 'edit')
def update_permission():
    """更新权限配置（为角色分配路由权限）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        role_name = data.get('role_name')
        route_name = data.get('route_name')

        if not role_name or not route_name:
            return jsonify({
                "code": 400,
                "msg": "角色名称和路由名称不能为空",
                "data": None
            }), 400

        # 验证角色和路由是否存在
        role = SimpleRole.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({
                "code": 400,
                "msg": "角色不存在",
                "data": None
            }), 400

        if route_name not in ALL_ROUTES:
            return jsonify({
                "code": 400,
                "msg": "路由名称不存在",
                "data": None
            }), 400

        # 查找现有权限记录
        permission = SimpleRolePermission.query.filter_by(
            role_id=role.id,
            route_name=route_name
        ).first()

        if permission:
            # 如果权限存在，删除它（切换权限状态）
            db.session.delete(permission)
            db.session.commit()
            action = "权限已移除"
        else:
            # 创建新的权限记录
            permission = SimpleRolePermission(
                role_id=role.id,
                route_name=route_name
            )
            db.session.add(permission)
            db.session.commit()
            action = "权限已添加"

        return jsonify({
            "code": 200,
            "msg": action,
            "data": {
                "role_name": role_name,
                "route_name": route_name,
                "action": action
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新权限失败: {str(e)}",
            "data": None
        }), 500


@permission_bp.route('/create-role', methods=['POST'])
@require_module_permission("permission_manage", 'edit')
def create_role():
    """创建新角色"""
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

        # 检查角色是否已存在
        existing_role = SimpleRole.query.filter_by(name=role_name).first()
        if existing_role:
            return jsonify({
                "code": 400,
                "msg": "角色已存在",
                "data": None
            }), 400

        # 创建新角色
        role = SimpleRole(name=role_name, remark=role_description or f"{role_name}角色")
        db.session.add(role)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "角色创建成功",
            "data": {
                "role_name": role_name,
                "role_description": role.remark
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
@require_module_permission("permission_manage", 'edit')
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

        # 更新角色描述
        role = SimpleRole.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({
                "code": 404,
                "msg": "角色不存在",
                "data": None
            }), 404

        role.remark = role_description
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "角色描述更新成功",
            "data": {
                "role_name": role_name,
                "role_description": role.remark
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
@require_module_permission("permission_manage", 'delete')
def delete_permission(permission_id):
    """删除角色（简化版权限模型中删除角色及关联权限）"""
    try:
        # 将permission_id视为角色名称
        role_name = permission_id
        
        # 获取角色
        role = SimpleRole.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({
                "code": 404,
                "msg": "角色不存在",
                "data": None
            }), 404

        # 删除该角色的所有权限关联
        SimpleRolePermission.query.filter_by(role_id=role.id).delete()
        # 删除角色本身
        db.session.delete(role)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "角色及关联权限删除成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除角色失败: {str(e)}",
            "data": None
        }), 500