"""用户相关的路由"""
from flask import Blueprint, request, jsonify
from app.models.employee import Employee
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_USER_MANAGE
from extensions import db
import hashlib
import config
import jwt
from datetime import datetime, timedelta
from app.models.simple_permission import get_user_role_from_token
import traceback
from app.models.totp_user import TotpUser
import uuid
from sqlalchemy import func
from app.constants.simple_permission_constants import ROUTE_USER_MANAGE

# 创建蓝图
user_bp = Blueprint('user', __name__, url_prefix='/api')

@user_bp.route('/init-admin', methods=['POST'])
@route_permission(ROUTE_USER_MANAGE)
def init_admin():
    """初始化管理员账户"""
    try:
        # 检查是否已存在管理员
        existing_admin = Employee.query.filter_by(user_role='admin').first()
        if existing_admin:
            return jsonify({
                "code": 400,
                "msg": "管理员账户已存在",
                "data": None
            }), 400

        data = request.get_json()
        name = data.get('name', 'admin')
        emp_id = data.get('emp_id', 'admin')
        password = data.get('password', 'admin123')

        # 检查员工ID是否已存在
        existing_employee = Employee.query.filter_by(emp_id=emp_id).first()
        if existing_employee:
            return jsonify({
                "code": 400,
                "msg": "员工ID已存在",
                "data": None
            }), 400

        # 创建管理员账户（临时状态，需要绑定TOTP）
        admin_employee = Employee(
            emp_id=emp_id,
            name=name,
            user_role='admin',
            status='pending_binding',  # 需要绑定TOTP
            dept='管理部',
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        db.session.add(admin_employee)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "管理员账户创建成功，请绑定TOTP验证器",
            "data": {
                "emp_id": admin_employee.emp_id,
                "name": admin_employee.name
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建管理员账户失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/employee', methods=['POST'])
@route_permission(ROUTE_USER_MANAGE)
def create_employee():
    """创建员工"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        required_fields = ['emp_id', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "code": 400,
                    "msg": f"缺少必需字段: {field}",
                    "data": None
                }), 400

        emp_id = data['emp_id']
        name = data['name']
        dept = data.get('dept', '')
        user_role = data.get('user_role', 'user')
        remarks = data.get('remarks', '')

        # 验证角色值 - 从数据库获取所有有效角色
        from app.models.simple_permission import SimpleRole
        valid_roles = [role.name for role in SimpleRole.query.all()]
        if user_role not in valid_roles:
            return jsonify({
                "code": 400,
                "msg": f"无效的角色值: {user_role}，有效值为: {valid_roles}",
                "data": None
            }), 400

        # 检查员工ID是否已存在
        existing_employee = Employee.query.filter_by(emp_id=emp_id).first()
        if existing_employee:
            return jsonify({
                "code": 400,
                "msg": "员工ID已存在",
                "data": None
            }), 400

        # 创建员工记录
        employee = Employee(
            emp_id=emp_id,
            name=name,
            dept=dept,
            inner_ip=request.remote_addr or '127.0.0.1',  # 使用请求IP或默认本地IP
            user_role=user_role,
            status='pending_approval',  # 待审批状态
            remarks=remarks,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        db.session.add(employee)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "员工创建成功",
            "data": employee.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建员工失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/employees', methods=['GET'])
@route_permission(ROUTE_USER_MANAGE)
def get_employees():
    """获取所有员工列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        user_role = request.args.get('user_role', '')
        
        # 构建查询
        query = Employee.query
        if search:
            query = query.filter(
                (Employee.emp_id.contains(search)) | 
                (Employee.name.contains(search)) |
                (Employee.dept.contains(search))
            )
        if status:
            query = query.filter(Employee.status == status)
        if user_role:
            query = query.filter(Employee.user_role == user_role)
        
        # 检查当前用户是否为管理员，如果不是则只返回自己的信息
        current_user_role = get_user_role_from_token()
        if current_user_role != 'admin':
            current_user_emp_id = request.headers.get('emp_id')  # 从token解析的emp_id
            # 如果不是管理员，可能需要特殊处理，此处简化为返回所有可见员工
            # 实际业务中可能需要更复杂的权限控制
        
        # 分页查询
        employees = query.offset((page - 1) * size).limit(size).all()
        total = query.count()
        
        # 获取所有角色列表（用于前端下拉选择）
        from app.models.permission import RolePermission
        role_permissions = RolePermission.query.with_entities(
            RolePermission.role_name, 
            RolePermission.role_description
        ).distinct().all()
        
        # 提取角色信息
        roles = []
        seen_roles = set()  # 避免重复角色
        
        for perm in role_permissions:
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
            "data": {
                "list": [emp.to_dict() for emp in employees],
                "total": total,
                "page": page,
                "size": size,
                "roles": roles  # 添加角色列表供前端使用
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取员工列表失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/employee/<emp_id>', methods=['PUT'])
@route_permission(ROUTE_USER_MANAGE)
def update_employee(emp_id):
    """更新员工信息"""
    try:
        # 检查当前用户权限
        current_user_role = get_user_role_from_token()
        current_user_emp_id = request.headers.get('emp_id')  # 这里应该从token中获取emp_id
        
        # 管理员可以更新任何员工，普通用户只能更新自己的信息
        if current_user_role != 'admin' and current_user_emp_id != emp_id:
            return jsonify({
                "code": 403,
                "msg": "权限不足，只能更新自己的信息",
                "data": None
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return jsonify({
                "code": 404,
                "msg": "员工不存在",
                "data": None
            }), 404

        # 检查是否尝试更改角色（只有管理员可以更改角色）
        if 'user_role' in data and current_user_role != 'admin':
            return jsonify({
                "code": 403,
                "msg": "权限不足，无法更改用户角色",
                "data": None
            }), 403

        # 检查是否尝试更改员工ID
        if 'emp_id' in data and data['emp_id'] != emp_id:
            # 只有管理员可以更改员工ID
            if current_user_role != 'admin':
                return jsonify({
                    "code": 403,
                    "msg": "权限不足，无法更改员工ID",
                    "data": None
                }), 403
            
            # 检查新员工ID是否已存在
            existing_employee = Employee.query.filter_by(emp_id=data['emp_id']).first()
            if existing_employee:
                return jsonify({
                    "code": 400,
                    "msg": "员工ID已存在",
                    "data": None
                }), 400
            
            # 更新员工ID
            employee.emp_id = data['emp_id']
        
        # 更新员工信息
        if 'name' in data:
            employee.name = data['name']
        if 'dept' in data:
            employee.dept = data['dept']
        if 'user_role' in data:
            # 从数据库获取所有有效角色
            from app.models.simple_permission import SimpleRole
            valid_roles = [role.name for role in SimpleRole.query.all()]
            if data['user_role'] in valid_roles:
                employee.user_role = data['user_role']
            else:
                return jsonify({
                    "code": 400,
                    "msg": f"无效的角色值: {data['user_role']}，有效值为: {valid_roles}",
                    "data": None
                }), 400
        if 'status' in data:
            employee.status = data['status']
        if 'remarks' in data:
            employee.remarks = data['remarks']
        
        employee.update_time = datetime.now()
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "员工信息更新成功",
            "data": employee.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新员工信息失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/employee/<emp_id>', methods=['DELETE'])
@route_permission(ROUTE_USER_MANAGE)
def delete_employee(emp_id):
    """删除员工"""
    try:
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return jsonify({
                "code": 404,
                "msg": "员工不存在",
                "data": None
            }), 404

        # 检查是否为管理员（不能删除管理员自己）
        current_user_emp_id = get_user_role_from_token()  # 这里应该获取当前用户ID
        if employee.user_role == 'admin':
            admin_count = Employee.query.filter_by(user_role='admin').count()
            if admin_count <= 1:
                return jsonify({
                    "code": 400,
                    "msg": "不能删除最后一个管理员账户",
                    "data": None
                }), 400

        db.session.delete(employee)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "员工删除成功",
            "data": None
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除员工失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/totp-qr', methods=['POST'])
@route_permission(ROUTE_USER_MANAGE)
def generate_totp_qr():
    """生成TOTP二维码"""
    try:
        data = request.get_json()
        emp_id = data.get('emp_id')

        if not emp_id:
            return jsonify({
                "code": 400,
                "msg": "员工ID不能为空",
                "data": None
            }), 400

        # 检查员工是否存在且状态为待绑定
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return jsonify({
                "code": 404,
                "msg": "员工不存在",
                "data": None
            }), 404

        # 检查员工状态
        if employee.status != 'pending_binding':
            return jsonify({
                "code": 400,
                "msg": f"员工当前状态为{employee.status}，无法生成TOTP二维码",
                "data": None
            }), 400

        # 生成TOTP密钥
        import pyotp
        secret = pyotp.random_base32()
        
        # 生成TOTP URI
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=emp_id,
            issuer_name="Soonwin OA System"
        )

        # 保存到临时表（或更新员工表存储密钥）
        # 这里可以创建一个临时的TOTP存储记录
        totp_user = TotpUser(
            emp_id=emp_id,
            totp_secret=secret,
            create_time=datetime.now()
        )
        
        # 检查是否已存在，如果存在则更新
        existing_totp = TotpUser.query.filter_by(emp_id=emp_id).first()
        if existing_totp:
            existing_totp.totp_secret = secret
            existing_totp.create_time = datetime.now()
        else:
            db.session.add(totp_user)

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "TOTP二维码生成成功",
            "data": {
                "totp_uri": totp_uri,
                "name": employee.name,
                "emp_id": employee.emp_id
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"生成TOTP二维码失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/totp/login', methods=['POST'])
def totp_login():
    """TOTP登录"""
    try:
        data = request.get_json()
        emp_id = data.get('emp_id')
        totp_code = data.get('totp_code')

        if not emp_id or not totp_code:
            return jsonify({
                "code": 400,
                "msg": "员工ID和TOTP验证码不能为空",
                "data": None
            }), 400

        # 检查员工是否存在
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return jsonify({
                "code": 404,
                "msg": "员工不存在或信息错误",
                "data": None
            }), 404

        # 检查员工状态
        if employee.status != 'active':
            return jsonify({
                "code": 400,
                "msg": "员工账户未激活，请联系管理员",
                "data": None
            }), 400

        # 获取TOTP密钥
        totp_user = TotpUser.query.filter_by(emp_id=emp_id).first()
        if not totp_user:
            return jsonify({
                "code": 404,
                "msg": "TOTP验证器未绑定",
                "data": None
            }), 404

        # 验证TOTP码
        import pyotp
        totp = pyotp.TOTP(totp_user.totp_secret)
        if not totp.verify(totp_code, valid_window=1):  # 允许前后1个时间窗口的容错
            return jsonify({
                "code": 401,
                "msg": "TOTP验证码错误",
                "data": None
            }), 401

        # 生成JWT token
        payload = {
            'emp_id': employee.emp_id,
            'user_role': employee.user_role,
            'name': employee.name,
            'exp': datetime.utcnow() + timedelta(days=30)  # 30天有效期
        }
        token = jwt.encode(payload, config.Config.JWT_SECRET_KEY, algorithm='HS256')

        # 更新最后登录时间
        employee.last_login_time = datetime.now()
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "登录成功",
            "data": {
                "token": token,
                "emp_id": employee.emp_id,
                "name": employee.name,
                "user_role": employee.user_role
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"登录失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/verify-totp', methods=['POST'])
@route_permission(ROUTE_USER_MANAGE)
def verify_totp():
    """验证TOTP码（用于绑定验证器）"""
    try:
        data = request.get_json()
        emp_id = data.get('emp_id')
        totp_code = data.get('totp_code')

        if not emp_id or not totp_code:
            return jsonify({
                "code": 400,
                "msg": "员工ID和TOTP验证码不能为空",
                "data": None
            }), 400

        # 检查是否是当前用户
        current_user_role = get_user_role_from_token()
        # 这里应该有机制验证是当前用户，简化处理

        # 获取TOTP密钥
        totp_user = TotpUser.query.filter_by(emp_id=emp_id).first()
        if not totp_user:
            return jsonify({
                "code": 404,
                "msg": "TOTP验证器配置不存在",
                "data": None
            }), 404

        # 验证TOTP码
        import pyotp
        totp = pyotp.TOTP(totp_user.totp_secret)
        if totp.verify(totp_code, valid_window=1):
            return jsonify({
                "code": 200,
                "msg": "TOTP验证成功",
                "data": None
            })
        else:
            return jsonify({
                "code": 401,
                "msg": "TOTP验证码错误",
                "data": None
            }), 401

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"TOTP验证失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/user/permissions', methods=['GET'])
@route_permission(ROUTE_USER_MANAGE)
def get_user_permissions():
    """获取当前用户的权限列表"""
    try:
        # 获取当前用户角色
        user_role = get_user_role_from_token()
        if not user_role:
            return jsonify({
                "code": 401,
                "msg": "认证失败",
                "data": None
            }), 401
        
        # 使用新的简化权限模型获取权限
        from app.models.simple_permission import SimpleRolePermission, SimpleRole
        
        # 获取当前用户角色对应的路由权限
        role = SimpleRole.query.filter_by(name=user_role).first()
        if not role:
            return jsonify({
                "code": 200,
                "msg": "success",
                "data": []
            })
        
        # 直接获取该角色的所有路由权限
        permissions = []
        for rp in role.permissions:
            permissions.append({
                "id": rp.id,
                "role_name": user_role,
                "route_name": rp.route_name,
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 使用当前时间，因为SimpleRolePermission没有时间字段
                "update_time": None
            })
        
        return jsonify({
            "code": 200,
            "msg": "success",
            "data": permissions
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取用户权限失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/user/permission/roles', methods=['GET'])
@route_permission(ROUTE_USER_MANAGE)
def get_all_roles():
    """获取所有角色列表"""
    try:
        from app.models.simple_permission import SimpleRole
        
        roles = SimpleRole.query.all()
        role_list = []
        
        for role in roles:
            # 计算该角色的权限数量
            permission_count = len(role.permissions)
            role_list.append({
                "role_name": role.name,
                "role_description": role.remark,
                "permissions_count": permission_count
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


@user_bp.route('/user/permission/all-routes', methods=['GET'])
@route_permission(ROUTE_USER_MANAGE)
def get_all_routes():
    """获取所有可用的路由权限列表"""
    try:
        from app.constants.simple_permission_constants import ALL_ROUTES
        
        # 将权限常量转换为前端可用的格式
        routes = []
        route_descriptions = {
            'display_file_manage': '文件展示',
            'photo_manage': '照片管理',
            'punch_manage': '打卡',
            'upload_manage': '文件上传模块',
            'video_manage': '视频管理',
            'inquiry_manage': '询盘管理',
            'order_manage': '订单管理',
            'order_status_manage': '订单状态',
            'expense_manage': '费用管理',
            'log_manage': '日志管理',
            'machine_manage': '设备管理',
            'user_manage': '员工管理',
            'permission_manage': '权限管理'
        }
        
        for route_name in ALL_ROUTES:
            routes.append({
                "route_name": route_name,
                "route_label": route_descriptions.get(route_name, route_name),
                "is_active": True  # 假设所有路由都是可用的
            })
        
        return jsonify({
            "code": 200,
            "msg": "success",
            "data": routes
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取路由列表失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/user/permission/role-permissions', methods=['GET'])
@route_permission(ROUTE_USER_MANAGE)
def get_role_permissions():
    """获取指定角色的权限列表"""
    try:
        role_name = request.args.get('role_name')
        if not role_name:
            return jsonify({
                "code": 400,
                "msg": "缺少角色名称参数",
                "data": None
            }), 400
        
        from app.models.simple_permission import SimpleRole
        
        role = SimpleRole.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({
                "code": 404,
                "msg": "角色不存在",
                "data": []
            })
        
        permissions = [rp.route_name for rp in role.permissions]
        
        return jsonify({
            "code": 200,
            "msg": "success",
            "data": permissions
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取角色权限失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/user/permission/update-role-permissions', methods=['POST'])
@route_permission(ROUTE_USER_MANAGE)
def update_role_permissions():
    """更新角色的权限列表"""
    try:
        data = request.get_json()
        role_name = data.get('role_name')
        permissions = data.get('permissions', [])
        
        if not role_name:
            return jsonify({
                "code": 400,
                "msg": "缺少角色名称参数",
                "data": None
            }), 400
        
        from app.models.simple_permission import SimpleRole, SimpleRolePermission
        from app.constants.simple_permission_constants import ALL_ROUTES
        
        # 验证权限名称是否有效
        valid_routes = set(ALL_ROUTES)
        for perm in permissions:
            if perm not in valid_routes:
                return jsonify({
                    "code": 400,
                    "msg": f"无效的权限名称: {perm}",
                    "data": None
                }), 400
        
        # 获取角色
        role = SimpleRole.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({
                "code": 404,
                "msg": "角色不存在",
                "data": None
            }), 404
        
        # 删除现有权限
        for perm in role.permissions:
            db.session.delete(perm)
        
        # 添加新权限
        for route_name in permissions:
            new_permission = SimpleRolePermission(
                role_id=role.id,
                route_name=route_name
            )
            db.session.add(new_permission)
        
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": "权限更新成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新角色权限失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/user/permission/update-role-description', methods=['POST'])
@route_permission(ROUTE_USER_MANAGE)
def update_role_description():
    """更新角色描述"""
    try:
        data = request.get_json()
        role_name = data.get('role_name')
        role_description = data.get('role_description')
        
        if not role_name:
            return jsonify({
                "code": 400,
                "msg": "缺少角色名称参数",
                "data": None
            }), 400
        
        from app.models.simple_permission import SimpleRole
        
        # 检查角色是否存在，如果不存在则创建
        role = SimpleRole.query.filter_by(name=role_name).first()
        if not role:
            # 创建新角色
            role = SimpleRole(name=role_name, remark=role_description)
            db.session.add(role)
        else:
            # 更新角色描述
            role.remark = role_description
        
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": "角色描述更新成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新角色描述失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/user/permission/delete-role', methods=['POST'])
@route_permission(ROUTE_USER_MANAGE)
def delete_role():
    """删除角色"""
    try:
        data = request.get_json()
        role_name = data.get('role_name')
        
        if not role_name:
            return jsonify({
                "code": 400,
                "msg": "缺少角色名称参数",
                "data": None
            }), 400
        
        # 检查是否为内置角色，禁止删除
        builtin_roles = ['admin', 'sales', 'design', 'user']
        if role_name in builtin_roles:
            return jsonify({
                "code": 400,
                "msg": f"内置角色 {role_name} 不能删除",
                "data": None
            }), 400
        
        from app.models.simple_permission import SimpleRole
        from app.models.employee import Employee
        
        # 检查该角色下是否有用户
        user_count = Employee.query.filter_by(user_role=role_name).count()
        if user_count > 0:
            return jsonify({
                "code": 400,
                "msg": f"角色 {role_name} 下有 {user_count} 个用户，不能删除",
                "data": None
            }), 400
        
        # 查找角色
        role = SimpleRole.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({
                "code": 404,
                "msg": "角色不存在",
                "data": None
            }), 404
        
        # 删除角色及其所有权限
        db.session.delete(role)
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": "角色删除成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除角色失败: {str(e)}",
            "data": None
        }), 500