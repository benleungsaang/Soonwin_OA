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

# ===================== 蓝图初始化 =====================
punch_bp = Blueprint('punch', __name__)

# ===================== 通用配置与常量 =====================
MOBILE_KEYWORDS = ['mobile', 'android', 'iphone', 'ipad', 'tablet', 'phone', 'ios', 'blackberry', 'windows phone', 'opera mini', 'mobile safari', 'mobile web', 'phone', 'android mobile', 'iphone os']
INNER_NET_PREFIXES = ('192.168.', '10.', '127.')
PUNCH_TIME_RANGES = {
    '上班打卡': (6, 12),
    '下班打卡': (12, 22),
    '非打卡时间打卡': (22, 6)
}
# 是否要求打卡必须在内网环境下进行
REQUIRE_INNER_NET_PUNCH = False  # 设置为False允许外网打卡
# 是否要求打卡必须使用移动设备
REQUIRE_MOBILE_DEVICE_PUNCH = True  # 设置为True强制要求使用移动设备打卡

# ===================== 基础工具函数 =====================
def get_server_ip():
    """自动获取当前服务器内网IP（UDP连接方式）"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def is_inner_net(ip):
    """检查IP是否为内网IP（192.168/10/127段）"""
    return ip.startswith(INNER_NET_PREFIXES)

def is_mobile_device(user_agent=None):
    """检测是否为移动设备（基于User-Agent）"""
    user_agent = user_agent or request.headers.get('User-Agent', '')
    user_agent_lower = user_agent.lower()
    return any(keyword.lower() in user_agent_lower for keyword in MOBILE_KEYWORDS)

def get_client_info():
    """统一获取客户端信息：设备ID + IP地址"""
    # 获取IP地址（优先X-Forwarded-For）
    forwarded = request.headers.get('X-Forwarded-For')
    user_ip = forwarded.split(',')[0].strip() if forwarded else request.remote_addr

    # 获取设备ID（优先JSON请求体，其次请求头）
    device_id = None
    if request.is_json:
        device_id = request.json.get('device_id')
    if not device_id:
        device_id = request.headers.get('X-Device-ID')

    return device_id, user_ip

def detect_device_info(user_agent=None):
    """解析设备信息：设备类型/操作系统/浏览器"""
    user_agent = user_agent or request.headers.get('User-Agent', '').lower()

    # 1. 解析操作系统
    os_info = _parse_os_info(user_agent)
    # 2. 解析设备类型
    device_type = _parse_device_type(user_agent)
    # 3. 解析浏览器
    browser = _parse_browser_info(user_agent)

    return f"{device_type}/{os_info}/{browser}"

def _parse_os_info(user_agent):
    """内部函数：解析操作系统信息"""
    if 'windows nt 10.0' in user_agent:
        return "Windows 10"
    elif 'windows nt 11.0' in user_agent:
        return "Windows 11"
    elif 'windows nt' in user_agent:
        win_match = re.search(r'windows nt (\d+\.\d+)', user_agent)
        return f"Windows {win_match.group(1)}" if win_match else "Windows"
    elif 'mac os x' in user_agent:
        mac_match = re.search(r'mac os x (\d+[._]\d+)', user_agent)
        return f"macOS {mac_match.group(1).replace('_', '.')}" if mac_match else "macOS"
    elif 'android' in user_agent:
        android_match = re.search(r'android[ /](\d+)', user_agent)
        return f"Android {android_match.group(1)}" if android_match else "Android"
    elif 'ipad' in user_agent:
        return "iPad"
    elif 'iphone' in user_agent:
        return "iPhone"
    elif 'linux' in user_agent:
        return "Linux"
    return "未知系统"

def _parse_device_type(user_agent):
    """内部函数：解析设备类型"""
    if any(keyword in user_agent for keyword in MOBILE_KEYWORDS):
        return "移动设备"
    elif 'tablet' in user_agent:
        return "平板设备"
    return "PC"

def _parse_browser_info(user_agent):
    """内部函数：解析浏览器信息"""
    if 'headlesschrome' in user_agent:
        chrome_match = re.search(r'chrome/(\d+)', user_agent)
        return f"HeadlessChrome {chrome_match.group(1)}" if chrome_match else "HeadlessChrome"
    elif 'edg' in user_agent:
        edge_match = re.search(r'edg[ /](\d+)', user_agent)
        return f"Edge {edge_match.group(1)}" if edge_match else "Edge"
    elif 'chrome' in user_agent and 'edg' not in user_agent and 'opr' not in user_agent and 'whale' not in user_agent:
        chrome_match = re.search(r'chrome/(\d+)', user_agent)
        return f"Chrome {chrome_match.group(1)}" if chrome_match else "Chrome"
    elif 'safari' in user_agent and 'chrome' not in user_agent and 'android' not in user_agent:
        safari_match = re.search(r'version/(\d+)', user_agent)
        return f"Safari {safari_match.group(1)}" if safari_match else "Safari"
    return "未知浏览器"

def get_punch_type():
    """根据当前时间判断打卡类型"""
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        return "上班打卡"
    elif 12 <= current_hour < 22:
        return "下班打卡"
    return "非打卡时间打卡"

# ===================== 数据库操作函数 =====================
def get_employee_by_id(emp_id):
    """根据员工ID查询员工信息（大小写不敏感）"""
    return Employee.query.filter(db.func.lower(Employee.emp_id) == emp_id.lower()).first()

def bind_device(emp_id, device_id):
    """绑定设备到员工，返回(是否成功, 提示信息)"""
    employee = get_employee_by_id(emp_id)
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

def validate_employee_device(emp_id, device_id):
    """验证员工设备合法性，返回(是否合法, 提示信息)"""
    if not device_id:
        return False, "设备ID未提供，请首次打卡以绑定设备"

    employee = get_employee_by_id(emp_id)
    if not employee:
        return False, "员工不存在"

    # 设备ID匹配
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

def create_punch_record_entry(employee, punch_type, user_ip, device_id, device_info):
    """创建打卡记录并更新员工信息"""
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

# ===================== 认证与权限校验函数 =====================
def validate_jwt_token(token):
    """验证JWT令牌，返回(是否有效, 载荷/错误信息)"""
    if not token:
        return False, "需要认证才能访问员工信息"

    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, "令牌已过期"
    except jwt.InvalidTokenError:
        return False, "无效的令牌"

def check_employee_permission(payload, target_emp_id):
    """检查员工信息访问权限"""
    current_emp_id = payload['emp_id']
    current_user_role = payload['user_role']

    # 权限校验：普通用户只能看自己，管理员可看所有
    if current_user_role != 'admin' and current_emp_id != target_emp_id:
        return False, "权限不足，只能查看自己的信息"
    return True, ""

# ===================== 核心业务接口 =====================
@punch_bp.route('/api/device-clock-in', methods=['POST'])
def device_clock_in():
    """打卡核心接口：设备验证、绑定、打卡记录创建"""
    try:
        # 1. 基础参数获取与校验
        data = request.get_json() or {}
        emp_id = data.get('emp_id')
        request_device_change = data.get('request_device_change', False)

        if not emp_id:
            return jsonify({"code": 400, "msg": "员工ID未提供"}), 400

        # 2. 获取客户端信息
        device_id, user_ip = get_client_info()
        user_agent = request.headers.get('User-Agent', '')
        device_info = detect_device_info(user_agent)

        # 3. 网络环境校验
        if REQUIRE_INNER_NET_PUNCH and not is_inner_net(user_ip):
            return jsonify({"code": 403, "msg": "非公司内网设备，禁止打卡！"}), 403

        # 4. 设备类型校验
        if REQUIRE_MOBILE_DEVICE_PUNCH and not is_mobile_device(user_agent):
            print(f"DEBUG: User-Agent: {user_agent}")  # 调试日志，显示实际的User-Agent
            print(f"DEBUG: Is mobile: {is_mobile_device(user_agent)}")  # 调试日志
            return jsonify({"code": 403, "msg": "请使用个人手机进行打卡"}), 403

        # 5. 确定打卡类型
        punch_type = get_punch_type()

        # 6. 设备ID处理逻辑
        if not device_id:
            # 首次打卡：生成新设备ID并绑定
            return _handle_first_punch(emp_id, punch_type, user_ip, device_info)

        # 已有设备ID：验证设备合法性
        is_valid, msg = validate_employee_device(emp_id, device_id)
        if not is_valid:
            return _handle_invalid_device(emp_id, device_id, punch_type, user_ip, device_info, msg, request_device_change)

        # 设备验证成功：创建打卡记录
        employee = get_employee_by_id(emp_id)
        if not employee:
            return jsonify({"code": 404, "msg": "员工未找到"}), 404

        result = create_punch_record_entry(employee, punch_type, user_ip, device_id, device_info)
        return jsonify(result)

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"打卡失败: {str(e)}"}), 500

def _handle_first_punch(emp_id, punch_type, user_ip, device_info):
    """处理首次打卡（无设备ID）"""
    new_device_id = str(uuid.uuid4())
    bind_success, bind_msg = bind_device(emp_id, new_device_id)

    if not bind_success:
        return jsonify({"code": 500, "msg": f"设备绑定失败: {bind_msg}"}), 500

    employee = get_employee_by_id(emp_id)
    if not employee:
        return jsonify({"code": 404, "msg": "员工未找到"}), 404

    result = create_punch_record_entry(employee, punch_type, user_ip, new_device_id, device_info)
    result["msg"] = "首次打卡成功"
    result["data"]["device_id"] = new_device_id
    return jsonify(result)

def _handle_invalid_device(emp_id, device_id, punch_type, user_ip, device_info, msg, request_device_change):
    """处理设备验证失败的情况"""
    # 首次绑定设备（设备未绑定任何员工）
    if "需要绑定设备" in msg:
        return _handle_first_punch(emp_id, punch_type, user_ip, device_info)

    # 设备ID变化：处理更换申请
    elif "设备ID变化" in msg:
        if request_device_change:
            return _handle_device_change_apply(emp_id, punch_type, user_ip, device_id, device_info)
        else:
            return jsonify({
                "code": 200,
                "msg": "设备ID发生变化，请申请更换设备",
                "data": {"emp_id": emp_id, "status": "device_change_required"}
            })

    # 其他验证失败（如设备绑定其他员工）
    else:
        # 检查是否是设备被其他员工绑定的情况，如果是，则返回设备更换申请状态
        if "设备已被员工" in msg and "绑定，请申请更换设备" in msg:
            return jsonify({
                "code": 200,
                "msg": msg,
                "data": {"emp_id": emp_id, "status": "device_change_required"}
            })
        else:
            return jsonify({"code": 403, "msg": msg}), 403

def _handle_device_change_apply(emp_id, punch_type, user_ip, device_id, device_info):
    """处理设备更换申请"""
    employee = get_employee_by_id(emp_id)
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

# ===================== 设备管理接口 =====================
@punch_bp.route('/api/request-device-change', methods=['POST'])
@route_permission(ROUTE_PUNCH)
def request_device_change():
    """提交设备更换申请"""
    try:
        data = request.get_json() or {}
        emp_id = data.get('emp_id')
        new_device_id = data.get('new_device_id')

        if not emp_id or not new_device_id:
            return jsonify({"code": 400, "msg": "员工ID和新设备ID不能为空"}), 400

        employee = get_employee_by_id(emp_id)
        if not employee:
            return jsonify({"code": 404, "msg": "员工未找到"}), 404

        # 检查新设备是否被占用（如果是被自己占用则允许）
        existing_employee = Employee.query.filter_by(device_id=new_device_id).first()
        conflict_info = None
        if existing_employee and existing_employee.emp_id != emp_id:
            conflict_info = f"新设备ID已被员工 {existing_employee.name}({existing_employee.emp_id}) 使用，需要管理员处理冲突"
            # 继续处理，允许创建申请，让管理员处理冲突
        elif existing_employee and existing_employee.emp_id == emp_id:
            # 设备已经是自己的，无需更换
            return jsonify({
                "code": 400,
                "msg": "设备已经是您的设备，无需更换"
            }), 400

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
    """批准设备更换申请"""
    try:
        data = request.get_json() or {}
        request_id = data.get('request_id')

        if not request_id:
            return jsonify({"code": 400, "msg": "申请ID不能为空"}), 400

        punch_record = PunchRecord.query.get(request_id)
        if not punch_record or punch_record.punch_type != "设备更换申请":
            return jsonify({"code": 404, "msg": "未找到设备更换申请"}), 404

        employee = get_employee_by_id(punch_record.emp_id)
        if not employee:
            return jsonify({"code": 404, "msg": "员工未找到"}), 404

        # 检查新设备是否被其他员工绑定，如果有则先解绑
        existing_employee = Employee.query.filter_by(device_id=punch_record.device_id).first()
        old_device_id = employee.device_id
        conflict_employee_info = None
        
        if existing_employee and existing_employee.emp_id != employee.emp_id:
            # 记录冲突员工信息
            conflict_employee_info = {
                "emp_id": existing_employee.emp_id,
                "name": existing_employee.name,
                "old_device_id": existing_employee.device_id
            }
            # 将设备从原员工解绑（设置为None或临时值）
            existing_employee.device_id = None

        # 将设备绑定到申请员工
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
    """拒绝设备更换申请"""
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

@punch_bp.route('/api/device-management/devices', methods=['GET'])
@route_permission(ROUTE_PUNCH)
def get_devices():
    """获取所有设备信息"""
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
    """解绑临时设备"""
    try:
        data = request.get_json() or {}
        temp_emp_id = data.get('temp_emp_id')

        if not temp_emp_id or not temp_emp_id.startswith('TEMP_'):
            return jsonify({"code": 400, "msg": "临时员工ID不能为空或不是临时员工"}), 400

        temp_employee = get_employee_by_id(temp_emp_id)
        if not temp_employee:
            return jsonify({"code": 404, "msg": f"未找到临时员工ID为 {temp_emp_id} 的员工"}), 404

        db.session.delete(temp_employee)
        db.session.commit()
        return jsonify({"code": 200, "msg": f"临时员工 {temp_emp_id} 已成功删除"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除临时员工失败: {str(e)}"}), 500

# ===================== 员工信息管理接口 =====================
@punch_bp.route('/api/employee-info/<emp_id>', methods=['GET'])
@route_permission(ROUTE_PUNCH)
def get_employee_info(emp_id):
    """获取员工详细信息（需要认证）"""
    try:
        # 1. 验证令牌
        token = request.headers.get('Authorization', '').replace("Bearer ", "")
        is_valid, result = validate_jwt_token(token)
        if not is_valid:
            return jsonify({"code": 401, "msg": result, "data": None}), 401

        # 2. 检查权限
        is_allowed, err_msg = check_employee_permission(result, emp_id)
        if not is_allowed:
            return jsonify({"code": 403, "msg": err_msg, "data": None}), 403

        # 3. 查询员工信息
        employee = get_employee_by_id(emp_id)
        if not employee:
            return jsonify({"code": 404, "msg": f"未找到员工ID为 {emp_id} 的员工"}), 404

        return jsonify({"code": 200, "msg": "获取员工信息成功", "data": employee.to_dict()})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取员工信息失败: {str(e)}"}), 500

@punch_bp.route('/api/employee-basic-info/<emp_id>', methods=['GET'])
def get_employee_basic_info(emp_id):
    """获取员工基本信息（无需认证）"""
    try:
        employee = get_employee_by_id(emp_id)
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
    """替换临时员工设备到正式员工"""
    try:
        data = request.get_json() or {}
        temp_emp_id = data.get('temp_emp_id')
        target_emp_id = data.get('target_emp_id')

        if not temp_emp_id or not target_emp_id:
            return jsonify({"code": 400, "msg": "临时员工ID和目标员工ID不能为空"}), 400

        # 校验临时员工
        temp_employee = get_employee_by_id(temp_emp_id)
        if not temp_employee or not temp_emp_id.startswith('TEMP_'):
            return jsonify({"code": 404, "msg": f"未找到临时员工ID为 {temp_emp_id} 的员工或该员工不是临时员工"}), 404

        # 校验目标员工
        target_employee = get_employee_by_id(target_emp_id)
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
    """更新员工备注信息"""
    try:
        data = request.get_json() or {}
        emp_id = data.get('emp_id')
        remarks = data.get('remarks')

        if not emp_id or not remarks:
            return jsonify({"code": 400, "msg": "员工ID和备注信息不能为空"}), 400

        employee = get_employee_by_id(emp_id)
        if not employee:
            return jsonify({"code": 404, "msg": f"未找到员工ID为 {emp_id} 的员工"}), 404

        employee.remarks = remarks
        db.session.commit()
        return jsonify({"code": 200, "msg": "备注信息更新成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新备注信息失败: {str(e)}"}), 500

# ===================== 打卡记录管理接口 =====================
@punch_bp.route('/api/punch-records', methods=['GET'])
@route_permission(ROUTE_PUNCH)
def get_punch_records():
    """获取打卡记录（分页+筛选）"""
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
            employee = get_employee_by_id(record.emp_id)
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
    """删除打卡记录"""
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

# 服务器静态IP全局变量
SERVER_INNER_IP = get_server_ip()