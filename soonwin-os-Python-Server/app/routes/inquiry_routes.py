from flask import Blueprint, request, jsonify
from extensions import db
from app.models.inquiry import Inquiry, InquiryCommunication, InquiryLog
from app.models.totp_user import TotpUser
from app.models.employee import Employee
from datetime import datetime
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


def create_inquiry_log(inquiry_id, operation_type, operator_id, details=""):
    """创建询盘操作日志"""
    log = InquiryLog(
        inquiry_id=inquiry_id,
        operation_type=operation_type,
        operator_id=operator_id,
        operation_details=details
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
        
        # 应用筛选条件
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

        # 验证必填字段
        required_fields = ['contact_person', 'packaging_product', 'machine_type']
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
        db.session.add(new_inquiry)
        db.session.commit()

        # 创建操作日志
        create_inquiry_log(
            inquiry_id=new_inquiry.id,
            operation_type='create',
            operator_id=current_user.emp_id,
            details=f"用户 {current_user.name} 创建了询盘，联系人: {data.get('contact_person')}, 公司: {data.get('company_name', 'N/A')}"
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

        db.session.commit()
        
        # 创建操作日志
        create_inquiry_log(
            inquiry_id=inquiry.id,
            operation_type='update',
            operator_id=current_user.emp_id,
            details=f"用户 {current_user.name} 更新了询盘，联系人: {inquiry.contact_person}, 公司: {inquiry.company_name or 'N/A'}"
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

        # 记录操作详情
        details = f"用户 {current_user.name} 删除了询盘，联系人: {inquiry.contact_person}, 公司: {inquiry.company_name or 'N/A'}"
        
        db.session.delete(inquiry)
        db.session.commit()

        # 创建操作日志
        create_inquiry_log(
            inquiry_id=inquiry.id,
            operation_type='delete',
            operator_id=current_user.emp_id,
            details=details
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

        # 创建沟通记录
        new_communication = InquiryCommunication(
            inquiry_id=inquiry_id,
            subject=data.get('subject'),
            content=data.get('content'),
            communication_date=datetime.strptime(data.get('communication_date'), '%Y-%m-%d').date() if data.get('communication_date') else None,
            creator_id=current_user.emp_id
        )
        db.session.add(new_communication)
        db.session.commit()

        # 序列化创建的沟通记录
        communication_data = new_communication.to_dict()

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

        # 更新沟通记录字段
        if 'subject' in data: communication.subject = data['subject']
        if 'content' in data: communication.content = data['content']
        if 'communication_date' in data and data['communication_date']: 
            communication.communication_date = datetime.strptime(data['communication_date'], '%Y-%m-%d').date()

        db.session.commit()

        communication_data = communication.to_dict()

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

        db.session.delete(communication)
        db.session.commit()

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
            query = query.join(TotpUser).filter(TotpUser.name.contains(operator_name))
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

        response_data = {
            "code": 200,
            "msg": "获取询盘日志成功",
            "data": {
                "list": logs_list,
                "total": total,
                "page": page,
                "size": size
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