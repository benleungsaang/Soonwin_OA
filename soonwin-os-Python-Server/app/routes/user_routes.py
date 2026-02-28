"""用户相关的路由"""
from flask import Blueprint, request, jsonify
from app.models.employee import Employee
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_USER_MANAGE
from extensions import db
import hashlib
import config
import jwt
import pyotp
from datetime import datetime, timedelta
from app.models.simple_permission import get_user_role_from_token
import traceback
from app.models.totp_user import TotpUser
import uuid
from sqlalchemy import func

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
        user_role = data.get('user_role', 'sales')
        remarks = data.get('remarks', '')

        # 检查员工ID是否已存在
        existing_employee = Employee.query.filter_by(emp_id=emp_id).first()
        if existing_employee:
            return jsonify({
                "code": 400,
                "msg": "员工ID已存在",
                "data": None
            }), 400

        # 验证角色的有效性
        from app.models.simple_permission import SimpleRole
        valid_roles = [role.name for role in SimpleRole.query.all()]
        # 添加内置角色
        builtin_roles = ['admin', 'sales', 'order', 'design']
        all_valid_roles = list(set(valid_roles + builtin_roles))

        if user_role not in all_valid_roles:
            return jsonify({
                "code": 400,
                "msg": f"无效的角色类型，可选角色: {all_valid_roles}",
                "data": None
            }), 400

        # 创建员工记录
        # 为 inner_ip 设置默认值，可以从请求中获取客户端IP，如果没有则使用默认值
        inner_ip = request.remote_addr if request.remote_addr else '127.0.0.1'

        new_employee = Employee(
            emp_id=emp_id,
            name=name,
            dept=dept,
            inner_ip=inner_ip,  # 添加 inner_ip 字段
            user_role=user_role,
            remarks=remarks,
            status='pending_binding',  # 默认状态改为待绑定
            create_time=datetime.now(),
            update_time=datetime.now()
        )

        db.session.add(new_employee)
        db.session.commit()

        # 获取所有角色列表（供前端参考）
        roles = []
        simple_roles = SimpleRole.query.all()
        for role in simple_roles:
            roles.append({
                "role_name": role.name,
                "role_description": role.remark
            })

        # 添加内置角色（如果不存在）
        seen_roles = {role.name for role in simple_roles}
        for builtin_role in builtin_roles:
            if builtin_role not in seen_roles:
                role_desc = {
                    'admin': '系统管理员',
                    'sales': '业务专员',
                    'design': '设计专员',
                    'order': '跟单专员'
                }.get(builtin_role, '普通用户')
                roles.append({
                    "role_name": builtin_role,
                    "role_description": role_desc
                })

        return jsonify({
            "code": 200,
            "msg": "员工创建成功",
            "data": {
                "employee": new_employee.to_dict() if hasattr(new_employee, 'to_dict') else {
                    'emp_id': new_employee.emp_id,
                    'name': new_employee.name,
                    'dept': new_employee.dept,
                    'user_role': new_employee.user_role
                },
                "roles": roles
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建员工失败: {str(e)}",
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

        # 更新员工基本信息
        if 'name' in data:
            employee.name = data['name']
        if 'dept' in data:
            employee.dept = data['dept']

        # 更新员工角色（需要验证角色有效性）
        if 'user_role' in data:
            # 验证角色的有效性
            from app.models.simple_permission import SimpleRole
            valid_roles = [role.name for role in SimpleRole.query.all()]
            builtin_roles = ['admin', 'sales', 'order', 'design']
            all_valid_roles = list(set(valid_roles + builtin_roles))

            new_role = data['user_role']
            if new_role not in all_valid_roles:
                return jsonify({
                    "code": 400,
                    "msg": f"无效的角色类型，可选角色: {all_valid_roles}",
                    "data": None
                }), 400

            employee.user_role = new_role

        # 更新员工状态
        if 'status' in data:
            # 验证状态值的有效性
            valid_statuses = ['pending_binding', 'pending_approval', 'active', 'inactive']
            new_status = data['status']
            if new_status not in valid_statuses:
                return jsonify({
                    "code": 400,
                    "msg": f"无效的状态值，可选状态: {valid_statuses}",
                    "data": None
                }), 400
            employee.status = new_status

        # 更新备注信息
        if 'remarks' in data:
            employee.remarks = data['remarks']

        # 更新最后修改时间
        employee.update_time = datetime.now()

        # 提交数据库修改
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "员工信息更新成功",
            "data": {
                "employee": employee.to_dict() if hasattr(employee, 'to_dict') else {
                    'emp_id': employee.emp_id,
                    'name': employee.name,
                    'dept': employee.dept,
                    'user_role': employee.user_role,
                    'remarks': employee.remarks
                }
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新员工信息失败: {str(e)}",
            "data": None
        }), 500

@user_bp.route('/employees', methods=['GET'])
@route_permission(ROUTE_USER_MANAGE)
def get_employees():
    """获取所有员工列表（用于员工管理界面）"""
    try:
        # 使用JOIN查询获取员工及其TOTP信息
        from sqlalchemy import and_

        # 获取所有员工及其TOTP信息
        results = db.session.query(
            Employee,
            TotpUser.totp_secret
        ).outerjoin(
            TotpUser,
            Employee.emp_id == TotpUser.emp_id
        ).all()

        employee_list = []
        for emp, totp_secret in results:
            employee_data = {
                'id': str(emp.id),  # 转换UUID为字符串
                'name': emp.name,
                'emp_id': emp.emp_id,
                'dept': emp.dept or '',
                'device_id': emp.device_id or '',
                'inner_ip': emp.inner_ip,
                'user_role': emp.user_role or 'sales',
                'status': emp.status or 'active',
                'remarks': emp.remarks or '',
                'last_login_time': emp.last_login_time.strftime("%Y-%m-%d %H:%M:%S") if emp.last_login_time else None,
                'login_device': emp.login_device or '',
                'create_time': emp.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                'update_time': emp.update_time.strftime("%Y-%m-%d %H:%M:%S") if emp.update_time and emp.update_time != emp.create_time else None,
                'totp_secret': totp_secret or ''  # 添加TOTP密钥字段
            }
            employee_list.append(employee_data)

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": {
                "list": employee_list
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取员工列表失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/permissions', methods=['GET'])
@route_permission(ROUTE_USER_MANAGE)
def get_user_permissions():
    """获取当前用户的权限列表"""
    try:
        from app.models.simple_permission import SimpleRole, SimpleRolePermission
        from app.utils.simple_auth_utils import get_user_role_from_token

        # 获取当前用户角色
        user_role = get_user_role_from_token()
        if not user_role:
            return jsonify({
                "code": 401,
                "msg": "未登录或登录已过期",
                "data": None
            }), 401

        # 管理员拥有所有权限
        if user_role == 'admin':
            from app.constants.simple_permission_constants import ALL_ROUTES
            permissions = {
                "role": user_role,
                "permissions": ALL_ROUTES,
                "is_admin": True
            }
        else:
            # 查询角色拥有的权限
            role = SimpleRole.query.filter_by(name=user_role).first()
            if not role:
                return jsonify({
                    "code": 404,
                    "msg": "角色不存在",
                    "data": None
                }), 404

            role_permissions = SimpleRolePermission.query.filter_by(role_id=role.id).all()
            permission_routes = [perm.route_name for perm in role_permissions]

            permissions = {
                "role": user_role,
                "permissions": permission_routes,
                "is_admin": False
            }

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": permissions
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取权限失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/user/permission/roles', methods=['GET'])
@route_permission(ROUTE_USER_MANAGE)
def get_user_permission_roles():
    """获取所有角色列表（用于前端角色管理）"""
    try:
        from app.models.simple_permission import SimpleRole

        # 获取所有角色
        roles = SimpleRole.query.all()
        role_list = []
        for role in roles:
            # 计算该角色拥有的权限数量
            from app.models.simple_permission import SimpleRolePermission
            permissions_count = SimpleRolePermission.query.filter_by(role_id=role.id).count()
            role_list.append({
                "role_name": role.name,
                "role_description": role.remark,
                "permissions_count": permissions_count
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


@user_bp.route('/user/permission/role-permissions', methods=['GET'])
@route_permission(ROUTE_USER_MANAGE)
def get_user_role_permissions():
    """获取指定角色的权限列表（用于前端角色权限管理）"""
    try:
        from app.models.simple_permission import SimpleRole, SimpleRolePermission

        # 从查询参数获取角色名
        role_name = request.args.get('role_name')
        if not role_name:
            return jsonify({
                "code": 400,
                "msg": "缺少角色名称参数",
                "data": None
            }), 400

        # 查询角色
        role = SimpleRole.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({
                "code": 404,
                "msg": "角色不存在",
                "data": None
            }), 404

        # 查询角色的权限
        role_permissions = SimpleRolePermission.query.filter_by(role_id=role.id).all()
        permissions = [perm.route_name for perm in role_permissions]

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


@user_bp.route('/user/permission/all-routes', methods=['GET'])
@route_permission(ROUTE_USER_MANAGE)
def get_all_routes():
    """获取所有可用的路由列表（用于前端权限分配）"""
    try:
        from app.constants.simple_permission_constants import ALL_ROUTES

        # 定义与前端 MODULE_CONSTANTS 一致的路由中文名称映射
        route_labels = {
            "display_file_manage": "展示文件管理",
            "photo_manage": "照片管理",
            "punch_manage": "打卡管理",
            "upload_manage": "上传管理",
            "video_manage": "视频管理",
            "inquiry_manage": "询盘管理",
            "order_manage": "订单管理",
            "order_status_manage": "订单状态管理",
            "expense_manage": "费用管理",
            "log_manage": "日志管理",
            "machine_manage": "机器管理",
            "machine_list": "机器管理",
            "user_manage": "用户管理",
            "permission_manage": "权限管理",
            "report_stat": "报表统计",
            "device_manage": "设备管理",
            "order_progress_manage": "订单进度管理",
            "auth_manage": "认证管理",
            "attendance_manage": "考勤管理",
        }

        # 从常量中获取所有路由
        routes = []
        for route in ALL_ROUTES:
            # 为每个路由创建一个对象，包含路由名称和显示标签
            routes.append({
                "route_name": route,
                "route_label": route_labels.get(route, route.replace('_', ' ').title())  # 使用预定义的中文名称，如果没有则使用默认格式
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


@user_bp.route('/user/permission/update-role-permissions', methods=['POST'])
@route_permission(ROUTE_USER_MANAGE)
def update_role_permissions():
    """更新角色权限（用于前端角色权限管理）"""
    try:
        from app.models.simple_permission import SimpleRole, SimpleRolePermission
        from app.constants.simple_permission_constants import ALL_ROUTES

        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        role_name = data.get('role_name')
        permissions = data.get('permissions', [])

        if not role_name:
            return jsonify({
                "code": 400,
                "msg": "角色名称不能为空",
                "data": None
            }), 400

        if not isinstance(permissions, list):
            return jsonify({
                "code": 400,
                "msg": "权限必须是数组格式",
                "data": None
            }), 400

        # 查询角色
        role = SimpleRole.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({
                "code": 404,
                "msg": "角色不存在",
                "data": None
            }), 404

        # 验证权限名称
        for perm in permissions:
            if perm not in ALL_ROUTES:
                return jsonify({
                    "code": 400,
                    "msg": f"无效的权限名称: {perm}",
                    "data": None
                }), 400

        # 删除该角色现有的所有权限
        SimpleRolePermission.query.filter_by(role_id=role.id).delete()

        # 添加新权限
        for perm in permissions:
            role_permission = SimpleRolePermission(
                role_id=role.id,
                route_name=perm
            )
            db.session.add(role_permission)

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "角色权限更新成功",
            "data": {
                "role_name": role_name,
                "permissions": permissions
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新角色权限失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/totp-qr', methods=['POST'])
def generate_totp_qr():
    """
    生成TOTP配置URI，用于绑定验证器APP
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        emp_id = data.get('emp_id')

        if not emp_id:
            return jsonify({
                "code": 400,
                "msg": "员工ID不能为空",
                "data": None
            }), 400

        # 查询员工信息（使用大小写不敏感的查询）
        emp_id_lower = emp_id.lower()
        employee = Employee.query.filter(db.func.lower(Employee.emp_id) == emp_id_lower).first()

        if not employee:
            return jsonify({
                "code": 404,
                "msg": "员工信息不存在",
                "data": None
            }), 404

        # 检查员工状态是否为"待绑定"，只有此状态的员工可以获取TOTP配置
        if employee.status != 'pending_binding':
            return jsonify({
                "code": 400,
                "msg": f"员工账号状态({employee.status})不符合绑定TOTP验证器的条件，应为'待绑定'状态",
                "data": None
            }), 400

        # 检查是否已经存在TOTP配置
        existing_totp_user = TotpUser.query.filter(db.func.lower(TotpUser.emp_id) == emp_id_lower).first()
        if existing_totp_user:
            # 如果已存在TOTP配置，直接返回现有的URI（允许用户多次获取相同的二维码，直到验证成功）
            # 这样用户可以重新获取二维码，如果他们之前没有完成验证流程
            totp_uri = pyotp.totp.TOTP(existing_totp_user.totp_secret).provisioning_uri(
                name=employee.emp_id,
                issuer_name="Soonwin OA System"
            )

            return jsonify({
                "code": 200,
                "msg": "TOTP配置获取成功（使用现有配置）",
                "data": {
                    "totp_uri": totp_uri,
                    "name": employee.name
                }
            })

        # 生成TOTP密钥
        totp_secret = pyotp.random_base32()

        # 为员工创建TOTP配置
        totp_user = TotpUser(
            emp_id=employee.emp_id,
            name=employee.name,
            totp_secret=totp_secret
        )
        db.session.add(totp_user)
        db.session.commit()

        # 生成TOTP URI，用于生成二维码
        totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
            name=employee.emp_id,
            issuer_name="Soonwin OA System"
        )

        return jsonify({
            "code": 200,
            "msg": "TOTP配置生成成功",
            "data": {
                "totp_uri": totp_uri,
                "name": employee.name
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"生成TOTP配置失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/totp/login', methods=['POST'])
def totp_login():
    """
    TOTP登录接口
    通过员工ID和TOTP验证码进行登录
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        emp_id = data.get('emp_id')
        totp_code = data.get('totp_code')

        if not emp_id or not totp_code:
            return jsonify({
                "code": 400,
                "msg": "员工ID和TOTP验证码不能为空",
                "data": None
            }), 400

        # 验证TOTP验证码长度
        if len(str(totp_code)) != 6:
            return jsonify({
                "code": 400,
                "msg": "TOTP验证码必须为6位数字",
                "data": None
            }), 400

        # 查询员工和TOTP用户信息（使用大小写不敏感的查询）
        emp_id_lower = emp_id.lower()
        employee = Employee.query.filter(db.func.lower(Employee.emp_id) == emp_id_lower).first()
        totp_user = TotpUser.query.filter(db.func.lower(TotpUser.emp_id) == emp_id_lower).first()

        if not employee:
            return jsonify({
                "code": 401,
                "msg": "员工信息不存在或未绑定TOTP验证器",
                "data": None
            }), 401

        if not totp_user:
            return jsonify({
                "code": 401,
                "msg": "员工未绑定TOTP验证器",
                "data": None
            }), 401

        # 验证员工状态
        # 对于"待绑定"状态的员工，如果TOTP验证成功，则自动激活账号
        if employee.status == 'inactive':
            return jsonify({
                "code": 401,
                "msg": f"员工账号状态异常({employee.status})，无法登录",
                "data": None
            }), 401

        # 验证TOTP验证码
        totp = pyotp.TOTP(totp_user.totp_secret)
        is_valid = totp.verify(totp_code)

        if not is_valid:
            return jsonify({
                "code": 401,
                "msg": "TOTP验证码错误或已过期",
                "data": None
            }), 401

        # 验证成功后，如果员工状态是"待绑定"，则更新为"已激活"
        if employee.status == 'pending_binding':
            employee.status = 'active'

        # 更新员工的最后登录时间
        employee.last_login_time = datetime.now()
        # 获取设备信息（从请求中获取IP等信息作为设备信息）
        employee.login_device = request.headers.get('User-Agent', 'Unknown') + ' - ' + request.remote_addr
        db.session.commit()

        # 生成JWT令牌 (2小时有效期)
        payload = {
            'emp_id': employee.emp_id,
            'name': employee.name,
            'user_role': employee.user_role,
            'exp': datetime.now() + timedelta(hours=2)  # 2小时后过期
        }
        token = jwt.encode(payload, config.Config.JWT_SECRET_KEY, algorithm='HS256')

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
def verify_totp_and_bind():
    """
    验证TOTP验证码并绑定（用于TOTP验证器绑定流程）
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        emp_id = data.get('emp_id')
        totp_code = data.get('totp_code')

        if not emp_id or not totp_code:
            return jsonify({
                "code": 400,
                "msg": "员工ID和TOTP验证码不能为空",
                "data": None
            }), 400

        # 验证TOTP验证码长度
        if len(str(totp_code)) != 6:
            return jsonify({
                "code": 400,
                "msg": "TOTP验证码必须为6位数字",
                "data": None
            }), 400

        # 查询员工和TOTP用户信息（使用大小写不敏感的查询）
        emp_id_lower = emp_id.lower()
        employee = Employee.query.filter(db.func.lower(Employee.emp_id) == emp_id_lower).first()
        totp_user = TotpUser.query.filter(db.func.lower(TotpUser.emp_id) == emp_id_lower).first()

        if not employee:
            return jsonify({
                "code": 404,
                "msg": "员工信息不存在",
                "data": None
            }), 404

        if not totp_user:
            return jsonify({
                "code": 404,
                "msg": "员工未绑定TOTP验证器或TOTP配置不存在",
                "data": None
            }), 404

        # 验证TOTP验证码
        totp = pyotp.TOTP(totp_user.totp_secret)
        is_valid = totp.verify(totp_code)

        if not is_valid:
            return jsonify({
                "code": 401,
                "msg": "TOTP验证码错误或已过期，请重试",
                "data": None
            }), 401

        # 验证成功，可以完成绑定流程（在前端调用此接口后会更新员工状态为'active'）
        return jsonify({
            "code": 200,
            "msg": "TOTP验证成功，可以完成绑定",
            "data": {
                "emp_id": employee.emp_id,
                "name": employee.name
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"TOTP验证失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/user/permissions', methods=['GET'])
def get_current_user_permissions():
    """获取当前用户的权限列表（用于前端权限验证）"""
    try:
        from app.models.simple_permission import SimpleRole, SimpleRolePermission, get_user_role_from_token
        from app.utils.auth_utils import get_user_id_from_token

        # 获取当前用户角色
        user_role = get_user_role_from_token()
        if not user_role:
            return jsonify({
                "code": 401,
                "msg": "未登录或登录已过期",
                "data": None
            }), 401

        # 管理员拥有所有权限
        if user_role == 'admin':
            from app.constants.simple_permission_constants import ALL_ROUTES
            permissions = []
            for route in ALL_ROUTES:
                permissions.append({
                    "id": "",
                    "role_name": user_role,
                    "route_name": route,
                    "create_time": "",
                    "update_time": None
                })
        else:
            # 查询角色拥有的权限
            role = SimpleRole.query.filter_by(name=user_role).first()
            if not role:
                return jsonify({
                    "code": 404,
                    "msg": "角色不存在",
                    "data": None
                }), 404

            role_permissions = SimpleRolePermission.query.filter_by(role_id=role.id).all()
            permissions = []
            for perm in role_permissions:
                try:
                    # SimpleRolePermission 模型只有 id, role_id, route_name 字段
                    # 没有 create_time 和 update_time 字段
                    perm_id = getattr(perm, 'id', None)
                    route_name = getattr(perm, 'route_name', '')

                    permissions.append({
                        "id": str(perm_id) if perm_id else "",
                        "role_name": user_role,
                        "route_name": route_name,
                        "create_time": "",  # 保持兼容性，但SimpleRolePermission模型无此字段
                        "update_time": None  # 保持兼容性，但SimpleRolePermission模型无此字段
                    })
                except Exception as e:
                    print(f"处理权限记录时出错: {str(e)}, 权限对象: {perm}")
                    continue  # 跳过有问题的记录

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": permissions
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取权限失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/user/permission/delete-role', methods=['POST'])
@route_permission(ROUTE_USER_MANAGE)
def delete_user_role():
    """删除角色（用于前端角色管理）"""
    try:
        from app.models.simple_permission import SimpleRole, SimpleRolePermission

        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        role_name = data.get('role_name')

        if not role_name:
            return jsonify({
                "code": 400,
                "msg": "角色名称不能为空",
                "data": None
            }), 400

        # 不能删除admin角色
        if role_name == 'admin':
            return jsonify({
                "code": 400,
                "msg": "不能删除管理员角色",
                "data": None
            }), 400

        # 查询角色
        role = SimpleRole.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({
                "code": 404,
                "msg": "角色不存在",
                "data": None
            }), 404

        # 检查是否有用户使用此角色
        from app.models.employee import Employee
        users_with_role = Employee.query.filter_by(user_role=role_name).count()
        if users_with_role > 0:
            return jsonify({
                "code": 400,
                "msg": f"无法删除角色：有{users_with_role}个用户正在使用此角色",
                "data": None
            }), 400

        # 删除该角色的所有权限关联
        SimpleRolePermission.query.filter_by(role_id=role.id).delete()

        # 删除角色本身
        db.session.delete(role)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "角色删除成功",
            "data": {
                "role_name": role_name
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除角色失败: {str(e)}",
            "data": None
        }), 500


@user_bp.route('/user/permission/update-role-description', methods=['POST'])
@route_permission(ROUTE_USER_MANAGE)
def update_role_description():
    """更新角色描述"""
    try:
        from app.models.simple_permission import SimpleRole
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

        # 检查角色名称有效性
        role_name = role_name.strip()
        if len(role_name) < 1:
            return jsonify({
                "code": 400,
                "msg": "角色名称不能为空字符串",
                "data": None
            }), 400

        # 检查是否是纯空白字符
        if not role_name or role_name.isspace():
            return jsonify({
                "code": 400,
                "msg": "角色名称不能只包含空白字符",
                "data": None
            }), 400

        # 检查角色描述有效性
        role_description = role_description.strip()
        if len(role_description) < 1:
            return jsonify({
                "code": 400,
                "msg": "角色描述不能为空字符串",
                "data": None
            }), 400

        # 更新角色描述
        role = SimpleRole.query.filter_by(name=role_name).first()
        if not role:
            # 如果角色不存在，创建新角色
            role = SimpleRole(name=role_name, remark=role_description)
            db.session.add(role)
        else:
            role.remark = role_description
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "角色描述更新/创建成功",
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
