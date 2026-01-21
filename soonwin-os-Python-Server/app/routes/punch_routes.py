import re
import json
import socket
import uuid
import jwt
import config
from flask import Blueprint, request, jsonify, redirect, Response
from extensions import db
from app.models.employee import Employee
from app.models.employee_device import EmployeeDevice
from app.models.punch_record import PunchRecord
from app.utils.auth_utils import require_admin, require_auth
from datetime import datetime, timedelta



# ===================== 这里是全局变量插入位置 =====================
# 定义服务器静态IP全局变量（自动获取当前服务器IP）
def get_server_ip():
    try:
        # 创建一个UDP连接来获取本机IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 连接到一个远程地址（不会实际发送数据）
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        return ip
    except Exception:
        # 如果获取失败，回退到localhost
        return "127.0.0.1"

SERVER_INNER_IP = get_server_ip()
# =================================================================



# 创建蓝图
punch_bp = Blueprint('punch', __name__)

def is_inner_net(ip):
    """检查IP是否为内网IP"""
    return ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.')

def get_client_device_identifier():
    """获取客户端设备的唯一标识符，从请求中获取前端存储的设备ID"""
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        user_ip = forwarded.split(',')[0].strip()
    else:
        user_ip = request.remote_addr
    
    # 从请求头或请求体中获取设备ID
    device_id = request.headers.get('X-Device-ID') or request.json.get('device_id') if request.json else None
    
    # 如果没有提供设备ID，返回None表示这是首次打卡
    if not device_id:
        return None, user_ip
    
    return device_id, user_ip

def detect_device_info():
    """检测设备信息，返回格式: 设备类型/操作系统/浏览器"""
    user_agent = request.headers.get('User-Agent', '')
    
    # 检测操作系统
    os_info = "未知系统"
    if 'windows nt 10.0' in user_agent.lower():
        os_info = "Windows 10"
    elif 'windows nt 11.0' in user_agent.lower():
        os_info = "Windows 11"
    elif 'windows nt' in user_agent.lower():
        # 提取Windows版本
        import re
        win_match = re.search(r'windows nt (\d+\.\d+)', user_agent, re.IGNORECASE)
        if win_match:
            os_info = f"Windows {win_match.group(1)}"
        else:
            os_info = "Windows"
    elif 'mac os x' in user_agent.lower():
        # 提取macOS版本
        import re
        mac_match = re.search(r'mac os x (\d+[._]\d+)', user_agent, re.IGNORECASE)
        if mac_match:
            version = mac_match.group(1).replace('_', '.')
            os_info = f"macOS {version}"
        else:
            os_info = "macOS"
    elif 'android' in user_agent.lower():
        # 提取Android版本
        import re
        android_match = re.search(r'android[ /](\d+)', user_agent, re.IGNORECASE)
        if android_match:
            os_info = f"Android {android_match.group(1)}"
        else:
            os_info = "Android"
    elif 'iphone' in user_agent.lower() or 'ipad' in user_agent.lower():
        # 检查是否iPad
        if 'ipad' in user_agent.lower():
            os_info = "iPad"
        else:
            os_info = "iPhone"
    elif 'linux' in user_agent.lower():
        os_info = "Linux"
    
    # 检测设备类型
    device_type = "PC"
    if any(mobile in user_agent.lower() for mobile in ['mobile', 'android', 'iphone', 'ipad']):
        device_type = "移动设备"
    elif 'tablet' in user_agent.lower():
        device_type = "平板设备"
    
    # 检测浏览器 - 按优先级顺序检测
    browser = "未知浏览器"
    
    # 特殊检测：HeadlessChrome
    if 'headlesschrome' in user_agent.lower():
        import re
        chrome_match = re.search(r'chrome/(\d+)', user_agent, re.IGNORECASE)
        if chrome_match:
            browser = f"HeadlessChrome {chrome_match.group(1)}"
        else:
            browser = "HeadlessChrome"
    # Edge浏览器检测
    elif 'edg' in user_agent.lower():
        import re
        edge_match = re.search(r'edg[ /](\d+)', user_agent, re.IGNORECASE)
        if edge_match:
            browser = f"Edge {edge_match.group(1)}"
        else:
            browser = "Edge"
    # Chrome浏览器检测（必须在Safari检测之前，且排除Edge和Opera）
    elif 'chrome' in user_agent.lower() and 'edg' not in user_agent.lower() and 'opr' not in user_agent.lower() and 'whale' not in user_agent.lower():
        import re
        chrome_match = re.search(r'chrome/(\d+)', user_agent, re.IGNORECASE)
        if chrome_match:
            browser = f"Chrome {chrome_match.group(1)}"
        else:
            browser = "Chrome"
    # Firefox浏览器检测
    elif 'firefox' in user_agent.lower():
        import re
        firefox_match = re.search(r'firefox/(\d+)', user_agent, re.IGNORECASE)
        if firefox_match:
            browser = f"Firefox {firefox_match.group(1)}"
        else:
            browser = "Firefox"
    # Safari浏览器检测（Safari的User-Agent中通常包含Safari但不包含Chrome）
    elif 'safari' in user_agent.lower() and 'chrome' not in user_agent.lower() and 'android' not in user_agent.lower():
        import re
        safari_match = re.search(r'version/(\d+)', user_agent, re.IGNORECASE)
        if safari_match:
            browser = f"Safari {safari_match.group(1)}"
        else:
            browser = "Safari"
    # Opera浏览器检测
    elif 'opera' in user_agent.lower() or 'opr' in user_agent.lower():
        import re
        opera_match = re.search(r'(?:opera|opr)[ /](\d+)', user_agent, re.IGNORECASE)
        if opera_match:
            browser = f"Opera {opera_match.group(1)}"
        else:
            browser = "Opera"
    # Internet Explorer检测
    elif 'msie' in user_agent.lower() or 'trident' in user_agent.lower():
        browser = "Internet Explorer"
    
    return f"{device_type}/{os_info}/{browser}"

