from flask import Blueprint, request, jsonify
from extensions import db
from app.models.inquiry import Inquiry, InquiryCommunication
from app.models.totp_user import TotpUser
from app.models.employee import Employee
from app.models.business_operation_log import BusinessOperationLog, add_inquiry_log
from app.models.data_change_stats import DataChangeStats
from app.models.simple_permission import get_user_role_from_token
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_INQUIRY
from datetime import datetime, timedelta
import json
from functools import wraps

def get_user_id_from_token():
    """从JWT token中获取用户ID信息（兼容现有系统）"""
    from flask import request
    import jwt
    import config
    from app.models.employee import Employee
    
    token = request.headers.get('Authorization')
    if not token:
        return None

    # 移除 "Bearer " 前缀
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        # 解码JWT令牌
        payload = jwt.decode(token, config.Config.JWT_SECRET_KEY, algorithms=['HS256'])
        emp_id = payload['emp_id']
        return emp_id

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

# 创建蓝图
inquiry_bp = Blueprint('inquiry', __name__)

def get_current_user():
    """获取当前用户信息的辅助函数"""
    emp_id = get_user_id_from_token()
    user_role = get_user_role_from_token()
    user_name = "system"  # 默认名称
    
    # 尝试从数据库获取用户信息以获取真实姓名
    if emp_id:
        from app.models.employee import Employee
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if employee:
            user_name = employee.name
    
    # 创建模拟用户对象
    current_user = type('User', (), {
        'emp_id': emp_id,
        'user_role': user_role,
        'name': user_name
    })()
    
    return current_user



def create_inquiry_log(inquiry_id, operation_type, operator_id, details="", inquiry_obj=None, communication_obj=None):
    """创建询盘操作日志，不包含统计信息"""
    # 获取公司名称
    company_name = None
    if inquiry_obj:
        company_name = inquiry_obj.company_name
    elif communication_obj:
        company_name = communication_obj.company_name
    elif inquiry_id:
        # 如果没有传入对象但有 inquiry_id，则查询获取公司名称
        inquiry = Inquiry.query.get(inquiry_id)
        if inquiry:
            company_name = inquiry.company_name

    # 将公司名称等操作相关信息整合到 details 中
    details_dict = json.loads(details) if details else {}
    details_dict.update({
        "company_name": company_name
    })

    # 使用新的通用日志函数
    add_inquiry_log(
        inquiry_id=inquiry_id,
        operation_type=operation_type,
        operator_id=operator_id,
        details=details_dict
    )


@inquiry_bp.route('/inquiries', methods=['GET'])
@route_permission(ROUTE_INQUIRY)
def get_inquiries():
    """获取询盘列表，支持分页和筛选"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 获取筛选参数
        search = request.args.get('search')  # 新增的综合搜索参数
        area = request.args.get('area')
        contact_person = request.args.get('contact_person')
        company_name = request.args.get('company_name')
        packaging_product = request.args.get('packaging_product')
        machine_type = request.args.get('machine_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        inquiry_source = request.args.get('inquiry_source')

        # 获取当前用户信息
        current_user = get_current_user()

        # 初始化查询对象
        query = Inquiry.query

        # 检查是否为管理员，如果不是管理员则只查询自己创建的数据
        if current_user.user_role != 'admin':
            query = query.filter(Inquiry.creator_id == current_user.emp_id)

        # 应用综合搜索条件（使用新的search_field字段）
        if search:
            query = query.filter(Inquiry.search_field.contains(search))
        else:
            # 如果没有综合搜索，则应用单独的筛选条件
            if area:
                query = query.filter(Inquiry.area.contains(area))
            if contact_person:
                query = query.filter(Inquiry.contact_person.contains(contact_person))
            if company_name:
                query = query.filter(Inquiry.company_name.contains(company_name))
            if packaging_product:
                query = query.filter(Inquiry.packaging_product.contains(packaging_product))
            if machine_type:
                query = query.filter(Inquiry.machine_type.contains(machine_type))
            if inquiry_source:
                query = query.filter(Inquiry.inquiry_source.contains(inquiry_source))

        # 应用日期范围筛选（独立于内容搜索）
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Inquiry.inquiry_date >= start_datetime)
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Inquiry.inquiry_date <= end_datetime)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        inquiries = query.order_by(Inquiry.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 序列化询盘数据
        inquiries_list = [inquiry.to_dict() for inquiry in inquiries]

        # 返回统一格式的数据
        response_data = {
            "code": 200,
            "msg": "获取询盘列表成功",
            "data": {
                "list": inquiries_list,
                "total": total,
                "page": page,
                "size": size
            }
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取询盘列表失败: {str(e)}",
            "data": None
        }), 500


# 其余代码保持不变...