from flask import Blueprint, request, jsonify
from extensions import db
from app.models.inquiry import Inquiry, InquiryCommunication
from app.models.inquiry_communication_media import InquiryCommunicationMedia
from app.models.totp_user import TotpUser
from app.models.employee import Employee
from app.models.business_operation_log import BusinessOperationLog, add_inquiry_log
from app.models.data_change_stats import DataChangeStats
from app.models.simple_permission import get_user_role_from_token
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_INQUIRY
from app.utils.auth_utils import get_user_id_from_token
from datetime import datetime, timedelta
import json
import os
import re
import uuid
import logging
from functools import wraps
from werkzeug.utils import secure_filename
from PIL import Image

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
inquiry_bp = Blueprint('inquiry', __name__)

# ------------------------------
# 通用工具函数（提取冗余逻辑）
# ------------------------------
def get_current_user():
    """获取当前用户信息的辅助函数"""
    try:
        from app.models.employee import Employee
        emp_id = get_user_id_from_token()
        user_role = get_user_role_from_token()
        user_name = "system"  # 默认名称

        # 尝试从数据库获取用户真实姓名
        if emp_id:
            employee = Employee.query.filter_by(emp_id=emp_id).first()
            if employee:
                user_name = employee.name

        # 创建模拟用户对象（简化属性访问）
        class CurrentUser:
            def __init__(self, emp_id, user_role, name):
                self.emp_id = emp_id
                self.user_role = user_role or ''  # 防止角色为空
                self.name = name

        return CurrentUser(emp_id, user_role, user_name)
    except Exception as e:
        logger.error(f"获取当前用户信息失败: {str(e)}")
        return None

def validate_email(email):
    """验证邮箱格式"""
    if not email:
        return True
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def check_inquiry_permission(current_user, inquiry, action="access"):
    """
    通用询盘权限校验函数（修正非管理员权限）
    :param current_user: 当前用户对象
    :param inquiry: 询盘对象
    :param action: 操作类型（access/modify/delete）
    :return: (bool, str) 校验结果、错误信息
    """
    # 未登录/用户信息异常
    if not current_user or not current_user.emp_id:
        return False, "未登录或登录状态失效"

    # 管理员拥有全部权限
    if current_user.user_role == 'admin':
        return True, ""

    # 非管理员：可操作「自己创建」或「被分配给自己」的询盘
    if inquiry.creator_id != current_user.emp_id and inquiry.follower_id != current_user.emp_id:
        return False, f"无权限{action}该询盘（仅能操作自己创建或被分配的询盘）"

    return True, ""

def check_communication_permission(current_user, communication):
    """通用沟通记录权限校验函数"""
    if not current_user or not current_user.emp_id:
        return False, "未登录或登录状态失效"

    # 管理员拥有全部权限
    if current_user.user_role == 'admin':
        return True, ""

    # 非管理员：仅能操作自己创建的沟通记录
    if communication.creator_id != current_user.emp_id:
        return False, "无权限操作该沟通记录"

    return True, ""