def detect_device_info():
    """检测设备信息，返回格式: 设备类型/操作系统/浏览器"""
    user_agent = request.headers.get('User-Agent', '')
    
    # 检测操作系统
    os_info = "未知系统"
    if 'windows nt 10.0' in user_agent.lower():
        os_info = "Windows 10"
    elif 'windows nt 11.0' in user_agent.lower():
        os_info = "Windows 11"
    elif 'windows nt' in user_agent.lower():
        # 提取Windows版本
        import re
        win_match = re.search(r'windows nt (\d+\.\d+)', user_agent, re.IGNORECASE)
        if win_match:
            os_info = f"Windows {win_match.group(1)}"
        else:
            os_info = "Windows"
    elif 'mac os x' in user_agent.lower():
        # 提取macOS版本
        import re
        mac_match = re.search(r'mac os x (\d+[._]\d+)', user_agent, re.IGNORECASE)
        if mac_match:
            version = mac_match.group(1).replace('_', '.')
            os_info = f"macOS {version}"
        else:
            os_info = "macOS"
    elif 'android' in user_agent.lower():
        # 提取Android版本
        import re
        android_match = re.search(r'android[ /](\d+)', user_agent, re.IGNORECASE)
        if android_match:
            os_info = f"Android {android_match.group(1)}"
        else:
            os_info = "Android"
    elif 'iphone' in user_agent.lower() or 'ipad' in user_agent.lower():
        # 检查是否iPad
        if 'ipad' in user_agent.lower():
            os_info = "iPad"
        else:
            os_info = "iPhone"
    elif 'linux' in user_agent.lower():
        os_info = "Linux"
    
    # 检测设备类型
    device_type = "PC"
    if any(mobile in user_agent.lower() for mobile in ['mobile', 'android', 'iphone', 'ipad']):
        device_type = "移动设备"
    elif 'tablet' in user_agent.lower():
        device_type = "平板设备"
    
    # 检测浏览器 - 按优先级顺序检测
    browser = "未知浏览器"
    
    # 特殊检测：HeadlessChrome
    if 'headlesschrome' in user_agent.lower():
        import re
        chrome_match = re.search(r'chrome/(\d+)', user_agent, re.IGNORECASE)
        if chrome_match:
            browser = f"HeadlessChrome {chrome_match.group(1)}"
        else:
            browser = "HeadlessChrome"
    # Edge浏览器检测
    elif 'edg' in user_agent.lower():
        import re
        edge_match = re.search(r'edg[ /](\d+)', user_agent, re.IGNORECASE)
        if edge_match:
            browser = f"Edge {edge_match.group(1)}"
        else:
            browser = "Edge"
    # Chrome浏览器检测（必须在Safari检测之前，且排除Edge和Opera）
    elif 'chrome' in user_agent.lower() and 'edg' not in user_agent.lower() and 'opr' not in user_agent.lower() and 'whale' not in user_agent.lower():
        import re
        chrome_match = re.search(r'chrome/(\d+)', user_agent, re.IGNORECASE)
        if chrome_match:
            browser = f"Chrome {chrome_match.group(1)}"
        else:
            browser = "Chrome"
    # Firefox浏览器检测
    elif 'firefox' in user_agent.lower():
        import re
        firefox_match = re.search(r'firefox/(\d+)', user_agent, re.IGNORECASE)
        if firefox_match:
            browser = f"Firefox {firefox_match.group(1)}"
        else:
            browser = "Firefox"
    # Safari浏览器检测（Safari的User-Agent中通常包含Safari但不包含Chrome）
    elif 'safari' in user_agent.lower() and 'chrome' not in user_agent.lower() and 'android' not in user_agent.lower():
        import re
        safari_match = re.search(r'version/(\d+)', user_agent, re.IGNORECASE)
        if safari_match:
            browser = f"Safari {safari_match.group(1)}"
        else:
            browser = "Safari"
    # Opera浏览器检测
    elif 'opera' in user_agent.lower() or 'opr' in user_agent.lower():
        import re
        opera_match = re.search(r'(?:opera|opr)[ /](\d+)', user_agent, re.IGNORECASE)
        if opera_match:
            browser = f"Opera {opera_match.group(1)}"
        else:
            browser = "Opera"
    # Internet Explorer检测
    elif 'msie' in user_agent.lower() or 'trident' in user_agent.lower():
        browser = "Internet Explorer"
    
    return f"{device_type}/{os_info}/{browser}"

