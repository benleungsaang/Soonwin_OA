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
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
from functools import wraps

# 创建蓝图

inquiry_bp = Blueprint('inquiry', __name__)



def get_current_user():

    """获取当前用户信息的辅助函数"""

    from app.models.employee import Employee

    emp_id = get_user_id_from_token()

    user_role = get_user_role_from_token()

    user_name = "system"  # 默认名称

    

    # 尝试从数据库获取用户信息以获取真实姓名

    if emp_id:

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
        include_associated = request.args.get('include_associated', 'true').lower() == 'true'  # 是否包含已关联订单的询盘

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
            query = query.filter(Inquiry.inquiry_date <= end_date)

        # 如果需要排除已关联订单的询盘
        if not include_associated:
            # 查询所有已关联订单的询盘ID
            from app.models.order import Order
            associated_inquiry_ids = db.session.query(Order.inquiry_id).filter(Order.inquiry_id.isnot(None)).distinct()
            query = query.filter(~Inquiry.id.in_([id[0] for id in associated_inquiry_ids if id[0] is not None]))

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


@inquiry_bp.route('/inquiries', methods=['POST'])
@route_permission(ROUTE_INQUIRY)
def create_inquiry():
    """创建新询盘"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 获取当前用户
        current_user = get_current_user()

        # 验证必填字段 - 所有字段都必须填写
        required_fields = ['area', 'inquiry_date', 'inquiry_source', 'company_name', 'contact_person', 'phone', 'email', 'packaging_product', 'machine_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "code": 400,
                    "msg": f"缺少必填字段: {field}",
                    "data": None
                }), 400

        # 验证邮箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if data.get('email') and not re.match(email_pattern, data.get('email')):
            return jsonify({
                "code": 400,
                "msg": "邮箱格式不正确",
                "data": None
            }), 400

        # 创建询盘记录
        new_inquiry = Inquiry(
            area=data.get('area'),
            inquiry_date=datetime.strptime(data.get('inquiry_date'), '%Y-%m-%d').date() if data.get('inquiry_date') else None,
            inquiry_source=data.get('inquiry_source'),
            company_name=data.get('company_name'),
            contact_person=data.get('contact_person'),
            phone=data.get('phone'),
            email=data.get('email'),
            packaging_product=data.get('packaging_product'),
            machine_type=data.get('machine_type'),
            creator_id=current_user.emp_id
        )
        # 更新冗余搜索字段
        new_inquiry.update_search_field()
        db.session.add(new_inquiry)
        db.session.commit()

        # 增加询盘新增统计数据
        DataChangeStats.increment_stats('inquiry', 'new', 1)
        DataChangeStats.increment_stats('inquiry', 'total', 1)

        # 创建操作日志
        # 记录完整的询盘数据
        inquiry_data = new_inquiry.to_dict()
        full_details = {
            "action": "create",
            "user": current_user.name,
            "inquiry_data": inquiry_data
        }

        create_inquiry_log(
            inquiry_id=new_inquiry.id,
            operation_type='create',
            operator_id=current_user.emp_id,
            details=json.dumps(full_details, ensure_ascii=False),
            inquiry_obj=new_inquiry
        )

        # 序列化创建的询盘
        inquiry_data = new_inquiry.to_dict()

        response_data = {
            "code": 200,
            "msg": "询盘创建成功",
            "data": inquiry_data
        }
        return jsonify(response_data)
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建询盘失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiries/<int:inquiry_id>', methods=['GET'])
@route_permission(ROUTE_INQUIRY)
def get_inquiry(inquiry_id):
    """获取单个询盘详情"""
    try:
        # 获取当前用户
        current_user = get_current_user()

        inquiry = Inquiry.query.get_or_404(inquiry_id)

        # 检查权限：管理员可以查看所有，普通用户只能查看自己创建的
        if current_user.user_role != 'admin' and inquiry.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限访问该询盘",
                "data": None
            }), 403

        inquiry_data = inquiry.to_dict()

        response_data = {
            "code": 200,
            "msg": "获取询盘详情成功",
            "data": inquiry_data
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取询盘详情失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiries/<int:inquiry_id>', methods=['PUT'])
@route_permission(ROUTE_INQUIRY)
def update_inquiry(inquiry_id):
    """更新询盘信息"""
    try:
        inquiry = Inquiry.query.get_or_404(inquiry_id)

        # 获取当前用户
        current_user = get_current_user()

        # 检查权限：管理员可以修改所有，普通用户只能修改自己创建的
        if current_user.user_role != 'admin' and inquiry.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限修改该询盘",
                "data": None
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 验证邮箱格式
        if 'email' in data and data['email']:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                return jsonify({
                    "code": 400,
                    "msg": "邮箱格式不正确",
                    "data": None
                }), 400

        # 记录修改前的数据
        old_data = inquiry.to_dict()

        # 更新询盘字段
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

        # 更新冗余搜索字段
        inquiry.update_search_field()

        db.session.commit()

        # 创建操作日志
        # 记录修改的字段
        updated_fields = {}
        for field in ['area', 'inquiry_date', 'inquiry_source', 'company_name', 'contact_person',
                     'phone', 'email', 'packaging_product', 'machine_type']:
            if field in data:
                old_value = old_data.get(field)
                new_value = data[field] if field != 'inquiry_date' or not data['inquiry_date'] else datetime.strptime(data['inquiry_date'], '%Y-%m-%d').date().strftime('%Y-%m-%d')
                updated_fields[field] = {'old': old_value, 'new': new_value}

        details = {
            "action": "update",
            "user": current_user.name,
            "updated_fields": updated_fields
        }

        create_inquiry_log(
            inquiry_id=inquiry.id,
            operation_type='update',
            operator_id=current_user.emp_id,
            details=json.dumps(details, ensure_ascii=False),
            inquiry_obj=inquiry
        )

        inquiry_data = inquiry.to_dict()

        response_data = {
            "code": 200,
            "msg": "询盘更新成功",
            "data": inquiry_data
        }
        return jsonify(response_data)
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新询盘失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiries/<int:inquiry_id>', methods=['DELETE'])
@route_permission(ROUTE_INQUIRY)
def delete_inquiry(inquiry_id):
    """删除询盘"""
    try:
        inquiry = Inquiry.query.get_or_404(inquiry_id)

        # 获取当前用户
        current_user = get_current_user()

        # 检查权限：管理员可以删除所有，普通用户只能删除自己创建的
        if current_user.user_role != 'admin' and inquiry.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限删除该询盘",
                "data": None
            }), 403

        # 检查询盘是否已关联订单
        from app.models.order import Order
        associated_orders = Order.query.filter_by(inquiry_id=inquiry_id).all()
        
        if associated_orders:
            # 如果询盘已关联订单，返回已关联订单的基础信息并提示不能删除
            associated_order_info = []
            for order in associated_orders:
                order_info = {
                    "id": order.id,
                    "customer_name": order.customer_name,
                    "contract_no": order.contract_no,
                    "order_time": order.order_time.strftime('%Y-%m-%d') if order.order_time else None,
                    "contract_amount": float(order.contract_amount) if order.contract_amount else 0.0
                }
                associated_order_info.append(order_info)
            
            return jsonify({
                "code": 400,
                "msg": "该询盘已关联订单，不能删除",
                "data": {
                    "associated_orders": associated_order_info
                }
            }), 400

        # 记录完整询盘数据及关联的沟通记录
        inquiry_data = inquiry.to_dict()

        # 获取关联的沟通记录
        communications = InquiryCommunication.query.filter_by(inquiry_id=inquiry.id).all()
        communication_data_list = [comm.to_dict() for comm in communications]

        details = {
            "action": "delete",
            "user": current_user.name,
            "inquiry_data": inquiry_data,
            "communication_data": communication_data_list  # 包含关联的沟通记录
        }

        # 减少询盘总统计数据
        DataChangeStats.increment_stats('inquiry', 'total', -1)

        # 减少关联沟通记录的累计统计数据
        communication_count = len(communications)
        if communication_count > 0:
            DataChangeStats.increment_stats('communication', 'total', -1 * communication_count)

        db.session.delete(inquiry)
        db.session.commit()

        # 创建操作日志
        create_inquiry_log(
            inquiry_id=0,  # 删除后询盘已不存在，使用0
            operation_type='delete',
            operator_id=current_user.emp_id,
            details=json.dumps(details, ensure_ascii=False),
            inquiry_obj=inquiry  # 传递原询盘对象以获取公司名称
        )

        return jsonify({
            "code": 200,
            "msg": "询盘删除成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除询盘失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiries/<int:inquiry_id>/communications', methods=['GET'])
@route_permission(ROUTE_INQUIRY)
def get_inquiry_communications(inquiry_id):
    """获取询盘沟通记录列表"""
    try:
        # 获取当前用户
        current_user = get_current_user()

        # 检查询盘是否存在及其访问权限
        inquiry = Inquiry.query.get_or_404(inquiry_id)
        if current_user.user_role != 'admin' and inquiry.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限访问该询盘的沟通记录",
                "data": None
            }), 403

        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 构建查询
        query = InquiryCommunication.query.filter_by(inquiry_id=inquiry_id)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        communications = query.order_by(InquiryCommunication.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 序列化沟通记录数据
        communications_list = [comm.to_dict() for comm in communications]

        response_data = {
            "code": 200,
            "msg": "获取询盘沟通记录成功",
            "data": {
                "list": communications_list,
                "total": total,
                "page": page,
                "size": size
            }
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取询盘沟通记录失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiries/<int:inquiry_id>/communications', methods=['POST'])
@route_permission(ROUTE_INQUIRY)
def create_inquiry_communication(inquiry_id):
    """为询盘添加沟通记录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 获取当前用户
        current_user = get_current_user()

        # 检查询盘是否存在及其访问权限
        inquiry = Inquiry.query.get_or_404(inquiry_id)
        if current_user.user_role != 'admin' and inquiry.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限为该询盘添加沟通记录",
                "data": None
            }), 403

        # 验证必填字段
        required_fields = ['subject']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "code": 400,
                    "msg": f"缺少必填字段: {field}",
                    "data": None
                }), 400

        # 创建沟通记录，包含公司名称
        new_communication = InquiryCommunication(
            inquiry_id=inquiry_id,
            subject=data.get('subject'),
            content=data.get('content'),
            communication_date=datetime.strptime(data.get('communication_date'), '%Y-%m-%d').date() if data.get('communication_date') else None,
            company_name=inquiry.company_name,  # 自动设置公司名称
            creator_id=current_user.emp_id
        )
        db.session.add(new_communication)
        db.session.commit()

        # 增加沟通记录新增统计数据
        DataChangeStats.increment_stats('communication', 'new', 1)
        DataChangeStats.increment_stats('communication', 'total', 1)

        # 序列化创建的沟通记录
        communication_data = new_communication.to_dict()

        # 创建操作日志
        details = {
            "action": "create_communication",
            "user": current_user.name,
            "communication_data": communication_data
        }

        create_inquiry_log(
            inquiry_id=inquiry_id,
            operation_type='create_communication',
            operator_id=current_user.emp_id,
            details=json.dumps(details, ensure_ascii=False),
            inquiry_obj=inquiry  # 传递关联的询盘对象以获取公司名称
        )

        response_data = {
            "code": 200,
            "msg": "沟通记录创建成功",
            "data": communication_data
        }
        return jsonify(response_data)
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"创建沟通记录失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiries/<int:inquiry_id>/communications/<int:comm_id>', methods=['PUT'])
@route_permission(ROUTE_INQUIRY)
def update_inquiry_communication(inquiry_id, comm_id):
    """更新询盘沟通记录"""
    try:
        # 获取当前用户
        current_user = get_current_user()

        # 获取沟通记录
        communication = InquiryCommunication.query.filter_by(
            id=comm_id,
            inquiry_id=inquiry_id
        ).first_or_404()

        # 检查权限
        if current_user.user_role != 'admin' and communication.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限修改该沟通记录",
                "data": None
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 记录修改前的数据
        old_data = communication.to_dict()

        # 更新沟通记录字段
        if 'subject' in data: communication.subject = data['subject']
        if 'content' in data: communication.content = data['content']
        if 'communication_date' in data and data['communication_date']:
            communication.communication_date = datetime.strptime(data['communication_date'], '%Y-%m-%d').date()

        # 获取关联的询盘，更新公司名称
        inquiry = Inquiry.query.get_or_404(inquiry_id)
        communication.company_name = inquiry.company_name  # 自动更新公司名称

        db.session.commit()

        communication_data = communication.to_dict()

        # 记录修改的字段
        updated_fields = {}
        for field in ['subject', 'content', 'communication_date']:
            if field in data:
                old_value = old_data.get(field)
                new_value = data[field] if field != 'communication_date' or not data['communication_date'] else datetime.strptime(data['communication_date'], '%Y-%m-%d').date().strftime('%Y-%m-%d')
                updated_fields[field] = {'old': old_value, 'new': new_value}

        details = {
            "action": "update_communication",
            "user": current_user.name,
            "communication_id": communication.id,  # 添加沟通记录ID，用于恢复
            "updated_fields": updated_fields
        }

        # 创建操作日志
        create_inquiry_log(
            inquiry_id=inquiry_id,
            operation_type='update_communication',
            operator_id=current_user.emp_id,
            details=json.dumps(details, ensure_ascii=False),
            inquiry_obj=inquiry  # 传递关联的询盘对象以获取公司名称
        )

        response_data = {
            "code": 200,
            "msg": "沟通记录更新成功",
            "data": communication_data
        }
        return jsonify(response_data)
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新沟通记录失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiries/<int:inquiry_id>/communications/<int:comm_id>', methods=['DELETE'])
@route_permission(ROUTE_INQUIRY)
def delete_inquiry_communication(inquiry_id, comm_id):
    """删除询盘沟通记录"""
    try:
        # 获取当前用户
        current_user = get_current_user()

        # 获取沟通记录
        communication = InquiryCommunication.query.filter_by(
            id=comm_id,
            inquiry_id=inquiry_id
        ).first_or_404()

        # 检查权限
        if current_user.user_role != 'admin' and communication.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限删除该沟通记录",
                "data": None
            }), 403

        # 记录完整沟通记录数据
        communication_data = communication.to_dict()

        # 在删除前先获取关联的询盘对象，以避免删除后无法访问
        related_inquiry = communication.inquiry

        # 减少沟通记录总统计数据
        DataChangeStats.increment_stats('communication', 'total', -1)

        db.session.delete(communication)
        db.session.commit()

        # 创建操作日志
        details = {
            "action": "delete_communication",
            "user": current_user.name,
            "communication_data": communication_data
        }

        create_inquiry_log(
            inquiry_id=inquiry_id,
            operation_type='delete_communication',
            operator_id=current_user.emp_id,
            details=json.dumps(details, ensure_ascii=False),
            inquiry_obj=related_inquiry  # 传递关联的询盘对象以获取公司名称
        )

        return jsonify({
            "code": 200,
            "msg": "沟通记录删除成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除沟通记录失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiry-logs', methods=['GET'])
@route_permission(ROUTE_INQUIRY)
def get_inquiry_logs():
    """获取询盘日志列表（仅管理员）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 获取筛选参数
        operation_type = request.args.get('operation_type')
        operator_name = request.args.get('operator_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 构建查询 - 只查找模块为inquiry的日志
        query = BusinessOperationLog.query.filter(BusinessOperationLog.module == 'inquiry')

        # 应用筛选条件
        if operation_type:
            query = query.filter(BusinessOperationLog.operation_type.contains(operation_type))
        if operator_name:
            query = query.join(Employee).filter(Employee.name.contains(operator_name))
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(BusinessOperationLog.create_time >= start_datetime)
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            query = query.filter(BusinessOperationLog.create_time < end_datetime)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        logs = query.order_by(BusinessOperationLog.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 序列化日志数据
        logs_list = [log.to_dict() for log in logs]

        # 从新的统计数据模型获取统计信息
        # 获取询盘统计
        inquiry_total_stats = DataChangeStats.query.filter_by(module='inquiry', stats_type='total').first()
        inquiry_new_stats = DataChangeStats.query.filter_by(module='inquiry', stats_type='new').first()

        # 获取沟通记录统计
        communication_total_stats = DataChangeStats.query.filter_by(module='communication', stats_type='total').first()
        communication_new_stats = DataChangeStats.query.filter_by(module='communication', stats_type='new').first()

        # 复位时间
        inquiry_reset_time = inquiry_new_stats.reset_time if inquiry_new_stats else None

        # 获取特定时间段内的新增统计 (最近30天)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_inquiries = Inquiry.query.filter(Inquiry.create_time >= thirty_days_ago).count()
        new_communications = InquiryCommunication.query.filter(InquiryCommunication.create_time >= thirty_days_ago).count()

        statistics = {
            "total_inquiries": inquiry_total_stats.stats_value if inquiry_total_stats else 0,
            "total_communications": communication_total_stats.stats_value if communication_total_stats else 0,
            "new_inquiries": inquiry_new_stats.stats_value if inquiry_new_stats else 0,
            "new_communications": communication_new_stats.stats_value if communication_new_stats else 0,
            "last_reset_time": inquiry_reset_time.strftime('%Y-%m-%d') if inquiry_reset_time else None,
            "monthly_inquiries": new_inquiries,  # 最近30天的新增询盘数（作为月度参考）
            "monthly_communications": new_communications,  # 最近30天的新增沟通数（作为月度参考）
            # 为前端添加兼容字段
            "total_main": inquiry_total_stats.stats_value if inquiry_total_stats else 0,
            "total_sub": communication_total_stats.stats_value if communication_total_stats else 0,
            "new_main": inquiry_new_stats.stats_value if inquiry_new_stats else 0,
            "new_sub": communication_new_stats.stats_value if communication_new_stats else 0,
            "monthly_main": new_inquiries,
            "monthly_sub": new_communications
        }

        response_data = {
            "code": 200,
            "msg": "获取询盘日志成功",
            "data": {
                "list": logs_list,
                "total": total,
                "page": page,
                "size": size,
                "statistics": statistics
            }
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取询盘日志失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiries/stats', methods=['GET'])
@route_permission(ROUTE_INQUIRY)
def get_inquiry_statistics():
    """获取询盘统计信息"""
    try:
        # 获取当前用户
        current_user = get_current_user()

        # 构建查询
        query = Inquiry.query

        # 检查是否为管理员，如果不是管理员则只统计自己创建的数据
        if current_user.user_role != 'admin':
            query = query.filter(Inquiry.creator_id == current_user.emp_id)

        # 计算总询盘数
        total_inquiries = query.count()

        # 计算按来源统计
        from sqlalchemy import func
        source_stats = db.session.query(
            Inquiry.inquiry_source,
            func.count(Inquiry.id)
        ).filter(Inquiry.inquiry_source.isnot(None))

        if current_user.user_role != 'admin':
            source_stats = source_stats.filter(Inquiry.creator_id == current_user.emp_id)

        source_stats = source_stats.group_by(Inquiry.inquiry_source).all()

        # 计算按地区统计
        area_stats = db.session.query(
            Inquiry.area,
            func.count(Inquiry.id)
        ).filter(Inquiry.area.isnot(None))

        if current_user.user_role != 'admin':
            area_stats = area_stats.filter(Inquiry.creator_id == current_user.emp_id)

        area_stats = area_stats.group_by(Inquiry.area).all()

        stats_data = {
            'total_inquiries': total_inquiries,
            'source_statistics': {stat[0]: stat[1] for stat in source_stats},
            'area_statistics': {stat[0]: stat[1] for stat in area_stats}
        }

        response_data = {
            "code": 200,
            "msg": "获取询盘统计成功",
            "data": stats_data
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取询盘统计失败: {str(e)}",
            "data": None
        }), 500


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_thumbnail(image_path, thumb_path, size=(200, 200)):
    """创建缩略图"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumb_path, "JPEG", quality=70, optimize=True)
        return True
    except Exception as e:
        print(f"创建缩略图失败: {e}")
        return False


@inquiry_bp.route('/inquiries/upload-communication-media', methods=['POST'])
@route_permission(ROUTE_INQUIRY)
def upload_communication_media():
    """上传沟通记录媒体文件"""
    try:
        communication_id = request.form.get('communication_id') or request.form.get('task_id')
        
        if not communication_id:
            return jsonify({
                "code": 400,
                "msg": "缺少沟通记录ID或任务ID",
                "data": None
            }), 400

        # 获取当前用户
        current_user = get_current_user()

        # 获取沟通记录
        communication = InquiryCommunication.query.filter_by(id=communication_id).first()
        if not communication:
            # 尝试按任务ID查找（为了兼容性）
            from app.models.order_status import StatusTask
            task = StatusTask.query.filter_by(id=communication_id).first()
            if not task:
                return jsonify({
                    "code": 404,
                    "msg": "沟通记录或任务不存在",
                    "data": None
                }), 404
            # 如果是任务，则使用不同的处理逻辑（这里返回错误，因为我们应该使用专门的端点）
            return jsonify({
                "code": 400,
                "msg": "请使用订单状态相关API上传到任务",
                "data": None
            }), 400

        # 检查权限
        if current_user.user_role != 'admin' and communication.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限上传媒体文件到该沟通记录",
                "data": None
            }), 403

        # 检查是否有文件
        if 'file' not in request.files and 'files' not in request.files:
            return jsonify({
                "code": 400,
                "msg": "没有上传文件",
                "data": None
            }), 400

        # 获取上传的文件列表
        uploaded_files = []
        if 'files' in request.files:  # 多个文件
            uploaded_files = request.files.getlist('files')
        elif 'file' in request.files:  # 单个文件
            uploaded_files = [request.files['file']]

        if not uploaded_files or all(f.filename == '' for f in uploaded_files):
            return jsonify({
                "code": 400,
                "msg": "没有选择文件",
                "data": None
            }), 400

        # 存储上传成功的媒体文件信息
        uploaded_media_files = []

        # 创建文件保存路径
        # 路径格式: assets/Media/inquiries/沟通记录ID/
        media_dir = os.path.join('assets', 'Media', 'inquiries', str(communication_id))
        os.makedirs(media_dir, exist_ok=True)

        for file in uploaded_files:
            if file.filename == '':
                continue  # 跳过空文件名

            # 检查文件是否允许
            if not allowed_file(file.filename):
                return jsonify({
                    "code": 400,
                    "msg": f"不支持的文件格式: {file.filename}",
                    "data": None
                }), 400

            # 获取文件扩展名
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()

            # 生成唯一文件名（使用UUID + 时间戳）
            unique_filename = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{file_ext}"
            file_path = os.path.join(media_dir, unique_filename)

            # 保存文件
            file.save(file_path)

            # 获取文件大小
            file_size = os.path.getsize(file_path)

            # 判断文件类型
            file_type = 'image' if file_ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'] else 'video'

            # 创建缩略图（仅对图片文件）
            thumb_path = None
            if file_type == 'image':
                thumb_filename = f"thumb_{unique_filename}"
                thumb_path = os.path.join(media_dir, thumb_filename)
                create_thumbnail(file_path, thumb_path)

            # 创建媒体文件记录
            media_file = InquiryCommunicationMedia(
                communication_id=communication_id,
                file_name=filename,
                file_path=file_path.replace('\\', '/'),  # 统一使用正斜杠
                thumb_path=thumb_path.replace('\\', '/') if thumb_path else None,
                file_size=file_size,
                file_type=file_type
            )
            db.session.add(media_file)
            db.session.flush()  # 获取ID但不提交事务

            # 添加到返回列表
            uploaded_media_files.append(media_file.to_dict())

        # 提交所有更改
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": f"成功上传 {len(uploaded_media_files)} 个媒体文件",
            "data": {
                "media_files": uploaded_media_files
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"媒体文件上传失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiries/communications/<int:comm_id>/media', methods=['DELETE'])
@route_permission(ROUTE_INQUIRY)
def delete_communication_media(comm_id):
    """删除沟通记录媒体文件"""
    try:
        data = request.get_json()
        media_file_id = data.get('media_file_id') if data else None

        if not media_file_id:
            return jsonify({
                "code": 400,
                "msg": "缺少媒体文件ID",
                "data": None
            }), 400

        # 获取当前用户
        current_user = get_current_user()

        # 获取媒体文件记录
        media_file = InquiryCommunicationMedia.query.filter_by(id=media_file_id).first()
        if not media_file:
            return jsonify({
                "code": 404,
                "msg": "媒体文件不存在",
                "data": None
            }), 404

        # 获取关联的沟通记录
        communication = InquiryCommunication.query.filter_by(id=media_file.communication_id).first()
        if not communication:
            return jsonify({
                "code": 404,
                "msg": "关联的沟通记录不存在",
                "data": None
            }), 404

        # 检查权限
        if current_user.user_role != 'admin' and communication.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限删除该媒体文件",
                "data": None
            }), 403

        # 记录媒体文件信息
        media_file_info = media_file.to_dict()

        # 删除实际文件
        media_file.delete_file()

        # 从数据库删除记录
        db.session.delete(media_file)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "媒体文件删除成功",
            "data": media_file_info
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除媒体文件失败: {str(e)}",
            "data": None
        }), 500