def create_inquiry_log(inquiry_id, operation_type, operator_id, details="", inquiry_obj=None, communication_obj=None):
    """创建询盘操作日志，不包含统计信息"""
    try:
        # 获取公司名称
        company_name = None
        if inquiry_obj:
            company_name = inquiry_obj.company_name
        elif communication_obj:
            company_name = communication_obj.company_name
        elif inquiry_id:
            inquiry = Inquiry.query.get(inquiry_id)
            if inquiry:
                company_name = inquiry.company_name

        # 整合详情信息
        details_dict = json.loads(details) if isinstance(details, str) else (details or {})
        details_dict.update({"company_name": company_name})

        # 记录日志
        add_inquiry_log(
            inquiry_id=inquiry_id,
            operation_type=operation_type,
            operator_id=operator_id,
            details=details_dict
        )
    except Exception as e:
        logger.error(f"创建询盘日志失败: {str(e)}")

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    ALLOWED_EXTENSIONS = {
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp',  # 图片
        'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v'  # 视频
    }
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_thumbnail(image_path, thumb_path, size=(200, 200)):
    """创建缩略图"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumb_path, "JPEG", quality=70, optimize=True)
        return True
    except Exception as e:
        logger.error(f"创建缩略图失败: {str(e)}")
        return False

# ------------------------------
# 核心接口（统一权限逻辑）
# ------------------------------
@inquiry_bp.route('/inquiries', methods=['GET'])
@route_permission(ROUTE_INQUIRY)
def get_inquiries():
    """获取询盘列表，支持分页和筛选（修正非管理员权限）"""
    try:
        # 获取分页/筛选参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        search = request.args.get('search')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        inquiry_source = request.args.get('inquiry_source')
        include_associated = request.args.get('include_associated', 'true').lower() == 'true'

        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 初始化查询
        query = Inquiry.query

        # 权限过滤：
        # - 管理员：查看全部
        # - 非管理员：查看自己创建 + 被分配的询盘
        if current_user.user_role != 'admin':
            query = query.filter(
                (Inquiry.creator_id == current_user.emp_id) |
                (Inquiry.follower_id == current_user.emp_id)  # 被分配的询盘
            )

        # 搜索条件
        if search:
            query = query.filter(Inquiry.search_field.contains(search))

        # 日期筛选
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Inquiry.inquiry_date >= start_datetime)
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Inquiry.inquiry_date <= end_datetime)

        # 排除已关联订单的询盘
        if not include_associated:
            from app.models.order import Order
            associated_ids = db.session.query(Order.inquiry_id).filter(Order.inquiry_id.isnot(None)).distinct()
            query = query.filter(~Inquiry.id.in_([id[0] for id in associated_ids if id[0]]))

        # 分页查询
        total = query.count()
        inquiries = query.order_by(Inquiry.create_time.desc()).offset((page-1)*size).limit(size).all()

        return jsonify({
            "code": 200,
            "msg": "获取询盘列表成功",
            "data": {
                "list": [i.to_dict() for i in inquiries],
                "total": total,
                "page": page,
                "size": size
            }
        })
    except Exception as e:
        logger.error(f"获取询盘列表失败: {str(e)}")
        return jsonify({"code": 500, "msg": f"获取询盘列表失败: {str(e)}", "data": None}), 500


@inquiry_bp.route('/inquiries', methods=['POST'])
@route_permission(ROUTE_INQUIRY)
def create_inquiry():
    """创建新询盘"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "msg": "请求数据不能为空", "data": None}), 400

        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 校验必填字段
        required_fields = ['area', 'inquiry_date', 'inquiry_source', 'company_name',
                          'contact_person', 'phone', 'email', 'packaging_product', 'machine_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"code": 400, "msg": f"缺少必填字段: {field}", "data": None}), 400

        # 校验邮箱格式
        if not validate_email(data.get('email')):
            return jsonify({"code": 400, "msg": "邮箱格式不正确", "data": None}), 400

        # 创建询盘
        new_inquiry = Inquiry(
            area=data.get('area'),
            inquiry_date=datetime.strptime(data.get('inquiry_date'), '%Y-%m-%d').date(),
            inquiry_source=data.get('inquiry_source'),
            company_name=data.get('company_name'),
            contact_person=data.get('contact_person'),
            phone=data.get('phone'),
            email=data.get('email'),
            packaging_product=data.get('packaging_product'),
            machine_type=data.get('machine_type'),
            creator_id=current_user.emp_id,
            follower_id=data.get('follower_id') or None
        )
        new_inquiry.update_search_field()
        db.session.add(new_inquiry)
        db.session.commit()

        # 更新统计
        DataChangeStats.increment_stats('inquiry', 'new', 1)
        DataChangeStats.increment_stats('inquiry', 'total', 1)

        # 记录日志
        create_inquiry_log(
            inquiry_id=new_inquiry.id,
            operation_type='create',
            operator_id=current_user.emp_id,
            details={
                "action": "create",
                "user": current_user.name,
                "inquiry_data": new_inquiry.to_dict()
            },
            inquiry_obj=new_inquiry
        )

        return jsonify({
            "code": 200,
            "msg": "询盘创建成功",
            "data": new_inquiry.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建询盘失败: {str(e)}")
        return jsonify({"code": 500, "msg": f"创建询盘失败: {str(e)}", "data": None}), 500

@inquiry_bp.route('/inquiries/<int:inquiry_id>', methods=['GET'])
@route_permission(ROUTE_INQUIRY)
def get_inquiry(inquiry_id):
    """获取单个询盘详情"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 查询询盘
        inquiry = Inquiry.query.get_or_404(inquiry_id)

        # 权限校验
        is_allowed, msg = check_inquiry_permission(current_user, inquiry)
        if not is_allowed:
            return jsonify({"code": 403, "msg": msg, "data": None}), 403

        return jsonify({
            "code": 200,
            "msg": "获取询盘详情成功",
            "data": inquiry.to_dict()
        })
    except Exception as e:
        logger.error(f"获取询盘详情失败（ID:{inquiry_id}）: {str(e)}")
        return jsonify({"code": 500, "msg": f"获取询盘详情失败: {str(e)}", "data": None}), 500

@inquiry_bp.route('/inquiries/<int:inquiry_id>', methods=['PUT'])
@route_permission(ROUTE_INQUIRY)
def update_inquiry(inquiry_id):
    """更新询盘信息（兼容非管理员修改被分配的询盘）"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 查询询盘
        inquiry = Inquiry.query.get_or_404(inquiry_id)

        # 权限校验（已修正：非管理员可操作自己创建/被分配的询盘）
        is_allowed, msg = check_inquiry_permission(current_user, inquiry, "修改")
        if not is_allowed:
            return jsonify({"code": 403, "msg": msg, "data": None}), 403

        # 校验请求数据
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "msg": "请求数据不能为空", "data": None}), 400

        # 校验邮箱格式
        if 'email' in data and not validate_email(data.get('email')):
            return jsonify({"code": 400, "msg": "邮箱格式不正确", "data": None}), 400

        # 记录旧数据
        old_data = inquiry.to_dict()

        # 更新字段
        if 'area' in data: inquiry.area = data['area']
        if 'inquiry_date' in data and data['inquiry_date']:
            inquiry.inquiry_date = datetime.strptime(data['inquiry_date'], '%Y-%m-%d').date()
        if 'inquiry_source' in data: inquiry.inquiry_source = data['inquiry_source']
        if 'company_name' in data: inquiry.company_name = data['company_name']
        if 'contact_person' in data: inquiry.contact_person = data['contact_person']
        if 'phone' in data: inquiry.phone = data['phone']
        if 'email' in data: inquiry.email = data['email']
        if 'packaging_product' in data: inquiry.packaging_product = data['packaging_product']
        if 'machine_type' in data: inquiry.machine_type = data['machine_type']

        # 仅管理员可更新跟单专员
        if 'follower_id' in data and current_user.user_role == 'admin':
            inquiry.follower_id = data['follower_id']

        inquiry.update_search_field()
        db.session.commit()

        # 记录日志
        updated_fields = {}
        for field in ['area', 'inquiry_date', 'inquiry_source', 'company_name',
                     'contact_person', 'phone', 'email', 'packaging_product', 'machine_type']:
            if field in data:
                old_val = old_data.get(field)
                new_val = data[field] if field != 'inquiry_date' else datetime.strptime(data[field], '%Y-%m-%d').date().strftime('%Y-%m-%d')
                updated_fields[field] = {'old': old_val, 'new': new_val}

        create_inquiry_log(
            inquiry_id=inquiry.id,
            operation_type='update',
            operator_id=current_user.emp_id,
            details={
                "action": "update",
                "user": current_user.name,
                "updated_fields": updated_fields
            },
            inquiry_obj=inquiry
        )

        return jsonify({
            "code": 200,
            "msg": "询盘更新成功",
            "data": inquiry.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新询盘失败（ID:{inquiry_id}）: {str(e)}")
        return jsonify({"code": 500, "msg": f"更新询盘失败: {str(e)}", "data": None}), 500

@inquiry_bp.route('/inquiries/<int:inquiry_id>', methods=['DELETE'])
@route_permission(ROUTE_INQUIRY)
def delete_inquiry(inquiry_id):
    """删除询盘"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 查询询盘
        inquiry = Inquiry.query.get_or_404(inquiry_id)

        # 权限校验
        is_allowed, msg = check_inquiry_permission(current_user, inquiry, "删除")
        if not is_allowed:
            return jsonify({"code": 403, "msg": msg, "data": None}), 403

        # 清理关联的客户ID
        inquiry.customer_id = None

        # 检查是否关联订单
        from app.models.order import Order
        associated_orders = Order.query.filter_by(inquiry_id=inquiry_id).all()
        if associated_orders:
            order_info = [{
                "id": o.id,
                "customer_name": o.customer_name,
                "contract_no": o.contract_no,
                "order_time": o.order_time.strftime('%Y-%m-%d') if o.order_time else None,
                "contract_amount": float(o.contract_amount) if o.contract_amount else 0.0
            } for o in associated_orders]
            return jsonify({
                "code": 400,
                "msg": "该询盘已关联订单，不能删除",
                "data": {"associated_orders": order_info}
            }), 400

        # 记录删除前数据
        inquiry_data = inquiry.to_dict()
        communications = InquiryCommunication.query.filter_by(inquiry_id=inquiry_id).all()
        comm_data = [c.to_dict() for c in communications]

        # 更新统计
        DataChangeStats.increment_stats('inquiry', 'total', -1)
        if communications:
            DataChangeStats.increment_stats('communication', 'total', -len(communications))

        # 删除询盘
        db.session.delete(inquiry)
        db.session.commit()

        # 记录日志
        create_inquiry_log(
            inquiry_id=0,
            operation_type='delete',
            operator_id=current_user.emp_id,
            details={
                "action": "delete",
                "user": current_user.name,
                "inquiry_data": inquiry_data,
                "communication_data": comm_data
            },
            inquiry_obj=inquiry
        )

        return jsonify({"code": 200, "msg": "询盘删除成功", "data": None})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除询盘失败（ID:{inquiry_id}）: {str(e)}")
        return jsonify({"code": 500, "msg": f"删除询盘失败: {str(e)}", "data": None}), 500

@inquiry_bp.route('/inquiries/<int:inquiry_id>/communications', methods=['GET'])
@route_permission(ROUTE_INQUIRY)
def get_inquiry_communications(inquiry_id):
    """获取询盘沟通记录列表"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 查询询盘并校验权限
        inquiry = Inquiry.query.get_or_404(inquiry_id)
        is_allowed, msg = check_inquiry_permission(current_user, inquiry)
        if not is_allowed:
            return jsonify({"code": 403, "msg": f"无权限访问该询盘的沟通记录: {msg}", "data": None}), 403

        # 分页查询
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        query = InquiryCommunication.query.filter_by(inquiry_id=inquiry_id)
        total = query.count()
        communications = query.order_by(InquiryCommunication.create_time.desc()).offset((page-1)*size).limit(size).all()

        return jsonify({
            "code": 200,
            "msg": "获取询盘沟通记录成功",
            "data": {
                "list": [c.to_dict() for c in communications],
                "total": total,
                "page": page,
                "size": size
            }
        })
    except Exception as e:
        logger.error(f"获取沟通记录失败（询盘ID:{inquiry_id}）: {str(e)}")
        return jsonify({"code": 500, "msg": f"获取询盘沟通记录失败: {str(e)}", "data": None}), 500

@inquiry_bp.route('/inquiries/<int:inquiry_id>/communications', methods=['POST'])
@route_permission(ROUTE_INQUIRY)
def create_inquiry_communication(inquiry_id):
    """为询盘添加沟通记录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "msg": "请求数据不能为空", "data": None}), 400

        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 查询询盘并校验权限
        inquiry = Inquiry.query.get_or_404(inquiry_id)
        is_allowed, msg = check_inquiry_permission(current_user, inquiry)
        if not is_allowed:
            return jsonify({"code": 403, "msg": f"无权限添加沟通记录: {msg}", "data": None}), 403

        # 校验必填字段
        if not data.get('subject'):
            return jsonify({"code": 400, "msg": "缺少必填字段: subject", "data": None}), 400

        # 创建沟通记录
        new_comm = InquiryCommunication(
            inquiry_id=inquiry_id,
            subject=data.get('subject'),
            content=data.get('content'),
            communication_date=datetime.strptime(data.get('communication_date'), '%Y-%m-%d').date() if data.get('communication_date') else None,
            company_name=inquiry.company_name,
            creator_id=current_user.emp_id
        )
        db.session.add(new_comm)
        db.session.commit()

        # 更新统计
        DataChangeStats.increment_stats('communication', 'new', 1)
        DataChangeStats.increment_stats('communication', 'total', 1)

        # 记录日志
        create_inquiry_log(
            inquiry_id=inquiry_id,
            operation_type='create_communication',
            operator_id=current_user.emp_id,
            details={
                "action": "create_communication",
                "user": current_user.name,
                "communication_data": new_comm.to_dict()
            },
            inquiry_obj=inquiry
        )

        return jsonify({
            "code": 200,
            "msg": "沟通记录创建成功",
            "data": new_comm.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建沟通记录失败（询盘ID:{inquiry_id}）: {str(e)}")
        return jsonify({"code": 500, "msg": f"创建沟通记录失败: {str(e)}", "data": None}), 500

@inquiry_bp.route('/inquiries/<int:inquiry_id>/communications/<int:comm_id>', methods=['PUT'])
@route_permission(ROUTE_INQUIRY)
def update_inquiry_communication(inquiry_id, comm_id):
    """更新询盘沟通记录"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 查询沟通记录
        comm = InquiryCommunication.query.filter_by(id=comm_id, inquiry_id=inquiry_id).first_or_404()

        # 权限校验
        is_allowed, msg = check_communication_permission(current_user, comm)
        if not is_allowed:
            return jsonify({"code": 403, "msg": msg, "data": None}), 403

        # 校验请求数据
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "msg": "请求数据不能为空", "data": None}), 400

        # 记录旧数据
        old_data = comm.to_dict()

        # 更新字段
        if 'subject' in data: comm.subject = data['subject']
        if 'content' in data: comm.content = data['content']
        if 'communication_date' in data and data['communication_date']:
            comm.communication_date = datetime.strptime(data['communication_date'], '%Y-%m-%d').date()

        # 更新公司名称
        inquiry = Inquiry.query.get_or_404(inquiry_id)
        comm.company_name = inquiry.company_name

        db.session.commit()

        # 记录日志
        updated_fields = {}
        for field in ['subject', 'content', 'communication_date']:
            if field in data:
                old_val = old_data.get(field)
                new_val = data[field] if field != 'communication_date' else datetime.strptime(data[field], '%Y-%m-%d').date().strftime('%Y-%m-%d')
                updated_fields[field] = {'old': old_val, 'new': new_val}

        create_inquiry_log(
            inquiry_id=inquiry_id,
            operation_type='update_communication',
            operator_id=current_user.emp_id,
            details={
                "action": "update_communication",
                "user": current_user.name,
                "communication_id": comm.id,
                "updated_fields": updated_fields
            },
            inquiry_obj=inquiry
        )

        return jsonify({
            "code": 200,
            "msg": "沟通记录更新成功",
            "data": comm.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新沟通记录失败（ID:{comm_id}）: {str(e)}")
        return jsonify({"code": 500, "msg": f"更新沟通记录失败: {str(e)}", "data": None}), 500

@inquiry_bp.route('/inquiries/<int:inquiry_id>/communications/<int:comm_id>', methods=['DELETE'])
@route_permission(ROUTE_INQUIRY)
def delete_inquiry_communication(inquiry_id, comm_id):
    """删除询盘沟通记录"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 查询沟通记录
        comm = InquiryCommunication.query.filter_by(id=comm_id, inquiry_id=inquiry_id).first_or_404()

        # 权限校验
        is_allowed, msg = check_communication_permission(current_user, comm)
        if not is_allowed:
            return jsonify({"code": 403, "msg": msg, "data": None}), 403

        # 记录数据
        comm_data = comm.to_dict()
        inquiry = comm.inquiry

        # 更新统计
        DataChangeStats.increment_stats('communication', 'total', -1)

        # 删除记录
        db.session.delete(comm)
        db.session.commit()

        # 记录日志
        create_inquiry_log(
            inquiry_id=inquiry_id,
            operation_type='delete_communication',
            operator_id=current_user.emp_id,
            details={
                "action": "delete_communication",
                "user": current_user.name,
                "communication_data": comm_data
            },
            inquiry_obj=inquiry
        )

        return jsonify({"code": 200, "msg": "沟通记录删除成功", "data": comm_data})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除沟通记录失败（ID:{comm_id}）: {str(e)}")
        return jsonify({"code": 500, "msg": f"删除沟通记录失败: {str(e)}", "data": None}), 500

@inquiry_bp.route('/inquiry-logs', methods=['GET'])
@route_permission(ROUTE_INQUIRY)
def get_inquiry_logs():
    """获取询盘日志列表（仅管理员）"""
    try:
        # 分页/筛选参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        operation_type = request.args.get('operation_type')
        operator_name = request.args.get('operator_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 构建查询
        query = BusinessOperationLog.query.filter(BusinessOperationLog.module == 'inquiry')

        # 筛选条件
        if operation_type: query = query.filter(BusinessOperationLog.operation_type.contains(operation_type))
        if operator_name: query = query.join(Employee).filter(Employee.name.contains(operator_name))
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(BusinessOperationLog.create_time >= start_dt)
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(BusinessOperationLog.create_time < end_dt)

        # 分页查询
        total = query.count()
        logs = query.order_by(BusinessOperationLog.create_time.desc()).offset((page-1)*size).limit(size).all()

        # 统计数据
        inquiry_total = DataChangeStats.query.filter_by(module='inquiry', stats_type='total').first()
        inquiry_new = DataChangeStats.query.filter_by(module='inquiry', stats_type='new').first()
        comm_total = DataChangeStats.query.filter_by(module='communication', stats_type='total').first()
        comm_new = DataChangeStats.query.filter_by(module='communication', stats_type='new').first()

        # 近30天统计
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_inqs = Inquiry.query.filter(Inquiry.create_time >= thirty_days_ago).count()
        new_comms = InquiryCommunication.query.filter(InquiryCommunication.create_time >= thirty_days_ago).count()

        statistics = {
            "total_inquiries": inquiry_total.stats_value if inquiry_total else 0,
            "total_communications": comm_total.stats_value if comm_total else 0,
            "new_inquiries": inquiry_new.stats_value if inquiry_new else 0,
            "new_communications": comm_new.stats_value if comm_new else 0,
            "last_reset_time": inquiry_new.reset_time.strftime('%Y-%m-%d') if (inquiry_new and inquiry_new.reset_time) else None,
            "monthly_inquiries": new_inqs,
            "monthly_communications": new_comms,
            # 兼容字段
            "total_main": inquiry_total.stats_value if inquiry_total else 0,
            "total_sub": comm_total.stats_value if comm_total else 0,
            "new_main": inquiry_new.stats_value if inquiry_new else 0,
            "new_sub": comm_new.stats_value if comm_new else 0,
            "monthly_main": new_inqs,
            "monthly_sub": new_comms
        }

        return jsonify({
            "code": 200,
            "msg": "获取询盘日志成功",
            "data": {
                "list": [l.to_dict() for l in logs],
                "total": total,
                "page": page,
                "size": size,
                "statistics": statistics
            }
        })
    except Exception as e:
        logger.error(f"获取询盘日志失败: {str(e)}")
        return jsonify({"code": 500, "msg": f"获取询盘日志失败: {str(e)}", "data": None}), 500

@inquiry_bp.route('/inquiries/stats', methods=['GET'])
@route_permission(ROUTE_INQUIRY)
def get_inquiry_statistics():
    """获取询盘统计信息（修正非管理员统计范围）"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 基础查询：非管理员统计「自己创建 + 被分配」的询盘
        query = Inquiry.query
        if current_user.user_role != 'admin':
            query = query.filter(
                (Inquiry.creator_id == current_user.emp_id) |
                (Inquiry.follower_id == current_user.emp_id)
            )

        # 总询盘数
        total = query.count()

        # 按来源/地区统计
        from sqlalchemy import func
        source_stats = db.session.query(Inquiry.inquiry_source, func.count(Inquiry.id)).filter(Inquiry.inquiry_source.isnot(None))
        area_stats = db.session.query(Inquiry.area, func.count(Inquiry.id)).filter(Inquiry.area.isnot(None))

        # 权限过滤统计数据
        if current_user.user_role != 'admin':
            source_stats = source_stats.filter(
                (Inquiry.creator_id == current_user.emp_id) |
                (Inquiry.follower_id == current_user.emp_id)
            )
            area_stats = area_stats.filter(
                (Inquiry.creator_id == current_user.emp_id) |
                (Inquiry.follower_id == current_user.emp_id)
            )

        source_stats = source_stats.group_by(Inquiry.inquiry_source).all()
        area_stats = area_stats.group_by(Inquiry.area).all()

        return jsonify({
            "code": 200,
            "msg": "获取询盘统计成功",
            "data": {
                "total_inquiries": total,
                "source_statistics": {s[0]: s[1] for s in source_stats},
                "area_statistics": {a[0]: a[1] for a in area_stats}
            }
        })
    except Exception as e:
        logger.error(f"获取询盘统计失败: {str(e)}")
        return jsonify({"code": 500, "msg": f"获取询盘统计失败: {str(e)}", "data": None}), 500

@inquiry_bp.route('/inquiries/upload-communication-media', methods=['POST'])
@route_permission(ROUTE_INQUIRY)
def upload_communication_media():
    """上传沟通记录媒体文件"""
    try:
        # 获取沟通记录ID
        comm_id = request.form.get('communication_id') or request.form.get('task_id')
        if not comm_id:
            return jsonify({"code": 400, "msg": "缺少沟通记录ID或任务ID", "data": None}), 400

        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 验证沟通记录
        comm = InquiryCommunication.query.filter_by(id=comm_id).first()
        if not comm:
            from app.models.order_status import StatusTask
            task = StatusTask.query.filter_by(id=comm_id).first()
            if not task:
                return jsonify({"code": 404, "msg": "沟通记录或任务不存在", "data": None}), 404
            return jsonify({"code": 400, "msg": "请使用订单状态相关API上传到任务", "data": None}), 400

        # 权限校验
        is_allowed, msg = check_communication_permission(current_user, comm)
        if not is_allowed:
            return jsonify({"code": 403, "msg": msg, "data": None}), 403

        # 检查上传文件
        if 'file' not in request.files and 'files' not in request.files:
            return jsonify({"code": 400, "msg": "没有上传文件", "data": None}), 400

        # 获取文件列表
        uploaded_files = []
        if 'files' in request.files:
            uploaded_files = request.files.getlist('files')
        elif 'file' in request.files:
            uploaded_files = [request.files['file']]

        if not uploaded_files or all(f.filename == '' for f in uploaded_files):
            return jsonify({"code": 400, "msg": "没有选择文件", "data": None}), 400

        # 准备存储路径
        media_dir = os.path.join('assets', 'Media', 'inquiries', str(comm_id))
        os.makedirs(media_dir, exist_ok=True)
        uploaded_media = []

        # 处理文件上传
        for file in uploaded_files:
            if file.filename == '':
                continue

            # 验证文件格式
            if not allowed_file(file.filename):
                return jsonify({"code": 400, "msg": f"不支持的文件格式: {file.filename}", "data": None}), 400

            # 生成唯一文件名
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{ext}"
            file_path = os.path.join(media_dir, unique_name)

            # 保存文件
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            file_type = 'image' if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'] else 'video'

            # 生成缩略图
            thumb_path = None
            if file_type == 'image':
                thumb_name = f"thumb_{unique_name}"
                thumb_path = os.path.join(media_dir, thumb_name)
                create_thumbnail(file_path, thumb_path)

            # 保存媒体记录
            media = InquiryCommunicationMedia(
                communication_id=comm_id,
                file_name=filename,
                file_path=file_path.replace('\\', '/'),
                thumb_path=thumb_path.replace('\\', '/') if thumb_path else None,
                file_size=file_size,
                file_type=file_type
            )
            db.session.add(media)
            db.session.flush()
            uploaded_media.append(media.to_dict())

        # 提交事务
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": f"成功上传 {len(uploaded_media)} 个媒体文件",
            "data": {"media_files": uploaded_media}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"上传媒体文件失败: {str(e)}")
        return jsonify({"code": 500, "msg": f"媒体文件上传失败: {str(e)}", "data": None}), 500

@inquiry_bp.route('/inquiries/communications/<int:comm_id>/media', methods=['DELETE'])
@route_permission(ROUTE_INQUIRY)
def delete_communication_media(comm_id):
    """删除沟通记录媒体文件"""
    try:
        # 获取媒体文件ID
        data = request.get_json()
        media_id = data.get('media_file_id') if data else None
        if not media_id:
            return jsonify({"code": 400, "msg": "缺少媒体文件ID", "data": None}), 400

        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({"code": 401, "msg": "未登录或登录状态失效", "data": None}), 401

        # 查询媒体文件
        media = InquiryCommunicationMedia.query.filter_by(id=media_id).first()
        if not media:
            return jsonify({"code": 404, "msg": "媒体文件不存在", "data": None}), 404

        # 验证沟通记录权限
        comm = InquiryCommunication.query.filter_by(id=media.communication_id).first()
        if not comm:
            return jsonify({"code": 404, "msg": "关联的沟通记录不存在", "data": None}), 404

        is_allowed, msg = check_communication_permission(current_user, comm)
        if not is_allowed:
            return jsonify({"code": 403, "msg": msg, "data": None}), 403

        # 记录文件信息
        media_info = media.to_dict()

        # 删除文件和记录
        media.delete_file()
        db.session.delete(media)
        db.session.commit()

        return jsonify({"code": 200, "msg": "媒体文件删除成功", "data": media_info})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除媒体文件失败（ID:{media_id}）: {str(e)}")
        return jsonify({"code": 500, "msg": f"删除媒体文件失败: {str(e)}", "data": None}), 500