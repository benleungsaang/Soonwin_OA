from flask import Blueprint, request, jsonify
from extensions import db
from app.models.inquiry import Inquiry, InquiryCommunication, InquiryLog
from app.models.totp_user import TotpUser
from app.models.employee import Employee
from datetime import datetime, timedelta
import json
from functools import wraps

# 创建蓝图
inquiry_bp = Blueprint('inquiry', __name__)


def admin_required(f):
    """检查用户是否为管理员的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头获取JWT token
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"code": 401, "msg": "未提供访问令牌", "data": None}), 401
        
        try:
            # 去掉 "Bearer " 前缀
            token = token.replace('Bearer ', '')
            # 解码JWT token获取用户信息
            import jwt
            from config import Config
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            emp_id = payload.get('emp_id')
            
            # 查询用户信息 - 使用Employee表而不是TotpUser表
            user = Employee.query.filter_by(emp_id=emp_id).first()
            if not user or user.user_role != 'admin':
                return jsonify({"code": 403, "msg": "权限不足", "data": None}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({"code": 401, "msg": "令牌已过期", "data": None}), 401
        except jwt.InvalidTokenError:
            return jsonify({"code": 401, "msg": "无效的令牌", "data": None}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def get_user_from_token():
    """从JWT token中获取用户信息"""
    token = request.headers.get('Authorization')
    if not token:
        return None
    
    try:
        import jwt
        from config import Config
        token = token.replace('Bearer ', '')
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        emp_id = payload.get('emp_id')
        # 使用Employee表而不是TotpUser表
        return Employee.query.filter_by(emp_id=emp_id).first()
    except:
        return None


def create_inquiry_log(inquiry_id, operation_type, operator_id, details="", inquiry_obj=None, communication_obj=None):
    """创建询盘操作日志，包含统计信息"""
    from sqlalchemy import func
    
    # 计算统计信息
    total_inquiries = Inquiry.query.count()
    total_communications = 0
    new_inquiries_count = 0
    new_communications_count = 0
    
    # 计算总沟通记录数
    if inquiry_obj:
        # 如果有inquiry对象，计算该询盘下的沟通记录数
        total_communications = InquiryCommunication.query.join(Inquiry).filter(Inquiry.id == inquiry_obj.id).count()
    else:
        total_communications = InquiryCommunication.query.count()
    
    # 设置新增计数
    if operation_type == 'create':
        new_inquiries_count = 1
    elif operation_type == 'create_communication':
        new_communications_count = 1

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

    log = InquiryLog(
        inquiry_id=inquiry_id,
        operation_type=operation_type,
        operator_id=operator_id,
        operation_details=details,
        company_name=company_name,
        total_inquiries=total_inquiries,
        total_communications=total_communications,
        new_inquiries_count=new_inquiries_count,
        new_communications_count=new_communications_count
    )
    db.session.add(log)
    db.session.commit()


@inquiry_bp.route('/inquiries', methods=['GET'])
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
        
        # 检查用户权限
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({
                "code": 401,
                "msg": "未授权访问",
                "data": None
            }), 401
        
        # 构建查询
        query = Inquiry.query
        
        # 检查是否为管理员，如果不是管理员则只允许查看自己创建的数据
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


@inquiry_bp.route('/inquiries', methods=['POST'])
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
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({
                "code": 401,
                "msg": "未授权访问",
                "data": None
            }), 401

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
def get_inquiry(inquiry_id):
    """获取单个询盘详情"""
    try:
        # 获取当前用户
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({
                "code": 401,
                "msg": "未授权访问",
                "data": None
            }), 401

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
def update_inquiry(inquiry_id):
    """更新询盘信息"""
    try:
        inquiry = Inquiry.query.get_or_404(inquiry_id)
        
        # 获取当前用户
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({
                "code": 401,
                "msg": "未授权访问",
                "data": None
            }), 401

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
def delete_inquiry(inquiry_id):
    """删除询盘"""
    try:
        inquiry = Inquiry.query.get_or_404(inquiry_id)
        
        # 获取当前用户
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({
                "code": 401,
                "msg": "未授权访问",
                "data": None
            }), 401

        # 检查权限：管理员可以删除所有，普通用户只能删除自己创建的
        if current_user.user_role != 'admin' and inquiry.creator_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "无权限删除该询盘",
                "data": None
            }), 403

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
def get_inquiry_communications(inquiry_id):
    """获取询盘沟通记录列表"""
    try:
        # 获取当前用户
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({
                "code": 401,
                "msg": "未授权访问",
                "data": None
            }), 401

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
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({
                "code": 401,
                "msg": "未授权访问",
                "data": None
            }), 401

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
def update_inquiry_communication(inquiry_id, comm_id):
    """更新询盘沟通记录"""
    try:
        # 获取当前用户
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({
                "code": 401,
                "msg": "未授权访问",
                "data": None
            }), 401

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
def delete_inquiry_communication(inquiry_id, comm_id):
    """删除询盘沟通记录"""
    try:
        # 获取当前用户
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({
                "code": 401,
                "msg": "未授权访问",
                "data": None
            }), 401

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
@admin_required
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

        # 构建查询
        query = InquiryLog.query
        
        # 应用筛选条件
        if operation_type:
            query = query.filter(InquiryLog.operation_type.contains(operation_type))
        if operator_name:
            query = query.join(Employee).filter(Employee.name.contains(operator_name))
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(InquiryLog.create_time >= start_datetime)
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            query = query.filter(InquiryLog.create_time < end_datetime)

        # 计算总数
        total = query.count()

        # 应用分页和排序
        logs = query.order_by(InquiryLog.create_time.desc()).offset((page - 1) * size).limit(size).all()

        # 序列化日志数据
        logs_list = [log.to_dict() for log in logs]

        # 计算统计信息
        total_inquiries = Inquiry.query.count()
        total_communications = InquiryCommunication.query.count()
        
        # 获取最近一次复位时间
        last_reset_log = InquiryLog.query.filter(InquiryLog.operation_type == 'reset_stats').order_by(InquiryLog.reset_time.desc()).first()
        reset_time = last_reset_log.reset_time if last_reset_log else None
        
        # 计算复位后的新增统计（如果存在复位时间）
        if reset_time:
            # 复位后的新增统计
            new_inquiries_since_reset = Inquiry.query.filter(Inquiry.create_time >= reset_time).count()
            new_communications_since_reset = InquiryCommunication.query.filter(InquiryCommunication.create_time >= reset_time).count()
        else:
            # 如果没有复位过，使用最近30天的统计
            thirty_days_ago = datetime.now() - timedelta(days=30)
            new_inquiries_since_reset = Inquiry.query.filter(Inquiry.create_time >= thirty_days_ago).count()
            new_communications_since_reset = InquiryCommunication.query.filter(InquiryCommunication.create_time >= thirty_days_ago).count()

        # 获取特定时间段内的新增统计 (最近30天)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_inquiries = Inquiry.query.filter(Inquiry.create_time >= thirty_days_ago).count()
        new_communications = InquiryCommunication.query.filter(InquiryCommunication.create_time >= thirty_days_ago).count()

        statistics = {
            "total_inquiries": total_inquiries,
            "total_communications": total_communications,
            "new_inquiries": new_inquiries_since_reset if reset_time else new_inquiries,  # 使用复位后的新增数或最近30天的数
            "new_communications": new_communications_since_reset if reset_time else new_communications,  # 使用复位后的新增数或最近30天的数
            "last_reset_time": reset_time.strftime('%Y-%m-%d %H:%M:%S') if reset_time else None,
            "monthly_inquiries": new_inquiries,  # 最近30天的新增询盘数（作为月度参考）
            "monthly_communications": new_communications  # 最近30天的新增沟通数（作为月度参考）
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
def get_inquiry_statistics():
    """获取询盘统计信息"""
    try:
        # 获取当前用户
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({
                "code": 401,
                "msg": "未授权访问",
                "data": None
            }), 401

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


@inquiry_bp.route('/inquiry-logs/<int:log_id>', methods=['DELETE'])
@admin_required
def delete_inquiry_log(log_id):
    """删除询盘操作日志（仅管理员）"""
    try:
        # 查找日志记录
        log = InquiryLog.query.get_or_404(log_id)
        
        # 删除日志记录
        db.session.delete(log)
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": "日志删除成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除日志失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiry-logs', methods=['DELETE'])
@admin_required
def clear_all_inquiry_logs():
    """清空所有询盘操作日志（仅管理员）"""
    try:
        # 删除所有日志记录
        deleted_count = db.session.query(InquiryLog).delete()
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": f"成功清空 {deleted_count} 条日志",
            "data": {"message": f"成功清空 {deleted_count} 条日志"}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"清空日志失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/inquiry-logs/<int:log_id>/restore', methods=['POST'])
@admin_required
def restore_inquiry_log(log_id):
    """根据日志恢复被删除或修改的数据（仅管理员）"""
    try:
        # 查找日志记录
        log = InquiryLog.query.get_or_404(log_id)
        
        # 解析日志详情
        details = json.loads(log.operation_details)
        
        action = details.get('action', '')
        user = details.get('user', '系统')
        
        if action == 'delete':
            # 恢复被删除的询盘
            inquiry_data = details.get('inquiry_data', {})
            communication_data_list = details.get('communication_data', [])
            
            # 创建询盘
            new_inquiry = Inquiry(
                area=inquiry_data.get('area'),
                inquiry_date=datetime.strptime(inquiry_data['inquiry_date'], '%Y-%m-%d').date() if inquiry_data.get('inquiry_date') else None,
                inquiry_source=inquiry_data.get('inquiry_source'),
                company_name=inquiry_data.get('company_name'),
                contact_person=inquiry_data.get('contact_person'),
                phone=inquiry_data.get('phone'),
                email=inquiry_data.get('email'),
                packaging_product=inquiry_data.get('packaging_product'),
                machine_type=inquiry_data.get('machine_type'),
                search_field=inquiry_data.get('search_field'),
                creator_id=inquiry_data.get('creator_id')
            )
            db.session.add(new_inquiry)
            db.session.flush()  # 获取新询盘的ID
            
            # 恢复关联的沟通记录
            for comm_data in communication_data_list:
                new_communication = InquiryCommunication(
                    inquiry_id=new_inquiry.id,
                    subject=comm_data.get('subject'),
                    content=comm_data.get('content'),
                    communication_date=datetime.strptime(comm_data['communication_date'], '%Y-%m-%d').date() if comm_data.get('communication_date') else None,
                    company_name=comm_data.get('company_name'),  # 使用恢复的公司名称
                    creator_id=comm_data.get('creator_id')
                )
                db.session.add(new_communication)
            
            db.session.commit()
            
            # 创建恢复操作日志
            restore_details = {
                "action": "restore",
                "user": user,
                "restored_data_type": "inquiry",
                "restored_inquiry_id": new_inquiry.id,
                "original_log_id": log_id,
                "inquiry_data": inquiry_data  # 包含原始询盘数据用于日志显示
            }
            
            create_inquiry_log(
                inquiry_id=new_inquiry.id,
                operation_type='restore',
                operator_id=get_user_from_token().emp_id,
                details=json.dumps(restore_details, ensure_ascii=False),
                inquiry_obj=new_inquiry
            )
            
            return jsonify({
                "code": 200,
                "msg": "询盘及沟通记录恢复成功",
                "data": {"inquiry_id": new_inquiry.id}
            })
            
        elif action == 'update':
            # 恢复被修改的询盘（使用旧数据）
            updated_fields = details.get('updated_fields', {})
            
            # 从更新字段中提取原始数据
            original_data = {}
            for field, values in updated_fields.items():
                original_data[field] = values.get('old')  # 使用旧值
            
            # 查找需要恢复的询盘
            inquiry_id = log.inquiry_id
            inquiry = Inquiry.query.get_or_404(inquiry_id)
            
            # 恢复原始数据
            for field, value in original_data.items():
                if hasattr(inquiry, field):
                    if field == 'inquiry_date' and value:
                        setattr(inquiry, field, datetime.strptime(value, '%Y-%m-%d').date())
                    else:
                        setattr(inquiry, field, value)
            
            # 更新搜索字段
            inquiry.update_search_field()
            db.session.commit()
            
            # 创建恢复操作日志
            restore_details = {
                "action": "restore",
                "user": user,
                "restored_data_type": "inquiry_update",
                "inquiry_id": inquiry_id,
                "original_log_id": log_id,
                "restored_fields": list(original_data.keys()),
                "inquiry_data": inquiry.to_dict()  # 包含询盘当前数据用于日志显示
            }
            
            create_inquiry_log(
                inquiry_id=inquiry.id,
                operation_type='restore',
                operator_id=get_user_from_token().emp_id,
                details=json.dumps(restore_details, ensure_ascii=False),
                inquiry_obj=inquiry
            )
            
            return jsonify({
                "code": 200,
                "msg": "询盘修改恢复成功",
                "data": {"inquiry_id": inquiry.id}
            })
            
        elif action == 'delete_communication':
            # 恢复被删除的沟通记录
            communication_data = details.get('communication_data', {})
            
            # 创建沟通记录
            new_communication = InquiryCommunication(
                inquiry_id=communication_data.get('inquiry_id'),
                subject=communication_data.get('subject'),
                content=communication_data.get('content'),
                communication_date=datetime.strptime(communication_data['communication_date'], '%Y-%m-%d').date() if communication_data.get('communication_date') else None,
                company_name=communication_data.get('company_name'),
                creator_id=communication_data.get('creator_id')
            )
            db.session.add(new_communication)
            db.session.commit()
            
            # 创建恢复操作日志
            restore_details = {
                "action": "restore",
                "user": user,
                "restored_data_type": "communication",
                "restored_communication_data": communication_data,
                "original_log_id": log_id
            }
            
            # 获取关联的询盘对象用于记录日志
            inquiry = Inquiry.query.get(communication_data.get('inquiry_id'))
            
            create_inquiry_log(
                inquiry_id=communication_data.get('inquiry_id'),
                operation_type='restore',
                operator_id=get_user_from_token().emp_id,
                details=json.dumps(restore_details, ensure_ascii=False),
                inquiry_obj=inquiry
            )
            
            return jsonify({
                "code": 200,
                "msg": "沟通记录恢复成功",
                "data": {"communication_id": new_communication.id}
            })
            
        elif action == 'update_communication':
            # 恢复被修改的沟通记录（使用旧数据）
            updated_fields = details.get('updated_fields', {})
            
            # 从更新字段中提取原始数据
            original_data = {}
            for field, values in updated_fields.items():
                original_data[field] = values.get('old')  # 使用旧值
            
            # 查找需要恢复的沟通记录
            log_inquiry_id = log.inquiry_id
            communication_id = details.get('communication_id')  # 需要从日志详情中获取沟通记录ID
            communication = InquiryCommunication.query.filter_by(
                id=communication_id,
                inquiry_id=log_inquiry_id
            ).first_or_404()

            # 恢复原始数据
            for field, value in original_data.items():
                if hasattr(communication, field):
                    if field == 'communication_date' and value:
                        setattr(communication, field, datetime.strptime(value, '%Y-%m-%d').date())
                    else:
                        setattr(communication, field, value)

            db.session.commit()
            
            # 创建恢复操作日志
            restore_details = {
                "action": "restore",
                "user": user,
                "restored_data_type": "communication_update",
                "inquiry_id": log_inquiry_id,
                "original_log_id": log_id,
                "restored_fields": list(original_data.keys())
            }
            
            create_inquiry_log(
                inquiry_id=log_inquiry_id,
                operation_type='restore',
                operator_id=get_user_from_token().emp_id,
                details=json.dumps(restore_details, ensure_ascii=False),
                inquiry_obj=communication.inquiry
            )
            
            return jsonify({
                "code": 200,
                "msg": "沟通记录修改恢复成功",
                "data": {"communication_id": communication.id}
            })
            
        else:
            return jsonify({
                "code": 400,
                "msg": "该日志类型不支持恢复操作",
                "data": None
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"恢复操作失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/reset-stats', methods=['POST'])
@admin_required
def reset_statistics():
    """复位统计数字（仅管理员）"""
    try:
        # 获取当前统计数字
        from sqlalchemy import func
        current_new_inquiries = Inquiry.query.count()
        current_new_communications = InquiryCommunication.query.count()
        
        # 获取当前用户
        current_user = get_user_from_token()
        
        # 记录复位前的统计数字到日志
        details = {
            "action": "reset_stats",
            "user": current_user.name,
            "reset_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "previous_new_inquiries": current_new_inquiries,
            "previous_new_communications": current_new_communications
        }
        
        # 创建复位操作日志
        reset_log = InquiryLog(
            inquiry_id=0,  # 复位操作不关联特定询盘
            operation_type='reset_stats',
            operator_id=current_user.emp_id,
            operation_details=json.dumps(details, ensure_ascii=False),
            company_name="System",  # 系统操作
            total_inquiries=current_new_inquiries,
            total_communications=current_new_communications,
            new_inquiries_count=current_new_inquiries,  # 复位前的累计数
            new_communications_count=current_new_communications,  # 复位前的累计数
            reset_time=datetime.now()  # 记录复位时间
        )
        
        db.session.add(reset_log)
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": "统计数字复位成功",
            "data": {
                "reset_time": reset_log.reset_time.strftime('%Y-%m-%d %H:%M:%S'),
                "previous_new_inquiries": current_new_inquiries,
                "previous_new_communications": current_new_communications
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"统计数字复位失败: {str(e)}",
            "data": None
        }), 500


@inquiry_bp.route('/monthly-stats', methods=['GET'])
@admin_required
def get_monthly_stats():
    """获取本月统计数字（仅管理员）"""
    try:
        # 计算本月的开始和结束时间
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        
        # 如果是12月，则下个月是下一年的1月
        if now.month == 12:
            end_of_month = datetime(now.year + 1, 1, 1)
        else:
            end_of_month = datetime(now.year, now.month + 1, 1)
        
        # 查询本月新增的询盘数量
        monthly_inquiries = Inquiry.query.filter(
            Inquiry.create_time >= start_of_month,
            Inquiry.create_time < end_of_month
        ).count()
        
        # 查询本月新增的沟通记录数量
        monthly_communications = InquiryCommunication.query.filter(
            InquiryCommunication.create_time >= start_of_month,
            InquiryCommunication.create_time < end_of_month
        ).count()
        
        return jsonify({
            "code": 200,
            "msg": "本月统计查询成功",
            "data": {
                "monthly_start": start_of_month.strftime('%Y-%m-%d'),
                "monthly_inquiries": monthly_inquiries,
                "monthly_communications": monthly_communications
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"本月统计查询失败: {str(e)}",
            "data": None
        }), 500