def validate_device_for_employee(emp_id, device_id):
    """验证设备是否已授权给该员工"""
    if not device_id:
        return False, "设备ID未提供，请首次打卡以绑定设备"
    
    # 检查设备ID是否已绑定到该员工
    employee = Employee.query.filter_by(emp_id=emp_id).first()
    if not employee:
        return False, "员工不存在"
    
    # 检查设备ID是否与员工当前的phone_mac匹配（我们使用phone_mac字段存储设备ID）
    if employee.phone_mac == device_id:
        return True, "设备验证成功"
    
    # 检查是否为已知设备但属于其他员工（设备更换申请）
    existing_employee = Employee.query.filter_by(phone_mac=device_id).first()
    if existing_employee and existing_employee.emp_id != emp_id:
        return False, f"设备已被员工 {existing_employee.name}({existing_employee.emp_id}) 绑定，请申请更换设备"
    
    # 检查是否是设备更换请求（当前员工已有设备ID，但这次使用了新设备）
    if employee.phone_mac and employee.phone_mac != device_id:
        return False, "设备ID变化，请申请更换设备"
    
    # 如果设备ID未绑定到任何员工，这是设备绑定请求
    return False, "需要绑定设备"

def bind_device_to_employee(emp_id, device_id):
    """将设备ID绑定到员工"""
    employee = Employee.query.filter_by(emp_id=emp_id).first()
    if not employee:
        return False, "员工不存在"
    
    # 检查该设备ID是否已被其他员工使用
    existing_employee = Employee.query.filter_by(phone_mac=device_id).first()
    if existing_employee and existing_employee.emp_id != emp_id:
        return False, f"设备已绑定到其他员工 {existing_employee.name}({existing_employee.emp_id})"
    
    # 绑定设备ID到员工
    employee.phone_mac = device_id
    db.session.commit()
    return True, "设备绑定成功"

