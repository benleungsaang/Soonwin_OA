import subprocess
import re
import json
from flask import Blueprint, request, jsonify, redirect, Response
from extensions import db
from app.models.employee import Employee
from app.models.punch_record import PunchRecord
from datetime import datetime, timedelta



# ===================== 这里是全局变量插入位置 =====================
# 定义服务器静态IP全局变量（你的服务器固定内网IP，按需修改即可）
SERVER_INNER_IP = "192.168.30.53"
# =================================================================



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
    # from datetime import timedelta
    # time_threshold = datetime.now() - timedelta(minutes=30)
    # last_punch = PunchRecord.query.filter(
    #     PunchRecord.emp_id == employee.emp_id,
    #     PunchRecord.punch_type == punch_type,
    #     PunchRecord.punch_time > time_threshold
    # ).order_by(PunchRecord.punch_time.desc()).first()

    # if last_punch:
    #     # 重复打卡异常处理
    #     return jsonify({"code": 400, "msg": f"30分钟内已完成{punch_type}，无需重复打卡！"}), 400

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
    # 使用固定的前端开发服务器地址（localhost:5173 或实际IP:5173）
    redirect_url = f"http://{SERVER_INNER_IP}:5173/punch-success?name={employee.name}&emp_id={employee.emp_id}&punch_type={punch_type}&punch_time={punch_time_str}"

    # 返回重定向响应（测试阶段，实际部署时可以返回JSON）
    return redirect(redirect_url)


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
            query = query.filter(PunchRecord.name.contains(name))
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
            records_list.append({
                'id': record.id,
                'emp_id': record.emp_id,
                'name': record.name,
                'punch_type': record.punch_type,
                'punch_time': record.punch_time.strftime('%Y-%m-%d %H:%M:%S'),
                'inner_ip': record.inner_ip,
                'phone_mac': record.phone_mac
            })
        
        # 使用json.dumps确保中文正确显示
        import json
        from datetime import timedelta
        response_data = {
            "code": 200,
            "msg": "获取打卡记录成功",
            "data": records_list,
            "total": total,
            "page": page,
            "size": size
        }
        return Response(
            json.dumps(response_data, ensure_ascii=False, separators=(',', ':')),
            mimetype='application/json; charset=utf-8'
        )
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取打卡记录失败: {str(e)}"
        }), 500
