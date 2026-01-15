from flask import Blueprint, request, jsonify
from extensions import db
from app.models.employee import Employee
from app.models.punch_record import PunchRecord
from app.models.totp_user import TotpUser
from app.models.order import Order
from app.models.cost_allocation import CostAllocation
from app.utils.auth_utils import require_admin, require_auth
from datetime import datetime, timedelta
import pyotp
import jwt
import config
import re
import json
from decimal import Decimal

# ===================== 这里是全局变量插入位置 =====================
# 定义服务器静态IP全局变量（你的服务器固定内网IP，按需修改即可）
SERVER_INNER_IP = "192.168.1.24"
# =================================================================

# 创建蓝图
user_bp = Blueprint('user', __name__)

@user_bp.route('/init-admin', methods=['POST'])
def init_admin():
    """初始化管理员账号"""
    try:
        # 检查是否已存在管理员账号
        existing_admin = Employee.query.filter_by(emp_id='admin').first()
        if existing_admin:
            return jsonify({
                "code": 400,
                "msg": "管理员账号已存在",
                "data": None
            }), 400

        # 创建TOTP密钥
        totp_secret = pyotp.random_base32()

        # 生成唯一的phone_mac值，避免唯一性约束冲突
        import uuid
        # 生成基于管理员ID和随机数的唯一MAC地址
        unique_mac = f"FF:{str(uuid.uuid4()).split('-')[0][:2]}:{str(uuid.uuid4()).split('-')[1][:2]}:{str(uuid.uuid4()).split('-')[2][:2]}:{str(uuid.uuid4()).split('-')[3][:2]}:FE".upper()

        # 创建管理员员工记录
        admin_employee = Employee(
            name="管理员",
            emp_id="admin",
            dept="系统管理",
            phone_mac=unique_mac,  # 使用生成的唯一MAC地址
            inner_ip="127.0.0.1",  # 管理员默认值
            user_role="admin",
            status="active"
        )
        db.session.add(admin_employee)

        # 创建TOTP用户记录
        totp_user = TotpUser(
            emp_id="admin",
            name="管理员",
            totp_secret=totp_secret,
            create_time=datetime.now()
        )
        db.session.add(totp_user)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "管理员账户初始化成功",
            "data": {
                "emp_id": "admin",
                "name": "管理员",
                "totp_secret": totp_secret
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"初始化管理员账户失败: {str(e)}",
            "data": None
        }), 500

@user_bp.route('/employee', methods=['POST'])
@require_admin  # 只有管理员可以创建员工
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

        # 检查员工ID是否已存在
        existing_employee = Employee.query.filter_by(emp_id=data['emp_id']).first()
        if existing_employee:
            return jsonify({
                "code": 400,
                "msg": "员工ID已存在",
                "data": None
            }), 400

        # 如果没有提供phone_mac，则生成唯一的phone_mac值，避免唯一性约束冲突
        import uuid
        if not data.get('phone_mac'):
            # 生成基于员工ID和随机数的唯一MAC地址
            unique_mac = f"AA:{str(uuid.uuid4()).split('-')[0][:2]}:{str(uuid.uuid4()).split('-')[1][:2]}:{str(uuid.uuid4()).split('-')[2][:2]}:{str(uuid.uuid4()).split('-')[3][:2]}:BB".upper()
        else:
            unique_mac = data.get('phone_mac')

        # 创建员工记录
        new_employee = Employee(
            name=data['name'],
            emp_id=data['emp_id'],
            dept=data.get('dept', ''),
            remarks=data.get('remarks', ''),  # 添加备注字段
            phone_mac=unique_mac,  # 使用生成的唯一MAC地址
            inner_ip=data.get('inner_ip', '0.0.0.0'),  # 默认值
            user_role=data.get('user_role', 'user'),
            status='pending_binding'  # 新员工初始状态为待绑定
        )
        db.session.add(new_employee)

        # 创建TOTP密钥
        totp_secret = pyotp.random_base32()

        # 创建TOTP用户记录
        totp_user = TotpUser(
            emp_id=data['emp_id'],
            name=data['name'],
            totp_secret=totp_secret,
            create_time=datetime.now()
        )
        db.session.add(totp_user)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "员工创建成功",
            "data": {
                "emp_id": data['emp_id'],
                "name": data['name'],
                "totp_secret": totp_secret
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建员工失败: {str(e)}",
            "data": None
        }), 500