@punch_bp.route('/punch', methods=['GET'])
def punch():
    """打卡接口 - 保持原有GET接口用于重定向"""
    # 从请求头获取设备ID
    device_id = request.headers.get('X-Device-ID')
    user_ip = request.remote_addr

    # 从URL参数中获取员工ID
    emp_id = request.args.get('emp_id')
    if not emp_id:
        return jsonify({"code": 400, "msg": "员工ID未提供"}), 400

    # 1. 内网校验
    if not is_inner_net(user_ip):
        # 外网访问异常处理
        return jsonify({"code": 403, "msg": "非公司内网设备，禁止打卡！"}), 403

    # 获取设备信息
    device_info = detect_device_info()

    # 2. 检查打卡时间
    hour = datetime.now().hour
    if 6 <= hour < 12:
        punch_type = "上班打卡"
    elif 12 <= hour < 22:
        punch_type = "下班打卡"
    else:
        # 非打卡时间异常处理        
        punch_type = "避免返回400，临时测试用"
        # return jsonify({"code": 400, "msg": "非打卡时间（6:00-22:00）！"}), 400

    # 3. 验证设备ID
    is_valid, msg = validate_device_for_employee(emp_id, device_id)
    
    if not is_valid and "需要绑定设备" in msg:
        # 对于GET请求，我们不能绑定新设备ID，需要引导用户使用新的API
        return jsonify({"code": 403, "msg": "设备未绑定，请先通过API进行首次打卡"}), 403
    elif not is_valid:
        # 非法设备或验证失败
        return jsonify({"code": 403, "msg": msg}), 403
    else:
        # 设备验证成功，进行打卡
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return jsonify({"code": 404, "msg": "员工未找到"}), 404

        # 更新员工的登录信息
        current_time = datetime.now()
        employee.last_login_time = current_time
        employee.login_device = device_info

        # 记录打卡
        new_punch = PunchRecord(
            emp_id=employee.emp_id,
            name=employee.name,
            punch_type=punch_type,
            punch_time=current_time,
            inner_ip=user_ip,
            phone_mac=device_id,  # 使用验证通过的设备ID
            last_login_time=current_time,
            login_device=device_info
        )
        db.session.add(new_punch)
        db.session.commit()

        # 重定向到前端开发服务器
        punch_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        redirect_url = f"http://{SERVER_INNER_IP}:5173/punch-success?name={employee.name}&emp_id={employee.emp_id}&punch_type={punch_type}&punch_time={punch_time_str}"

        return redirect(redirect_url)


