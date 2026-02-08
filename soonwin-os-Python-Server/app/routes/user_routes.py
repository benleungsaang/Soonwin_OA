"""用户相关的路由"""
from flask import Blueprint, request, jsonify
from app.models.employee import Employee
from app.utils.auth_utils import require_auth, require_admin, require_module_permission
from extensions import db
import hashlib
import config
import jwt
from datetime import datetime, timedelta
from app.utils.auth_utils import get_user_role_from_token, is_admin_user
import traceback
from app.models.totp_user import TotpUser
import uuid
from sqlalchemy import func
from app.constants.permission_constants import MODULE_USER_MANAGE

# 创建蓝图
user_bp = Blueprint('user', __name__, url_prefix='/api')

@user_bp.route('/init-admin', methods=['POST'])
@require_module_permission(MODULE_USER_MANAGE, "edit")
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
@require_module_permission(MODULE_USER_MANAGE, "edit")  # 只有管理员可以创建员工
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

        # 验证角色值
        valid_roles = ['admin', 'sales', 'user']
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
@require_module_permission(MODULE_USER_MANAGE, "view")
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
@require_module_permission(MODULE_USER_MANAGE, "edit")
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
            valid_roles = ['admin', 'sales', 'user']
            if data['user_role'] in valid_roles:
                employee.user_role = data['user_role']
            else:
                return jsonify({
                    "code": 400,
                    "msg": f"无效的角色值: {data['user_role']}",
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
@require_module_permission(MODULE_USER_MANAGE, "delete")
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
@require_module_permission(MODULE_USER_MANAGE, "edit")
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
@require_module_permission(MODULE_USER_MANAGE, "edit")
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
@require_module_permission(MODULE_USER_MANAGE, "view")
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
        
        # 管理员拥有所有权限，返回所有模块的完全权限
        if user_role == 'admin':
            # 返回预定义的所有模块的完全权限
            all_modules = [
                "employee_manage", "expense_manage", "machine_parts_manage", 
                "photo_manage", "video_manage", "order_manage", 
                "inquiry_manage", "order_status_manage", "punch_manage", 
                "display_file_manage", "permission_manage", "log_manage", 
                "report_stat", "order_progress_manage"
            ]
            
            permissions = []
            for module in all_modules:
                permissions.append({
                    "id": "",  # 管理员权限是虚拟的，不需要实际ID
                    "role_name": "admin",
                    "module_name": module,
                    "can_view": True,
                    "can_edit": True,
                    "can_delete": True,
                    "create_time": "",
                    "update_time": None
                })
            
            return jsonify({
                "code": 200,
                "msg": "success",
                "data": permissions
            })
        
        # 普通用户返回其角色的实际权限
        from app.models.permission import RolePermission
        permissions = RolePermission.query.filter_by(role_name=user_role).all()
        result = [perm.to_dict() for perm in permissions]
        
        return jsonify({
            "code": 200,
            "msg": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取用户权限失败: {str(e)}",
            "data": None
        }), 500