@user_bp.route('/employees', methods=['GET'])
@require_admin  # 只有管理员可以查看所有员工
def get_employees():
    """获取所有员工"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 分页查询
        pagination = db.session.query(Employee).paginate(
            page=page, per_page=size, error_out=False
        )
        employees = pagination.items

        return jsonify({
            "code": 200,
            "msg": "获取员工列表成功",
            "data": [
                {
                    "id": str(emp.id),  # UUID转字符串
                    "emp_id": emp.emp_id,
                    "name": emp.name,
                    "dept": emp.dept,
                    "phone_mac": emp.phone_mac,
                    "inner_ip": emp.inner_ip,
                    "user_role": emp.user_role,
                    "status": emp.status,
                    "remarks": emp.remarks,
                    "last_login_time": emp.last_login_time.strftime("%Y-%m-%d %H:%M:%S") if emp.last_login_time else None,
                    "login_device": emp.login_device,
                    "create_time": emp.create_time.strftime("%Y-%m-%d %H:%M:%S")
                } for emp in employees
            ],
            "total": pagination.total,
            "page": page,
            "size": size
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取员工列表失败: {str(e)}",
            "data": None
        }), 500

@user_bp.route('/employee/<emp_id>', methods=['PUT'])
@require_admin  # 只有管理员可以更新员工信息
def update_employee(emp_id):
    """更新员工信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 查询员工记录
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return jsonify({
                "code": 404,
                "msg": "员工不存在",
                "data": None
            }), 404

        # 检查新员工ID是否已被其他员工使用
        new_emp_id = data.get('emp_id')
        if new_emp_id and new_emp_id != emp_id:
            existing_employee = Employee.query.filter_by(emp_id=new_emp_id).first()
            if existing_employee:
                return jsonify({
                    "code": 400,
                    "msg": "新员工ID已被使用",
                    "data": None
                }), 400

        # 保存旧的emp_id用于后续更新TOTP记录
        old_emp_id = employee.emp_id

        # 检查phone_mac是否被其他员工使用
        new_phone_mac = data.get('phone_mac')
        if new_phone_mac and new_phone_mac != employee.phone_mac:
            # 检查是否已有其他员工使用此MAC地址
            existing_employee_with_mac = Employee.query.filter(
                Employee.phone_mac == new_phone_mac,
                Employee.emp_id != emp_id  # 排除当前员工
            ).first()

            if existing_employee_with_mac:
                return jsonify({
                    "code": 400,
                    "msg": f"MAC地址 {new_phone_mac} 已被员工 {existing_employee_with_mac.name}({existing_employee_with_mac.emp_id}) 使用"
                }), 400

        # 更新员工信息
        employee.name = data.get('name', employee.name)
        employee.dept = data.get('dept', employee.dept)
        employee.user_role = data.get('user_role', employee.user_role)
        employee.status = data.get('status', employee.status)
        employee.remarks = data.get('remarks', employee.remarks)
        if new_phone_mac:
            employee.phone_mac = new_phone_mac

        # 如果员工ID被修改，更新它
        if new_emp_id and new_emp_id != emp_id:
            employee.emp_id = new_emp_id

        # 如果员工ID被修改，同时更新TOTP用户记录
        if old_emp_id != employee.emp_id:
            totp_user = TotpUser.query.filter_by(emp_id=old_emp_id).first()
            if totp_user:
                totp_user.emp_id = employee.emp_id
                totp_user.name = employee.name

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "员工信息更新成功",
            "data": {
                "emp_id": employee.emp_id,
                "name": employee.name,
                "dept": employee.dept,
                "user_role": employee.user_role,
                "status": employee.status
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新员工信息失败: {str(e)}",
            "data": None
        }), 500