@punch_bp.route('/api/device-clock-in', methods=['POST'])
def device_clock_in():
    """新的打卡API端点，支持设备ID验证和绑定"""
    try:
        data = request.get_json()
        emp_id = data.get('emp_id')
        device_id = data.get('device_id') or request.headers.get('X-Device-ID')
        request_device_change = data.get('request_device_change', False)  # 是否请求设备更换
        
        if not emp_id:
            return jsonify({"code": 400, "msg": "员工ID未提供"}), 400

        user_ip = request.remote_addr
        # 1. 内网校验
        if not is_inner_net(user_ip):
            return jsonify({"code": 403, "msg": "非公司内网设备，禁止打卡！"}), 403

        # 获取设备信息
        device_info = detect_device_info()

        # 2. 检查打卡时间
        hour = datetime.now().hour
        if 6 <= hour < 12:
            punch_type = "上班打卡"
        elif 12 <= hour < 22:
            punch_type = "下班打卡"
        else:
            punch_type = "非打卡时间打卡"
            # 可以选择是否允许非打卡时间打卡，这里先允许

        # 3. 验证设备ID
        # 如果没有提供设备ID，视为首次打卡
        if not device_id:
            # 首次打卡，生成并绑定设备ID
            new_device_id = str(uuid.uuid4())
            bind_success, bind_msg = bind_device_to_employee(emp_id, new_device_id)
            
            if bind_success:
                employee = Employee.query.filter_by(emp_id=emp_id).first()
                if employee:
                    current_time = datetime.now()
                    employee.last_login_time = current_time
                    employee.login_device = device_info

                    # 记录打卡
                    new_punch = PunchRecord(
                        emp_id=employee.emp_id,
                        name=employee.name,
                        punch_type=punch_type,
                        punch_time=current_time,
                        inner_ip=user_ip,
                        phone_mac=new_device_id,
                        last_login_time=current_time,
                        login_device=device_info
                    )
                    db.session.add(new_punch)
                    db.session.commit()

                    return jsonify({
                        "code": 200, 
                        "msg": "首次打卡成功", 
                        "data": {
                            "device_id": new_device_id,
                            "emp_id": employee.emp_id,
                            "name": employee.name,
                            "punch_type": punch_type,
                            "punch_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                    })
                else:
                    return jsonify({"code": 404, "msg": "员工未找到"}), 404
            else:
                return jsonify({"code": 500, "msg": f"设备绑定失败: {bind_msg}"}), 500
        
        # 如果提供了设备ID，进行验证
        is_valid, msg = validate_device_for_employee(emp_id, device_id)
        
        if not is_valid:
            if "需要绑定设备" in msg:
                # 首次打卡，生成并绑定设备ID
                new_device_id = str(uuid.uuid4())
                bind_success, bind_msg = bind_device_to_employee(emp_id, new_device_id)
                
                if bind_success:
                    employee = Employee.query.filter_by(emp_id=emp_id).first()
                    if employee:
                        current_time = datetime.now()
                        employee.last_login_time = current_time
                        employee.login_device = device_info

                        # 记录打卡
                        new_punch = PunchRecord(
                            emp_id=employee.emp_id,
                            name=employee.name,
                            punch_type=punch_type,
                            punch_time=current_time,
                            inner_ip=user_ip,
                            phone_mac=new_device_id,
                            last_login_time=current_time,
                            login_device=device_info
                        )
                        db.session.add(new_punch)
                        db.session.commit()

                        return jsonify({
                            "code": 200, 
                            "msg": "首次打卡成功", 
                            "data": {
                                "device_id": new_device_id,
                                "emp_id": employee.emp_id,
                                "name": employee.name,
                                "punch_type": punch_type,
                                "punch_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                        })
                    else:
                        return jsonify({"code": 404, "msg": "员工未找到"}), 404
                else:
                    return jsonify({"code": 500, "msg": f"设备绑定失败: {bind_msg}"}), 500
            elif "设备ID变化" in msg and request_device_change:
                # 用户申请更换设备，创建临时打卡记录等待管理员审批
                employee = Employee.query.filter_by(emp_id=emp_id).first()
                if not employee:
                    return jsonify({"code": 404, "msg": "员工未找到"}), 404
                
                current_time = datetime.now()
                employee.last_login_time = current_time
                employee.login_device = device_info

                # 创建待审批的打卡记录
                pending_punch = PunchRecord(
                    emp_id=employee.emp_id,
                    name=employee.name,
                    punch_type=punch_type,
                    punch_time=current_time,
                    inner_ip=user_ip,
                    phone_mac=device_id,  # 使用新设备ID
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
                        "status": "pending_approval"  # 表示需要管理员审批
                    }
                })
            elif "设备ID变化" in msg:
                # 设备ID变化，提示用户申请更换设备
                return jsonify({
                    "code": 403, 
                    "msg": "设备ID发生变化，请申请更换设备", 
                    "data": {
                        "emp_id": emp_id,
                        "status": "device_change_required"
                    }
                })
            else:
                # 非法设备或验证失败
                return jsonify({"code": 403, "msg": msg}), 403
        else:
            # 设备验证成功，进行打卡
            employee = Employee.query.filter_by(emp_id=emp_id).first()
            if not employee:
                return jsonify({"code": 404, "msg": "员工未找到"}), 404

            # 更新员工的登录信息
            current_time = datetime.now()
            employee.last_login_time = current_time
            employee.login_device = device_info

            # 记录打卡
            new_punch = PunchRecord(
                emp_id=employee.emp_id,
                name=employee.name,
                punch_type=punch_type,
                punch_time=current_time,
                inner_ip=user_ip,
                phone_mac=device_id,
                last_login_time=current_time,
                login_device=device_info
            )
            db.session.add(new_punch)
            db.session.commit()

            return jsonify({
                "code": 200, 
                "msg": "打卡成功", 
                "data": {
                    "emp_id": employee.emp_id,
                    "name": employee.name,
                    "punch_type": punch_type,
                    "punch_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
                }
            })
    except Exception as e:
        return jsonify({"code": 500, "msg": f"打卡失败: {str(e)}"}), 500


@punch_bp.route('/api/request-device-change', methods=['POST'])
@require_auth
def request_device_change():
    """请求更换设备的API端点"""
    try:
        data = request.get_json()
        emp_id = data.get('emp_id')
        new_device_id = data.get('new_device_id')
        
        if not emp_id or not new_device_id:
            return jsonify({"code": 400, "msg": "员工ID和新设备ID不能为空"}), 400
            
        # 检查当前员工是否已有设备ID
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return jsonify({"code": 404, "msg": "员工未找到"}), 404
            
        old_device_id = employee.phone_mac
        
        # 检查新设备ID是否已被其他员工使用
        existing_employee = Employee.query.filter_by(phone_mac=new_device_id).first()
        if existing_employee and existing_employee.emp_id != emp_id:
            return jsonify({
                "code": 409, 
                "msg": f"新设备ID已被员工 {existing_employee.name}({existing_employee.emp_id}) 使用"
            }), 409

        # 创建设备更换申请记录
        current_time = datetime.now()
        change_request = PunchRecord(
            emp_id=emp_id,
            name=employee.name,
            punch_type="设备更换申请",
            punch_time=current_time,
            inner_ip=request.remote_addr,
            phone_mac=new_device_id,  # 新设备ID
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
                "old_device_id": old_device_id,
                "new_device_id": new_device_id,
                "request_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending"
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": f"提交设备更换申请失败: {str(e)}"}), 500


@punch_bp.route('/api/approve-device-change', methods=['POST'])
@require_admin
def approve_device_change():
    """管理员批准设备更换申请"""
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        
        if not request_id:
            return jsonify({"code": 400, "msg": "申请ID不能为空"}), 400
            
        # 查找待审批的打卡记录
        punch_record = PunchRecord.query.get(request_id)
        if not punch_record or punch_record.punch_type != "设备更换申请":
            return jsonify({"code": 404, "msg": "未找到设备更换申请"}), 404
            
        # 更新员工的设备ID
        employee = Employee.query.filter_by(emp_id=punch_record.emp_id).first()
        if not employee:
            return jsonify({"code": 404, "msg": "员工未找到"}), 404
            
        old_device_id = employee.phone_mac
        new_device_id = punch_record.phone_mac  # 打卡记录中的phone_mac字段存储的是新设备ID
        
        # 更新员工的设备ID
        employee.phone_mac = new_device_id
        
        # 更新打卡记录状态（可选，标记为已处理）
        punch_record.punch_type = "设备更换已批准"
        
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "设备更换申请已批准",
            "data": {
                "emp_id": employee.emp_id,
                "old_device_id": old_device_id,
                "new_device_id": new_device_id
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": f"批准设备更换申请失败: {str(e)}"}), 500


@punch_bp.route('/api/reject-device-change', methods=['POST'])
@require_admin
def reject_device_change():
    """管理员拒绝设备更换申请"""
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        
        if not request_id:
            return jsonify({"code": 400, "msg": "申请ID不能为空"}), 400
            
        # 查找待审批的打卡记录
        punch_record = PunchRecord.query.get(request_id)
        if not punch_record or punch_record.punch_type != "设备更换申请":
            return jsonify({"code": 404, "msg": "未找到设备更换申请"}), 404
            
        # 删除待审批的打卡记录
        db.session.delete(punch_record)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "设备更换申请已拒绝"
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": f"拒绝设备更换申请失败: {str(e)}"}), 500


@punch_bp.route('/api/employee-info/<emp_id>', methods=['GET'])
def get_employee_info(emp_id):
    """获取员工信息接口（包含备注字段）"""
    try:
        # 从请求头获取认证信息
        token = request.headers.get('Authorization')
        if token and token.startswith("Bearer "):
            token = token[7:]
            try:
                # 解码JWT令牌
                payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
                current_emp_id = payload['emp_id']
                current_user_role = payload['user_role']
                
                # 普通用户只能查看自己的信息，管理员可以查看任意员工信息
                if current_user_role != 'admin' and current_emp_id != emp_id:
                    return jsonify({
                        "code": 403,
                        "msg": "权限不足，只能查看自己的信息",
                        "data": None
                    }), 403
            except jwt.ExpiredSignatureError:
                return jsonify({
                    "code": 401,
                    "msg": "令牌已过期",
                    "data": None
                }), 401
            except jwt.InvalidTokenError:
                return jsonify({
                    "code": 401,
                    "msg": "无效的令牌",
                    "data": None
                }), 401
        else:
            # 如果没有提供token，也只允许查看自己的信息
            return jsonify({
                "code": 401,
                "msg": "需要认证才能访问员工信息",
                "data": None
            }), 401

        # 查找员工记录（使用大小写不敏感的查询）
        emp_id_lower = emp_id.lower()
        employee = Employee.query.filter(db.func.lower(Employee.emp_id) == emp_id_lower).first()
        
        if not employee:
            return jsonify({
                "code": 404,
                "msg": f"未找到员工ID为 {emp_id} 的员工"
            }), 404
            
        return jsonify({
            "code": 200,
            "msg": "获取员工信息成功",
            "data": employee.to_dict()
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取员工信息失败: {str(e)}"
        }), 500


@punch_bp.route('/api/employee-basic-info/<emp_id>', methods=['GET'])
def get_employee_basic_info(emp_id):
    """获取员工基本信息接口（用于绑定验证器等无需认证的场景）"""
    try:
        # 查找员工记录（使用大小写不敏感的查询）
        emp_id_lower = emp_id.lower()
        employee = Employee.query.filter(db.func.lower(Employee.emp_id) == emp_id_lower).first()
        
        if not employee:
            return jsonify({
                "code": 404,
                "msg": f"未找到员工ID为 {emp_id} 的员工"
            }), 404
            
        # 只返回基本信息，不包含敏感信息
        basic_info = {
            "emp_id": employee.emp_id,
            "name": employee.name,
            "dept": employee.dept,
            "status": employee.status,
            "create_time": employee.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return jsonify({
            "code": 200,
            "msg": "获取员工基本信息成功",
            "data": basic_info
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取员工基本信息失败: {str(e)}"
        }), 500


@punch_bp.route('/api/replace-device-mac', methods=['POST'])
@require_admin  # 只有管理员可以替换设备MAC
def replace_device_mac():
    """替换设备MAC地址：将临时员工的设备MAC转移到正式员工，并删除临时员工"""
    try:
        data = request.get_json()
        temp_emp_id = data.get('temp_emp_id')  # 临时员工ID
        target_emp_id = data.get('target_emp_id')  # 目标员工ID
        
        if not temp_emp_id or not target_emp_id:
            return jsonify({
                "code": 400,
                "msg": "临时员工ID和目标员工ID不能为空"
            }), 400
            
        # 查找临时员工（使用大小写不敏感的查询）
        temp_emp_id_lower = temp_emp_id.lower()
        temp_employee = Employee.query.filter(db.func.lower(Employee.emp_id) == temp_emp_id_lower).first()
        if not temp_employee or not temp_emp_id.startswith('TEMP_'):
            return jsonify({
                "code": 404,
                "msg": f"未找到临时员工ID为 {temp_emp_id} 的员工或该员工不是临时员工"
            }), 404
            
        # 查找目标员工（使用大小写不敏感的查询）
        target_emp_id_lower = target_emp_id.lower()
        target_employee = Employee.query.filter(db.func.lower(Employee.emp_id) == target_emp_id_lower).first()
        if not target_employee:
            return jsonify({
                "code": 404,
                "msg": f"未找到目标员工ID为 {target_emp_id} 的员工"
            }), 404
            
        # 获取临时员工的设备MAC
        temp_mac = temp_employee.phone_mac
        
        # 临时修改临时员工的MAC为一个临时值，避免唯一性约束冲突
        import uuid
        temp_unique_mac = f"TEMP:{str(uuid.uuid4()).split('-')[0][:8]}".upper()
        temp_employee.phone_mac = temp_unique_mac
        db.session.commit()
        
        # 保存原目标员工的MAC和登录信息
        old_mac = target_employee.phone_mac
        old_last_login_time = target_employee.last_login_time
        old_login_device = target_employee.login_device
        
        # 将临时员工的MAC、登录信息转移到目标员工
        target_employee.phone_mac = temp_mac
        target_employee.last_login_time = temp_employee.last_login_time or target_employee.last_login_time
        target_employee.login_device = temp_employee.login_device or target_employee.login_device
        
        # 删除临时员工
        db.session.delete(temp_employee)
        
        # 更新相关的设备记录，将临时员工的设备记录转移到目标员工
        temp_devices = EmployeeDevice.query.filter_by(emp_id=temp_emp_id).all()
        for device in temp_devices:
            device.emp_id = target_emp_id
        
        # 提交更改
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": f"设备MAC替换成功：{target_emp_id}的设备已从{old_mac}更新为{temp_mac}，临时员工{temp_emp_id}已删除，登录信息已同步",
            "data": {
                "temp_emp_id": temp_emp_id,
                "target_emp_id": target_emp_id,
                "old_mac": old_mac,
                "new_mac": temp_mac
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"设备MAC替换失败: {str(e)}"
        }), 500


@punch_bp.route('/api/update-employee-remarks', methods=['POST'])
def update_employee_remarks():
    """更新员工备注信息接口"""
    try:
        data = request.get_json()
        emp_id = data.get('emp_id')
        remarks = data.get('remarks')
        
        if not emp_id or not remarks:
            return jsonify({
                "code": 400,
                "msg": "员工ID和备注信息不能为空"
            }), 400
            
        # 查找员工记录（使用大小写不敏感的查询）
        emp_id_lower = emp_id.lower()
        employee = Employee.query.filter(db.func.lower(Employee.emp_id) == emp_id_lower).first()
        
        if not employee:
            return jsonify({
                "code": 404,
                "msg": f"未找到员工ID为 {emp_id} 的员工"
            }), 404
            
        # 更新备注信息
        employee.remarks = remarks
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": "备注信息更新成功"
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"更新备注信息失败: {str(e)}"
        }), 500


@punch_bp.route('/api/device-management/devices', methods=['GET'])
@require_admin  # 只有管理员可以查看设备管理信息
def get_devices():
    """获取所有设备信息，用于设备管理"""
    try:
        # 获取所有员工及其设备信息
        employees = Employee.query.all()
        
        devices_list = []
        for emp in employees:
            devices_list.append({
                'emp_id': emp.emp_id,
                'name': emp.name,
                'phone_mac': emp.phone_mac,
                'inner_ip': emp.inner_ip,
                'last_login_time': emp.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if emp.last_login_time else None,
                'login_device': emp.login_device,
                'remarks': emp.remarks,
                'is_temp': emp.emp_id.startswith('TEMP_')
            })
        
        return jsonify({
            "code": 200,
            "msg": "获取设备信息成功",
            "data": {
                "devices": devices_list
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取设备信息失败: {str(e)}",
            "data": None
        }), 500


@punch_bp.route('/api/device-management/unbind-temp-device', methods=['POST'])
@require_admin  # 只有管理员可以解绑临时设备
def unbind_temp_device():
    """解绑临时设备，删除临时员工记录"""
    try:
        data = request.get_json()
        temp_emp_id = data.get('temp_emp_id')
        
        if not temp_emp_id or not temp_emp_id.startswith('TEMP_'):
            return jsonify({
                "code": 400,
                "msg": "临时员工ID不能为空或不是临时员工"
            }), 400
            
        # 查找临时员工（使用大小写不敏感的查询）
        temp_emp_id_lower = temp_emp_id.lower()
        temp_employee = Employee.query.filter(db.func.lower(Employee.emp_id) == temp_emp_id_lower).first()
        if not temp_employee:
            return jsonify({
                "code": 404,
                "msg": f"未找到临时员工ID为 {temp_emp_id} 的员工"
            }), 404
            
        # 删除临时员工
        db.session.delete(temp_employee)
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": f"临时员工 {temp_emp_id} 已成功删除"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除临时员工失败: {str(e)}"
        }), 500


@punch_bp.route('/api/punch-records', methods=['GET'])
@require_admin  # 只有管理员可以查看打卡记录
def get_punch_records():
    """获取打卡记录接口，支持分页和筛选"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        
        # 获取筛选参数
        name = request.args.get('name')
        emp_id = request.args.get('emp_id')
        punch_type = request.args.get('punch_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询
        query = PunchRecord.query
        
        # 应用筛选条件
        if name:
            # 同时搜索打卡记录中的姓名和关联员工的当前姓名
            employee_ids = [emp.emp_id for emp in Employee.query.filter(Employee.name.contains(name)).all()]
            query = query.filter(
                (PunchRecord.name.contains(name)) | 
                (PunchRecord.emp_id.in_(employee_ids))
            )
        if emp_id:
            query = query.filter(PunchRecord.emp_id.contains(emp_id))
        if punch_type:
            query = query.filter(PunchRecord.punch_type == punch_type)
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(PunchRecord.punch_time >= start_datetime)
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # 包含结束日期的整天
            query = query.filter(PunchRecord.punch_time < end_datetime)
        
        # 计算总数
        total = query.count()
        
        # 应用分页和排序
        punch_records = query.order_by(PunchRecord.punch_time.desc()).offset((page - 1) * size).limit(size).all()
        
        # 将打卡记录转换为字典格式
        records_list = []
        for record in punch_records:
            # 获取关联的员工当前信息
            employee = Employee.query.filter_by(emp_id=record.emp_id).first()
            records_list.append({
                'id': record.id,
                'emp_id': record.emp_id,
                'name': employee.name if employee else record.name,  # 显示当前员工姓名，以反映最新信息
                'punch_type': record.punch_type,
                'punch_time': record.punch_time.strftime('%Y-%m-%d %H:%M:%S'),
                'inner_ip': record.inner_ip,
                'phone_mac': record.phone_mac,
                'last_login_time': record.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if record.last_login_time else None,
                'login_device': record.login_device
            })
        
        # 返回统一格式：将分页信息放在data内
        response_data = {
            "code": 200,
            "msg": "获取打卡记录成功",
            "data": {
                "list": records_list,
                "total": total,
                "page": page,
                "size": size
            }
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取打卡记录失败: {str(e)}",
            "data": None
        }), 500
