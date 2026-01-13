import subprocess
import re
import json
import socket
from flask import Blueprint, request, jsonify, redirect, Response
from extensions import db
from app.models.employee import Employee
from app.models.punch_record import PunchRecord
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

def generate_device_fingerprint(ip, user_agent=""):
    """
    生成设备指纹，用于唯一标识设备
    在无法获取真实MAC地址的网络环境中，使用IP和User-Agent生成唯一标识符
    """
    import hashlib
    
    # 组合IP地址和User-Agent信息生成哈希
    fingerprint_input = f"{ip}_{user_agent}".encode('utf-8')
    # 使用SHA256生成更安全的哈希值
    hash_obj = hashlib.sha256(fingerprint_input)
    # 取前12个字符（对应MAC地址的长度）
    device_id = hash_obj.hexdigest()[:12]
    # 格式化为MAC地址格式
    formatted_mac = ':'.join([device_id[i:i+2] for i in range(0, 12, 2)])
    return formatted_mac.lower()

def get_mac_by_ip(ip, user_agent=""):
    """根据IP获取MAC地址，如果无法获取则生成设备指纹"""
    try:
        # 首先尝试ping一下目标IP，确保它在ARP表中
        subprocess.run(f"ping -n 1 -w 100 {ip}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 获取完整的ARP表
        res = subprocess.check_output("arp -a", shell=True, encoding="utf-8")
        
        # 查找包含目标IP的行
        for line in res.split('\n'):
            if ip in line and ('dynamic' in line.lower() or 'static' in line.lower()):
                # 在该行中查找MAC地址
                mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                if mac_match:
                    mac_addr = mac_match.group(0).lower()
                    # 验证MAC地址格式
                    if len(mac_addr.replace(':', '')) == 12:
                        return mac_addr
        
        # 如果无法获取真实MAC地址，生成设备指纹
        print(f"无法从ARP表获取IP {ip} 的真实MAC地址，生成设备指纹")
        return generate_device_fingerprint(ip, user_agent)
    except Exception as e:
        print(f"获取MAC地址时出错: {e}")
        # 出错时也生成设备指纹
        return generate_device_fingerprint(ip, user_agent)

def detect_device_info():
    """检测设备信息"""
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # 检测操作系统
    os_info = "未知系统"
    if 'windows' in user_agent:
        os_info = "Windows"
    elif 'macintosh' in user_agent or 'mac os x' in user_agent:
        os_info = "macOS"
    elif 'linux' in user_agent:
        os_info = "Linux"
    elif 'android' in user_agent:
        os_info = "Android"
    elif 'iphone' in user_agent or 'ipad' in user_agent:
        os_info = "iOS"
    
    # 检测设备类型
    device_type = "桌面设备"
    if any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipad']):
        device_type = "移动设备"
    
    # 检测浏览器
    browser = "未知浏览器"
    if 'chrome' in user_agent and 'edg' not in user_agent:
        browser = "Chrome"
    elif 'edg' in user_agent:
        browser = "Edge"
    elif 'firefox' in user_agent:
        browser = "Firefox"
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        browser = "Safari"
    elif 'opera' in user_agent or 'opr' in user_agent:
        browser = "Opera"
    
    return f"{os_info}/{device_type}/{browser}"

def migrate_old_device_info(employee):
    """将旧的设备信息迁移到新表"""
    # 检查是否已经迁移过
    existing_device = EmployeeDevice.query.filter_by(
        emp_id=employee.emp_id,
        device_mac=employee.phone_mac
    ).first()
    
    if not existing_device:
        # 创建设备记录
        device = EmployeeDevice(
            emp_id=employee.emp_id,
            device_mac=employee.phone_mac,
            device_ip=employee.inner_ip,
            device_type="Unknown",
            device_info="Migrated from old system",
            is_primary=True
        )
        db.session.add(device)
        db.session.commit()

def register_device(emp_id, device_mac, device_ip, device_info):
    """注册或更新设备记录"""
    if device_mac == "unknown_mac":
        # 如果无法获取MAC地址，则只记录IP
        return
    
    # 检查设备是否已注册
    device_record = EmployeeDevice.query.filter_by(
        emp_id=emp_id,
        device_mac=device_mac
    ).first()
    
    if device_record:
        # 更新现有记录
        device_record.device_ip = device_ip
        device_record.device_info = device_info
    else:
        # 创建新记录 - 检查是否是该员工的第一个设备，设为首要设备
        is_first_device = EmployeeDevice.query.filter_by(emp_id=emp_id).count() == 0
        device = EmployeeDevice(
            emp_id=emp_id,
            device_mac=device_mac,
            device_ip=device_ip,
            device_type="Unknown",
            device_info=device_info,
            is_primary=is_first_device
        )
        db.session.add(device)
    
    db.session.commit()

@punch_bp.route('/punch', methods=['GET'])
def punch():
    print(request.headers)
    """打卡接口"""
    # 获取真实IP - 先检查X-Forwarded-For头部
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        # X-Forwarded-For可能包含多个IP，取第一个
        user_ip = forwarded.split(',')[0].strip()
    else:
        user_ip = request.remote_addr

    # 1. 内网校验
    if not is_inner_net(user_ip):
        # 外网访问异常处理
        return jsonify({"code": 403, "msg": "非公司内网设备，禁止打卡！"}), 403

    # 2. 获取MAC地址
    user_agent = request.headers.get('User-Agent', '')
    user_mac = get_mac_by_ip(user_ip, user_agent)

    # 获取设备信息
    device_info = detect_device_info()

    # 3. 先检查打卡时间，如果不在打卡时间范围内直接返回错误
    hour = datetime.now().hour
    if 6 <= hour < 12:
        punch_type = "上班打卡"
    elif 12 <= hour < 22:
        punch_type = "下班打卡"
    else:
        # 非打卡时间异常处理        
        punch_type = "避免返回400，临时测试用"
        # return jsonify({"code": 400, "msg": "非打卡时间（6:00-22:00）！"}), 400

    # 4. 检查MAC地址是否已关联到某个员工
    employee = Employee.query.filter_by(phone_mac=user_mac).first()

    # 如果没找到（新设备），创建临时员工
    if not employee:
        # 检查是否已经存在相同MAC的临时员工
        temp_employee = Employee.query.filter(
            Employee.emp_id.like(f'TEMP_%{user_mac.replace(":", "")[-6:]}')
        ).first()
        
        if not temp_employee:
            # 创建新的临时员工记录
            temp_employee = Employee(
                name="临时员工",  # 待管理员修改
                emp_id=f"TEMP_{user_mac.replace(':', '')[-6:]}",
                dept="未分配",
                remarks=f"新设备({user_mac})打卡，需管理员绑定到已有账号",  # 添加明确的备注
                phone_mac=user_mac,
                inner_ip=user_ip
            )
            db.session.add(temp_employee)
            db.session.commit()
            employee = temp_employee
            print(f"为新设备创建临时员工: {temp_employee.emp_id}")
        else:
            employee = temp_employee
    else:
        # 如果找到了员工但IP不同，更新IP（设备可能换了网络）
        if employee.inner_ip != user_ip:
            employee.inner_ip = user_ip

    # 5. 更新员工的登录信息
    current_time = datetime.now()
    employee.last_login_time = current_time
    employee.login_device = device_info

    # 6. 记录存储 - 包含登录信息
    new_punch = PunchRecord(
        emp_id=employee.emp_id,
        name=employee.name,
        punch_type=punch_type,
        punch_time=current_time,
        inner_ip=user_ip,
        phone_mac=user_mac,
        last_login_time=current_time,
        login_device=device_info
    )
    db.session.add(new_punch)
    db.session.commit()

    # 7. 重定向到前端开发服务器（测试阶段）
    punch_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    # 使用固定的前端开发服务器地址（localhost:5173 或实际IP:5173）
    redirect_url = f"http://{SERVER_INNER_IP}:5173/punch-success?name={employee.name}&emp_id={employee.emp_id}&punch_type={punch_type}&punch_time={punch_time_str}"

    # 返回重定向响应（测试阶段，实际部署时可以返回JSON）
    return redirect(redirect_url)


@punch_bp.route('/api/employee-info/<emp_id>', methods=['GET'])
def get_employee_info(emp_id):
    """获取员工信息接口（包含备注字段）"""
    try:
        # 查找员工记录
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        
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


@punch_bp.route('/api/replace-device-mac', methods=['POST'])
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
            
        # 查找临时员工
        temp_employee = Employee.query.filter_by(emp_id=temp_emp_id).first()
        if not temp_employee or not temp_emp_id.startswith('TEMP_'):
            return jsonify({
                "code": 404,
                "msg": f"未找到临时员工ID为 {temp_emp_id} 的员工或该员工不是临时员工"
            }), 404
            
        # 查找目标员工
        target_employee = Employee.query.filter_by(emp_id=target_emp_id).first()
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
            
        # 查找员工记录
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        
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


@punch_bp.route('/api/punch-records', methods=['GET'])
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