@user_bp.route('/employee/<emp_id>', methods=['DELETE'])
@require_admin  # 只有管理员可以删除员工
def delete_employee(emp_id):
    """删除员工"""
    try:
        # 查询员工记录
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return jsonify({
                "code": 404,
                "msg": "员工不存在",
                "data": None
            }), 404

        # 删除员工记录
        db.session.delete(employee)

        # 同时删除相关的TOTP用户记录
        totp_user = TotpUser.query.filter_by(emp_id=emp_id).first()
        if totp_user:
            db.session.delete(totp_user)

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
def generate_totp_qr():
    """生成TOTP二维码（用于绑定验证器）"""
    try:
        # 确保Content-Type是application/json
        if request.is_json:
            data = request.get_json()
        else:
            # 如果不是JSON格式，尝试解析
            data = request.get_json(force=True)

        if not data or 'emp_id' not in data:
            return jsonify({
                "code": 400,
                "msg": "缺少员工ID",
                "data": None
            }), 400

        # 检查员工是否存在
        employee = Employee.query.filter_by(emp_id=data['emp_id']).first()
        if not employee:
            return jsonify({
                "code": 404,
                "msg": "员工不存在",
                "data": None
            }), 404

        # 检查TOTP用户是否存在
        totp_user = TotpUser.query.filter_by(emp_id=data['emp_id']).first()
        if not totp_user:
            # 如果TOTP配置不存在，但员工处于待绑定状态，则创建一个新的TOTP配置
            if employee.status == 'pending_binding':
                # 创建TOTP密钥
                totp_secret = pyotp.random_base32()

                # 创建TOTP用户记录
                totp_user = TotpUser(
                    emp_id=data['emp_id'],
                    name=employee.name,
                    totp_secret=totp_secret,
                    create_time=datetime.now()
                )
                db.session.add(totp_user)
                db.session.commit()
            else:
                return jsonify({
                    "code": 404,
                    "msg": "TOTP配置不存在",
                    "data": None
                }), 404

        # 获取TOTP密钥
        totp_secret = totp_user.totp_secret

        # 生成TOTP URI
        totp = pyotp.TOTP(totp_secret)
        totp_uri = totp.provisioning_uri(
            name=employee.name,
            issuer_name="SoonWinOA"
        )

        # 生成二维码内容（返回URI，前端负责生成二维码）
        return jsonify({
            "code": 200,
            "msg": "TOTP配置获取成功",
            "data": {
                "emp_id": data['emp_id'],
                "name": employee.name,
                "totp_uri": totp_uri,
                "secret": totp_secret
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
    """TOTP登录接口"""
    try:
        data = request.get_json()
        required_fields = ['emp_id', 'totp_code']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "code": 400,
                    "msg": f"缺少必要字段: {field}",
                    "data": None
                }), 400

        # 检查员工是否存在
        employee = Employee.query.filter_by(emp_id=data['emp_id']).first()
        if not employee:
            return jsonify({
                "code": 404,
                "msg": "员工不存在",
                "data": None
            }), 404

        # 检查员工状态
        if employee.user_role != 'admin':
            if employee.status != 'active' and employee.status != 'pending_binding':
                return jsonify({
                    "code": 403,
                    "msg": "员工账户未激活",
                    "data": None
                }), 403

        # 检查TOTP用户是否存在
        totp_user = TotpUser.query.filter_by(emp_id=data['emp_id']).first()
        if not totp_user:
            return jsonify({
                "code": 404,
                "msg": "TOTP配置不存在",
                "data": None
            }), 404

        # 验证TOTP码
        totp = pyotp.TOTP(totp_user.totp_secret)
        is_valid = totp.verify(data['totp_code'])

        if is_valid:
            # 如果员工状态是"待绑定"，验证成功后更新为"已激活"
            if employee.status == 'pending_binding':
                employee.status = 'active'
                db.session.commit()

            # 更新最后登录时间和设备信息
            employee.last_login_time = datetime.now()
            # 获取客户端IP作为登录设备IP
            login_device_ip = request.remote_addr or 'unknown'
            # 获取User-Agent作为设备信息
            user_agent = request.headers.get('User-Agent', 'unknown')
            employee.login_device = f"IP: {login_device_ip}, Browser: {user_agent}"
            db.session.commit()

            # 生成JWT令牌
            payload = {
                'emp_id': employee.emp_id,
                'name': employee.name,
                'user_role': employee.user_role,
                'exp': datetime.now() + timedelta(hours=2)  # 2小时后过期
            }
            token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')

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
        else:
            return jsonify({
                "code": 401,
                "msg": "TOTP验证码错误",
                "data": None
            }), 401
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"登录失败: {str(e)}",
            "data": None
        }), 500

@user_bp.route('/verify-totp', methods=['POST'])
def verify_totp():
    """验证TOTP码（用于绑定验证器）"""
    try:
        data = request.get_json()
        required_fields = ['emp_id', 'totp_code']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "code": 400,
                    "msg": f"缺少必要字段: {field}",
                    "data": None
                }), 400

        # 检查员工是否存在
        employee = Employee.query.filter_by(emp_id=data['emp_id']).first()
        if not employee:
            return jsonify({
                "code": 404,
                "msg": "员工不存在",
                "data": None
            }), 404

        # 检查员工状态是否为待绑定
        if employee.status != 'pending_binding':
            return jsonify({
                "code": 400,
                "msg": "员工状态不是待绑定",
                "data": None
            }), 400

        # 检查TOTP用户是否存在
        totp_user = TotpUser.query.filter_by(emp_id=data['emp_id']).first()
        if not totp_user:
            return jsonify({
                "code": 404,
                "msg": "TOTP配置不存在"
            }), 404

        # 验证TOTP码
        totp = pyotp.TOTP(totp_user.totp_secret)
        is_valid = totp.verify(data['totp_code'])

        if is_valid:
            # 更新员工状态为待审批
            employee.status = 'pending_approval'
            db.session.commit()

            return jsonify({
                "code": 200,
                "msg": "TOTP验证成功，账户已更新为待审批状态",
                "data": None
            })
        else:
            return jsonify({
                "code": 400,
                "msg": "TOTP验证码错误",
                "data": None
            }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"TOTP验证失败: {str(e)}",
            "data": None
        }), 500