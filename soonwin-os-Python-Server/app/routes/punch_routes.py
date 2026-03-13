import re
import json
import socket
import uuid
import jwt
import config
from flask import Blueprint, request, jsonify, redirect, Response
from extensions import db
from app.models.employee import Employee, UserStatus
from app.models.employee_device import EmployeeDevice
from app.models.punch_record import PunchRecord
from app.utils.auth_utils import require_admin, require_auth
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_PUNCH
from datetime import datetime, timedelta

# ===================== 全局变量与通用工具函数 =====================
def get_server_ip():
    """自动获取当前服务器内网IP（UDP连接方式）"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

# 服务器静态IP全局变量
SERVER_INNER_IP = get_server_ip()

def is_inner_net(ip):
    """检查IP是否为内网IP（192.168/10/127段）"""
    return ip.startswith(('192.168.', '10.', '127.'))

def is_mobile_device(user_agent=None):
    """检测是否为移动设备（基于User-Agent）"""
    user_agent = user_agent or request.headers.get('User-Agent', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'tablet']
    return any(keyword in user_agent for keyword in mobile_keywords)

def get_client_device_identifier():
    """获取客户端设备ID和IP（优先X-Forwarded-For，其次remote_addr）"""
    forwarded = request.headers.get('X-Forwarded-For')
    user_ip = forwarded.split(',')[0].strip() if forwarded else request.remote_addr

    # 从请求头/请求体获取设备ID
    device_id = None
    if request.is_json:
        device_id = request.json.get('device_id')
    if not device_id:
        device_id = request.headers.get('X-Device-ID')

    return device_id, user_ip

def detect_device_info():
    """统一检测设备信息，返回格式: 设备类型/操作系统/浏览器（去重冗余定义）"""
    user_agent = request.headers.get('User-Agent', '').lower()

    # 1. 检测操作系统
    os_info = "未知系统"
    if 'windows nt 10.0' in user_agent:
        os_info = "Windows 10"
    elif 'windows nt 11.0' in user_agent:
        os_info = "Windows 11"
    elif 'windows nt' in user_agent:
        win_match = re.search(r'windows nt (\d+\.\d+)', user_agent)
        os_info = f"Windows {win_match.group(1)}" if win_match else "Windows"
    elif 'mac os x' in user_agent:
        mac_match = re.search(r'mac os x (\d+[._]\d+)', user_agent)
        os_info = f"macOS {mac_match.group(1).replace('_', '.')}" if mac_match else "macOS"
    elif 'android' in user_agent:
        android_match = re.search(r'android[ /](\d+)', user_agent)
        os_info = f"Android {android_match.group(1)}" if android_match else "Android"
    elif 'ipad' in user_agent:
        os_info = "iPad"
    elif 'iphone' in user_agent:
        os_info = "iPhone"
    elif 'linux' in user_agent:
        os_info = "Linux"

    # 2. 检测设备类型
    device_type = "PC"
    if any(keyword in user_agent for keyword in ['mobile', 'android', 'iphone', 'ipad']):
        device_type = "移动设备"
    elif 'tablet' in user_agent:
        device_type = "平板设备"

    # 3. 检测浏览器
    browser = "未知浏览器"
    if 'headlesschrome' in user_agent:
        chrome_match = re.search(r'chrome/(\d+)', user_agent)
        browser = f"HeadlessChrome {chrome_match.group(1)}" if chrome_match else "HeadlessChrome"
    elif 'edg' in user_agent:
        edge_match = re.search(r'edg[ /](\d+)', user_agent)
        browser = f"Edge {edge_match.group(1)}" if edge_match else "Edge"
    elif 'chrome' in user_agent and 'edg' not in user_agent and 'opr' not in user_agent and 'whale' not in user_agent:
        chrome_match = re.search(r'chrome/(\d+)', user_agent)
        browser = f"Chrome {chrome_match.group(1)}" if chrome_match else "Chrome"
    elif 'safari' in user_agent and 'chrome' not in user_agent and 'android' not in user_agent:
        safari_match = re.search(r'version/(\d+)', user_agent)
        browser = f"Safari {safari_match.group(1)}" if safari_match else "Safari"

    return f"{device_type}/{os_info}/{browser}"

def validate_device_for_employee(emp_id, device_id):
    """验证设备是否已授权给该员工（提取通用逻辑）"""
    if not device_id:
        return False, "设备ID未提供，请首次打卡以绑定设备"

    employee = Employee.query.filter_by(emp_id=emp_id).first()
    if not employee:
        return False, "员工不存在"

    # 设备ID匹配验证
    if employee.device_id == device_id:
        return True, "设备验证成功"

    # 设备已绑定其他员工
    existing_employee = Employee.query.filter_by(device_id=device_id).first()
    if existing_employee and existing_employee.emp_id != emp_id:
        return False, f"设备已被员工 {existing_employee.name}({existing_employee.emp_id}) 绑定，请申请更换设备"

    # 员工已有设备但本次设备不一致
    if employee.device_id and employee.device_id != device_id:
        return False, "设备ID变化，请申请更换设备"

    # 设备未绑定任何员工（首次绑定）
    return False, "需要绑定设备"

def bind_device_to_employee(emp_id, device_id):
    """将设备ID绑定到员工（通用绑定逻辑）"""
    employee = Employee.query.filter_by(emp_id=emp_id).first()
    if not employee:
        return False, "员工不存在"

    # 检查设备是否被其他员工绑定
    existing_employee = Employee.query.filter_by(device_id=device_id).first()
    if existing_employee and existing_employee.emp_id != emp_id:
        return False, f"设备已绑定到其他员工 {existing_employee.name}({existing_employee.emp_id})"

    # 执行绑定
    employee.device_id = device_id
    db.session.commit()
    return True, "设备绑定成功"

def create_punch_record(employee, punch_type, user_ip, device_id, device_info):
    """创建打卡记录（提取重复的打卡记录创建逻辑）"""
    current_time = datetime.now()
    # 更新员工登录信息
    employee.last_login_time = current_time
    employee.login_device = device_info

    # 上班打卡：检查是否已有更早记录
    if punch_type == "上班打卡":
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = current_time.replace(hour=23, minute=59, second=59, microsecond=999999)
        existing_punch = PunchRecord.query.filter(
            PunchRecord.emp_id == employee.emp_id,
            PunchRecord.punch_type == "上班打卡",
            PunchRecord.punch_time >= today_start,
            PunchRecord.punch_time <= today_end
        ).order_by(PunchRecord.punch_time.asc()).first()

        if existing_punch and existing_punch.punch_time <= current_time:
            return {
                "code": 200,
                "msg": f"已在{existing_punch.punch_time.strftime('%H:%M')}成功打卡",
                "data": {
                    "emp_id": employee.emp_id,
                    "name": employee.name,
                    "punch_type": existing_punch.punch_type,
                    "punch_time": existing_punch.punch_time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }

    # 创建新打卡记录
    new_punch = PunchRecord(
        emp_id=employee.emp_id,
        name=employee.name,
        punch_type=punch_type,
        punch_time=current_time,
        inner_ip=user_ip,
        device_id=device_id,
        last_login_time=current_time,
        login_device=device_info
    )
    db.session.add(new_punch)
    db.session.commit()

    return {
        "code": 200,
        "msg": "打卡成功",
        "data": {
            "emp_id": employee.emp_id,
            "name": employee.name,
            "punch_type": punch_type,
            "punch_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

# ===================== 蓝图初始化与核心接口 =====================
punch_bp = Blueprint('punch', __name__)

@punch_bp.route('/api/device-clock-in', methods=['POST'])
def device_clock_in():
    """新的打卡API端点，支持设备ID验证和绑定（优化后）"""
    try:
        data = request.get_json() or {}
        emp_id = data.get('emp_id')
        device_id = data.get('device_id') or request.headers.get('X-Device-ID')
        request_device_change = data.get('request_device_change', False)

        # 基础参数校验
        if not emp_id:
            return jsonify({"code": 400, "msg": "员工ID未提供"}), 400

        # 1. 内网校验
        user_ip = request.remote_addr
        if not is_inner_net(user_ip):
            return jsonify({"code": 403, "msg": "非公司内网设备，禁止打卡！"}), 403

        # 2. 移动设备校验
        user_agent = request.headers.get('User-Agent', '')
        if not is_mobile_device(user_agent):
            return jsonify({"code": 403, "msg": "请使用个人手机进行打卡"}), 403

        # 3. 打卡类型判断
        current_hour = datetime.now().hour
        if 6 <= current_hour < 12:
            punch_type = "上班打卡"
        elif 12 <= current_hour < 22:
            punch_type = "下班打卡"
        else:
            punch_type = "非打卡时间打卡"

        # 4. 设备ID处理（首次打卡/已有设备）
        device_info = detect_device_info()
        if not device_id:
            # 首次打卡：生成新设备ID并绑定
            new_device_id = str(uuid.uuid4())
            bind_success, bind_msg = bind_device_to_employee(emp_id, new_device_id)
            if not bind_success:
                return jsonify({"code": 500, "msg": f"设备绑定失败: {bind_msg}"}), 500

            employee = Employee.query.filter_by(emp_id=emp_id).first()
            if not employee:
                return jsonify({"code": 404, "msg": "员工未找到"}), 404

            # 创建打卡记录并返回（含新设备ID）
            result = create_punch_record(employee, punch_type, user_ip, new_device_id, device_info)
            result["msg"] = "首次打卡成功"
            result["data"]["device_id"] = new_device_id
            return jsonify(result)

        # 5. 已有设备ID：验证设备合法性
        is_valid, msg = validate_device_for_employee(emp_id, device_id)
        if not is_valid:
            # 首次绑定设备（设备未绑定任何员工）
            if "需要绑定设备" in msg:
                new_device_id = str(uuid.uuid4())
                bind_success, bind_msg = bind_device_to_employee(emp_id, new_device_id)
                if not bind_success:
                    return jsonify({"code": 500, "msg": f"设备绑定失败: {bind_msg}"}), 500

                employee = Employee.query.filter_by(emp_id=emp_id).first()
                if not employee:
                    return jsonify({"code": 404, "msg": "员工未找到"}), 404

                result = create_punch_record(employee, punch_type, user_ip, new_device_id, device_info)
                result["msg"] = "首次打卡成功"
                result["data"]["device_id"] = new_device_id
                return jsonify(result)

            # 设备ID变化：处理更换申请
            elif "设备ID变化" in msg:
                if request_device_change:
                    # 主动申请更换：创建待审批记录
                    employee = Employee.query.filter_by(emp_id=emp_id).first()
                    if not employee:
                        return jsonify({"code": 404, "msg": "员工未找到"}), 404

                    current_time = datetime.now()
                    employee.last_login_time = current_time
                    employee.login_device = device_info

                    pending_punch = PunchRecord(
                        emp_id=employee.emp_id,
                        name=employee.name,
                        punch_type=punch_type,
                        punch_time=current_time,
                        inner_ip=user_ip,
                        device_id=device_id,
                        last_login_time=current_time,
                        login_device=device_info
                    )
                    db.session.add(pending_punch)
                    db.session.commit()

                    return jsonify({
                        "code": 200,
                        "msg": "设备更换申请已提交，请等待管理员审批",
                        "data": {
                            "emp_id": employee.emp_id,
                            "name": employee.name,
                            "punch_type": punch_type,
                            "punch_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "pending_approval"
                        }
                    })
                else:
                    # 非主动申请：提示更换设备
                    return jsonify({
                        "code": 200,
                        "msg": "设备ID发生变化，请申请更换设备",
                        "data": {"emp_id": emp_id, "status": "device_change_required"}
                    })

            # 其他验证失败（如设备绑定其他员工）
            else:
                return jsonify({"code": 403, "msg": msg}), 403

        # 6. 设备验证成功：创建打卡记录
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return jsonify({"code": 404, "msg": "员工未找到"}), 404

        result = create_punch_record(employee, punch_type, user_ip, device_id, device_info)
        return jsonify(result)

    except Exception as e:
        db.session.rollback()  # 异常时回滚事务
        return jsonify({"code": 500, "msg": f"打卡失败: {str(e)}"}), 500

# ===================== 其他接口（仅优化异常处理和代码可读性） =====================
@punch_bp.route('/api/request-device-change', methods=['POST'])
@route_permission(ROUTE_PUNCH)
def request_device_change():
    """请求更换设备的API端点（优化后）"""
    try:
        data = request.get_json() or {}
        emp_id = data.get('emp_id')
        new_device_id = data.get('new_device_id')

        if not emp_id or not new_device_id:
            return jsonify({"code": 400, "msg": "员工ID和新设备ID不能为空"}), 400

        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return jsonify({"code": 404, "msg": "员工未找到"}), 404

        # 检查新设备是否被占用
        existing_employee = Employee.query.filter_by(device_id=new_device_id).first()
        if existing_employee and existing_employee.emp_id != emp_id:
            return jsonify({
                "code": 409,
                "msg": f"新设备ID已被员工 {existing_employee.name}({existing_employee.emp_id}) 使用"
            }), 409

        # 创建更换申请记录
        current_time = datetime.now()
        change_request = PunchRecord(
            emp_id=emp_id,
            name=employee.name,
            punch_type="设备更换申请",
            punch_time=current_time,
            inner_ip=request.remote_addr,
            device_id=new_device_id,
            last_login_time=current_time,
            login_device=detect_device_info()
        )
        db.session.add(change_request)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "设备更换申请已提交",
            "data": {
                "request_id": change_request.id,
                "emp_id": emp_id,
                "old_device_id": employee.device_id,
                "new_device_id": new_device_id,
                "request_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending"
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"提交设备更换申请失败: {str(e)}"}), 500

@punch_bp.route('/api/approve-device-change', methods=['POST'])
@route_permission(ROUTE_PUNCH)
def approve_device_change():
    """管理员批准设备更换申请（优化后）"""
    try:
        data = request.get_json() or {}
        request_id = data.get('request_id')

        if not request_id:
            return jsonify({"code": 400, "msg": "申请ID不能为空"}), 400

        punch_record = PunchRecord.query.get(request_id)
        if not punch_record or punch_record.punch_type != "设备更换申请":
            return jsonify({"code": 404, "msg": "未找到设备更换申请"}), 404

        employee = Employee.query.filter_by(emp_id=punch_record.emp_id).first()
        if not employee:
            return jsonify({"code": 404, "msg": "员工未找到"}), 404

        # 更新设备ID和申请状态
        old_device_id = employee.device_id
        employee.device_id = punch_record.device_id
        punch_record.punch_type = "设备更换已批准"
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "设备更换申请已批准",
            "data": {
                "emp_id": employee.emp_id,
                "old_device_id": old_device_id,
                "new_device_id": punch_record.device_id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"批准设备更换申请失败: {str(e)}"}), 500

@punch_bp.route('/api/reject-device-change', methods=['POST'])
@route_permission(ROUTE_PUNCH)
def reject_device_change():
    """管理员拒绝设备更换申请（优化后）"""
    try:
        data = request.get_json() or {}
        request_id = data.get('request_id')

        if not request_id:
            return jsonify({"code": 400, "msg": "申请ID不能为空"}), 400

        punch_record = PunchRecord.query.get(request_id)
        if not punch_record or punch_record.punch_type != "设备更换申请":
            return jsonify({"code": 404, "msg": "未找到设备更换申请"}), 404

        db.session.delete(punch_record)
        db.session.commit()
        return jsonify({"code": 200, "msg": "设备更换申请已拒绝"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"拒绝设备更换申请失败: {str(e)}"}), 500

@punch_bp.route('/api/employee-info/<emp_id>', methods=['GET'])
@route_permission(ROUTE_PUNCH)
def get_employee_info(emp_id):
    """获取员工信息接口（包含备注字段）（优化后）"""
    try:
        # 认证校验
        token = request.headers.get('Authorization', '').replace("Bearer ", "")
        if not token:
            return jsonify({"code": 401, "msg": "需要认证才能访问员工信息", "data": None}), 401

        try:
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_emp_id = payload['emp_id']
            current_user_role = payload['user_role']

            # 权限校验：普通用户只能看自己，管理员可看所有
            if current_user_role != 'admin' and current_emp_id != emp_id:
                return jsonify({"code": 403, "msg": "权限不足，只能查看自己的信息", "data": None}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({"code": 401, "msg": "令牌已过期", "data": None}), 401
        except jwt.InvalidTokenError:
            return jsonify({"code": 401, "msg": "无效的令牌", "data": None}), 401

        # 查询员工信息（大小写不敏感）
        employee = Employee.query.filter(db.func.lower(Employee.emp_id) == emp_id.lower()).first()
        if not employee:
            return jsonify({"code": 404, "msg": f"未找到员工ID为 {emp_id} 的员工"}), 404

        return jsonify({"code": 200, "msg": "获取员工信息成功", "data": employee.to_dict()})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取员工信息失败: {str(e)}"}), 500

@punch_bp.route('/api/employee-basic-info/<emp_id>', methods=['GET'])
def get_employee_basic_info(emp_id):
    """获取员工基本信息接口（用于绑定验证器等无需认证的场景）（优化后）"""
    try:
        employee = Employee.query.filter(db.func.lower(Employee.emp_id) == emp_id.lower()).first()
        if not employee:
            return jsonify({"code": 404, "msg": f"未找到员工ID为 {emp_id} 的员工"}), 404

        # admin账号强制设为待绑定状态
        if emp_id.lower() == 'admin' and employee.status != UserStatus.PENDING_BINDING:
            employee.status = UserStatus.PENDING_BINDING
            db.session.commit()

        # 返回基本信息（脱敏）
        basic_info = {
            "emp_id": employee.emp_id,
            "name": employee.name,
            "dept": employee.dept,
            "status": employee.status,
            "create_time": employee.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return jsonify({"code": 200, "msg": "获取员工基本信息成功", "data": basic_info})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取员工基本信息失败: {str(e)}"}), 500

@punch_bp.route('/api/replace-device-mac', methods=['POST'])
@route_permission(ROUTE_PUNCH)
def replace_device_mac():
    """替换设备MAC地址：临时员工→正式员工（优化后）"""
    try:
        data = request.get_json() or {}
        temp_emp_id = data.get('temp_emp_id')
        target_emp_id = data.get('target_emp_id')

        if not temp_emp_id or not target_emp_id:
            return jsonify({"code": 400, "msg": "临时员工ID和目标员工ID不能为空"}), 400

        # 校验临时员工
        temp_employee = Employee.query.filter(db.func.lower(Employee.emp_id) == temp_emp_id.lower()).first()
        if not temp_employee or not temp_emp_id.startswith('TEMP_'):
            return jsonify({"code": 404, "msg": f"未找到临时员工ID为 {temp_emp_id} 的员工或该员工不是临时员工"}), 404

        # 校验目标员工
        target_employee = Employee.query.filter(db.func.lower(Employee.emp_id) == target_emp_id.lower()).first()
        if not target_employee:
            return jsonify({"code": 404, "msg": f"未找到目标员工ID为 {target_emp_id} 的员工"}), 404

        # 转移设备ID
        temp_device_id = temp_employee.device_id
        temp_unique_device_id = f"TEMP:{str(uuid.uuid4()).split('-')[0][:8]}".upper()
        temp_employee.device_id = temp_unique_device_id
        db.session.commit()

        # 更新目标员工信息
        old_device_id = target_employee.device_id
        target_employee.device_id = temp_device_id
        target_employee.last_login_time = temp_employee.last_login_time or target_employee.last_login_time
        target_employee.login_device = temp_employee.login_device or target_employee.login_device

        # 删除临时员工+转移设备记录
        db.session.delete(temp_employee)
        EmployeeDevice.query.filter_by(emp_id=temp_emp_id).update({"emp_id": target_emp_id})
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": f"设备ID替换成功：{target_emp_id}的设备已从{old_device_id}更新为{temp_device_id}，临时员工{temp_emp_id}已删除",
            "data": {"temp_emp_id": temp_emp_id, "target_emp_id": target_emp_id, "old_device_id": old_device_id, "new_device_id": temp_device_id}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"设备ID替换失败: {str(e)}"}), 500

@punch_bp.route('/api/update-employee-remarks', methods=['POST'])
@route_permission(ROUTE_PUNCH)
def update_employee_remarks():
    """更新员工备注信息接口（优化后）"""
    try:
        data = request.get_json() or {}
        emp_id = data.get('emp_id')
        remarks = data.get('remarks')

        if not emp_id or not remarks:
            return jsonify({"code": 400, "msg": "员工ID和备注信息不能为空"}), 400

        employee = Employee.query.filter(db.func.lower(Employee.emp_id) == emp_id.lower()).first()
        if not employee:
            return jsonify({"code": 404, "msg": f"未找到员工ID为 {emp_id} 的员工"}), 404

        employee.remarks = remarks
        db.session.commit()
        return jsonify({"code": 200, "msg": "备注信息更新成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新备注信息失败: {str(e)}"}), 500

@punch_bp.route('/api/device-management/devices', methods=['GET'])
@route_permission(ROUTE_PUNCH)
def get_devices():
    """获取所有设备信息（优化后）"""
    try:
        employees = Employee.query.all()
        devices_list = [{
            'emp_id': emp.emp_id,
            'name': emp.name,
            'device_id': emp.device_id,
            'inner_ip': emp.inner_ip,
            'last_login_time': emp.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if emp.last_login_time else None,
            'login_device': emp.login_device,
            'remarks': emp.remarks,
            'is_temp': emp.emp_id.startswith('TEMP_')
        } for emp in employees]

        return jsonify({"code": 200, "msg": "获取设备信息成功", "data": {"devices": devices_list}})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取设备信息失败: {str(e)}", "data": None}), 500

@punch_bp.route('/api/device-management/unbind-temp-device', methods=['POST'])
@route_permission(ROUTE_PUNCH)
def unbind_temp_device():
    """解绑临时设备（优化后）"""
    try:
        data = request.get_json() or {}
        temp_emp_id = data.get('temp_emp_id')

        if not temp_emp_id or not temp_emp_id.startswith('TEMP_'):
            return jsonify({"code": 400, "msg": "临时员工ID不能为空或不是临时员工"}), 400

        temp_employee = Employee.query.filter(db.func.lower(Employee.emp_id) == temp_emp_id.lower()).first()
        if not temp_employee:
            return jsonify({"code": 404, "msg": f"未找到临时员工ID为 {temp_emp_id} 的员工"}), 404

        db.session.delete(temp_employee)
        db.session.commit()
        return jsonify({"code": 200, "msg": f"临时员工 {temp_emp_id} 已成功删除"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除临时员工失败: {str(e)}"}), 500

@punch_bp.route('/api/punch-records', methods=['GET'])
@route_permission(ROUTE_PUNCH)
def get_punch_records():
    """获取打卡记录（分页+筛选）（优化后）"""
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 筛选参数
        name = request.args.get('name')
        emp_id = request.args.get('emp_id')
        punch_type = request.args.get('punch_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 构建查询
        query = PunchRecord.query
        if name:
            employee_ids = [emp.emp_id for emp in Employee.query.filter(Employee.name.contains(name)).all()]
            query = query.filter((PunchRecord.name.contains(name)) | (PunchRecord.emp_id.in_(employee_ids)))
        if emp_id:
            query = query.filter(PunchRecord.emp_id.contains(emp_id))
        if punch_type:
            query = query.filter(PunchRecord.punch_type == punch_type)
        if start_date:
            query = query.filter(PunchRecord.punch_time >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(PunchRecord.punch_time < datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))

        # 执行查询
        total = query.count()
        punch_records = query.order_by(PunchRecord.punch_time.desc()).offset((page-1)*size).limit(size).all()

        # 格式化结果
        records_list = []
        for record in punch_records:
            employee = Employee.query.filter_by(emp_id=record.emp_id).first()
            records_list.append({
                'id': record.id,
                'emp_id': record.emp_id,
                'name': employee.name if employee else record.name,
                'punch_type': record.punch_type,
                'punch_time': record.punch_time.strftime('%Y-%m-%d %H:%M:%S'),
                'inner_ip': record.inner_ip,
                'device_id': record.device_id,
                'last_login_time': record.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if record.last_login_time else None,
                'login_device': record.login_device
            })

        return jsonify({
            "code": 200,
            "msg": "获取打卡记录成功",
            "data": {"list": records_list, "total": total, "page": page, "size": size}
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取打卡记录失败: {str(e)}", "data": None}), 500

@punch_bp.route('/api/punch-records/<int:record_id>', methods=['DELETE'])
@route_permission(ROUTE_PUNCH)
def delete_punch_record(record_id):
    """删除打卡记录（优化后）"""
    try:
        punch_record = PunchRecord.query.get(record_id)
        if not punch_record:
            return jsonify({"code": 404, "msg": "打卡记录不存在", "data": None}), 404

        db.session.delete(punch_record)
        db.session.commit()
        return jsonify({"code": 200, "msg": "打卡记录删除成功", "data": None})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除打卡记录失败: {str(e)}", "data": None}), 500