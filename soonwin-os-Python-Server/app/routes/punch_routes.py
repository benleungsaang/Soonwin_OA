import subprocess
import re
from flask import Blueprint, request, jsonify, redirect
from extensions import db
from app.models.employee import Employee
from app.models.punch_record import PunchRecord
from datetime import datetime

# 创建蓝图
punch_bp = Blueprint('punch', __name__)

def is_inner_net(ip):
    """检查IP是否为内网IP"""
    return ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.')

def get_mac_by_ip(ip):
    """根据IP获取MAC地址"""
    try:
        res = subprocess.check_output(f"arp -a {ip}", shell=True, encoding="utf-8")
        # 查找MAC地址模式
        mac_matches = re.findall(r'([0-9A-Fa-f]{2}([-:])){5}([0-9A-Fa-f]{2})', res)
        if mac_matches:
            # 确保获取完整MAC地址
            for line in res.split('\n'):
                if ip in line and 'dynamic' in line.lower():
                    parts = line.split()
                    for part in parts:
                        if re.match(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', part):
                            return part.lower()
        return "unknown_mac"
    except:
        return "unknown_mac"

@punch_bp.route('/punch', methods=['GET'])
def punch():
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
    user_mac = get_mac_by_ip(user_ip)
    
    # 3. 检查是否已有对应MAC地址的员工记录
    employee = Employee.query.filter_by(phone_mac=user_mac).first()
    
    # 如果没有找到对应MAC地址的员工记录，检查是否IP已存在
    if not employee:
        employee = Employee.query.filter_by(inner_ip=user_ip).first()
        
        # 如果MAC和IP都未记录，则创建一个新的临时员工记录
        if not employee:
            # 创建临时员工记录（待管理员后续绑定）
            temp_employee = Employee(
                name="临时员工",  # 待管理员修改
                emp_id=f"TEMP_{user_mac.replace(':', '')[-6:]}",
                dept="未分配",
                phone_mac=user_mac,
                inner_ip=user_ip
            )
            db.session.add(temp_employee)
            db.session.commit()
            employee = temp_employee
    
    # 4. 打卡类型判断
    hour = datetime.now().hour
    if 6 <= hour < 12:
        punch_type = "上班打卡"
    elif 12 <= hour < 22:
        punch_type = "下班打卡"
    else:
        # 非打卡时间异常处理
        return jsonify({"code": 400, "msg": "非打卡时间（6:00-22:00）！"}), 400
    
    # 5. 重复打卡限制（30分钟内）
    from datetime import timedelta
    time_threshold = datetime.now() - timedelta(minutes=30)
    last_punch = PunchRecord.query.filter(
        PunchRecord.emp_id == employee.emp_id,
        PunchRecord.punch_type == punch_type,
        PunchRecord.punch_time > time_threshold
    ).order_by(PunchRecord.punch_time.desc()).first()
    
    if last_punch:
        # 重复打卡异常处理
        return jsonify({"code": 400, "msg": f"30分钟内已完成{punch_type}，无需重复打卡！"}), 400
    
    # 6. 记录存储
    new_punch = PunchRecord(
        emp_id=employee.emp_id,
        name=employee.name,
        punch_type=punch_type,
        punch_time=datetime.now(),
        inner_ip=user_ip,
        phone_mac=user_mac
    )
    db.session.add(new_punch)
    db.session.commit()
    
    # 7. 重定向到前端开发服务器（测试阶段）
    punch_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 使用当前服务器IP地址，根据实际请求IP来确定
    redirect_url = f"http://{user_ip}:5173/punch-success?name={employee.name}&emp_id={employee.emp_id}&punch_type={punch_type}&punch_time={punch_time_str}"
    
    # 返回重定向响应（测试阶段，实际部署时可以返回JSON）
    return redirect(redirect_url)
