from flask import Blueprint, request, jsonify
from extensions import db
from app.models.business_operation_log import BusinessOperationLog, get_logs_by_module, delete_logs_by_module
from app.models.employee import Employee
from app.models.inquiry import Inquiry, InquiryCommunication
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_LOG_MANAGE
from app.models.simple_permission import get_user_role_from_token
from datetime import datetime, timedelta
import json

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
log_bp = Blueprint('log', __name__)

def get_current_user():
    """获取当前用户信息的辅助函数"""
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







@log_bp.route('/<module>-logs', methods=['GET'])
@route_permission(ROUTE_LOG_MANAGE)
def get_logs_by_module_endpoint(module):
    """根据模块获取日志列表（仅管理员）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)

        # 获取筛选参数
        operation_type = request.args.get('operation_type')
        operator_name = request.args.get('operator_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 应用日期筛选
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 获取日志数据
        logs, total = get_logs_by_module(
            module_name=module,
            page=page,
            size=size,
            operation_type=operation_type,
            operator_name=operator_name,
            start_date=start_date,
            end_date=end_date
        )

        # 序列化日志数据
        logs_list = [log.to_dict() for log in logs]

        # 获取统计信息（根据模块）
        statistics = get_statistics_by_module(module)

        response_data = {
            "code": 200,
            "msg": f"获取{module}日志成功",
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
            "msg": f"获取{module}日志失败: {str(e)}",
            "data": None
        }), 500


def get_statistics_by_module(module):
    """根据模块获取统计信息"""
    from sqlalchemy import func

    # 通用统计结构
    stats = {
        "total_main": 0,
        "total_sub": 0,
        "new_main": 0,
        "new_sub": 0,
        "monthly_main": 0,
        "monthly_sub": 0,
        "last_reset_time": None
    }

    # 获取最近一次复位时间
    last_reset_log = BusinessOperationLog.query.filter(
        BusinessOperationLog.module == module,
        BusinessOperationLog.operation_type == 'reset_stats'
    ).order_by(BusinessOperationLog.create_time.desc()).first()

    reset_time = None
    if last_reset_log and 'reset_time' in last_reset_log.operation_details:
        try:
            reset_time_str = json.loads(last_reset_log.operation_details).get('reset_time')
            if reset_time_str:
                reset_time = datetime.strptime(reset_time_str.split(' ')[0], '%Y-%m-%d')
        except:
            reset_time = None

    # 根据模块类型计算统计数据
    if module == 'inquiry':
        # 询盘统计
        stats["total_main"] = Inquiry.query.count()
        stats["total_sub"] = InquiryCommunication.query.count()

        # 获取30天前的日期
        thirty_days_ago = datetime.now() - timedelta(days=30)

        # 计算新增统计（如果存在复位时间则使用复位后的时间，否则使用最近30天）
        if reset_time:
            stats["new_main"] = Inquiry.query.filter(Inquiry.create_time >= reset_time).count()
            stats["new_sub"] = InquiryCommunication.query.filter(InquiryCommunication.create_time >= reset_time).count()
        else:
            stats["new_main"] = Inquiry.query.filter(Inquiry.create_time >= thirty_days_ago).count()
            stats["new_sub"] = InquiryCommunication.query.filter(InquiryCommunication.create_time >= thirty_days_ago).count()

        # 月度统计
        stats["monthly_main"] = Inquiry.query.filter(Inquiry.create_time >= thirty_days_ago).count()
        stats["monthly_sub"] = InquiryCommunication.query.filter(InquiryCommunication.create_time >= thirty_days_ago).count()

        stats["last_reset_time"] = reset_time.strftime('%Y-%m-%d') if reset_time else None

    elif module == 'video':
        # 视频统计（示例）
        from app.models.video import Video
        stats["total_main"] = Video.query.filter(Video.is_deleted == 0).count()
        stats["total_sub"] = 0  # 视频子项统计（如视频标签、评论等）

        thirty_days_ago = datetime.now() - timedelta(days=30)
        stats["new_main"] = Video.query.filter(
            Video.is_deleted == 0,
            Video.upload_time >= thirty_days_ago
        ).count()
        stats["new_sub"] = 0
        stats["monthly_main"] = Video.query.filter(
            Video.is_deleted == 0,
            Video.upload_time >= thirty_days_ago
        ).count()
        stats["monthly_sub"] = 0
        stats["last_reset_time"] = reset_time.strftime('%Y-%m-%d') if reset_time else None

    elif module == 'photo':
        # 图片统计（示例）
        from app.models.photo import Photo
        stats["total_main"] = Photo.query.count()
        stats["total_sub"] = 0

        thirty_days_ago = datetime.now() - timedelta(days=30)
        stats["new_main"] = Photo.query.filter(Photo.upload_time >= thirty_days_ago).count()
        stats["new_sub"] = 0
        stats["monthly_main"] = Photo.query.filter(Photo.upload_time >= thirty_days_ago).count()
        stats["monthly_sub"] = 0
        stats["last_reset_time"] = reset_time.strftime('%Y-%m-%d') if reset_time else None

    elif module == 'employee':
        # 人员统计（示例）
        stats["total_main"] = Employee.query.count()
        stats["total_sub"] = 0

        thirty_days_ago = datetime.now() - timedelta(days=30)
        stats["new_main"] = Employee.query.filter(Employee.create_time >= thirty_days_ago).count()
        stats["new_sub"] = 0
        stats["monthly_main"] = Employee.query.filter(Employee.create_time >= thirty_days_ago).count()
        stats["monthly_sub"] = 0
        stats["last_reset_time"] = reset_time.strftime('%Y-%m-%d') if reset_time else None

    # 为其他模块预留空间
    else:
        # 默认统计（可以根据需要扩展）
        stats["total_main"] = BusinessOperationLog.query.filter(BusinessOperationLog.module == module).count()
        stats["total_sub"] = 0
        thirty_days_ago = datetime.now() - timedelta(days=30)
        stats["new_main"] = BusinessOperationLog.query.filter(
            BusinessOperationLog.module == module,
            BusinessOperationLog.create_time >= thirty_days_ago
        ).count()
        stats["new_sub"] = 0
        stats["monthly_main"] = stats["new_main"]
        stats["monthly_sub"] = 0
        stats["last_reset_time"] = reset_time.strftime('%Y-%m-%d') if reset_time else None

    return stats


@log_bp.route('/<module>-logs/<int:log_id>', methods=['DELETE'])
@route_permission(ROUTE_LOG_MANAGE)
def delete_log_by_id(module, log_id):
    """删除指定模块的特定日志（仅管理员）"""
    try:
        # 删除日志记录
        deleted_count = delete_logs_by_module(module, log_id)

        if deleted_count > 0:
            return jsonify({
                "code": 200,
                "msg": "日志删除成功",
                "data": None
            })
        else:
            return jsonify({
                "code": 404,
                "msg": "未找到指定的日志记录",
                "data": None
            }), 404
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"删除日志失败: {str(e)}",
            "data": None
        }), 500


@log_bp.route('/<module>-logs', methods=['DELETE'])
@route_permission(ROUTE_LOG_MANAGE)
def clear_all_logs_by_module(module):
    """清空指定模块的所有日志（仅管理员）"""
    try:
        # 删除所有指定模块的日志记录
        deleted_count = delete_logs_by_module(module)

        return jsonify({
            "code": 200,
            "msg": f"成功清空 {deleted_count} 条{module}日志",
            "data": {"message": f"成功清空 {deleted_count} 条{module}日志"}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"清空日志失败: {str(e)}",
            "data": None
        }), 500


@log_bp.route('/<module>-logs/<int:log_id>/restore', methods=['POST'])
@route_permission(ROUTE_LOG_MANAGE)
def restore_log_by_id(module, log_id):
    """根据日志恢复被删除或修改的数据（仅管理员）"""
    try:
        # 查找日志记录
        log = BusinessOperationLog.query.filter(
            BusinessOperationLog.id == log_id,
            BusinessOperationLog.module == module
        ).first_or_404()

        # 根据模块调用相应的恢复逻辑
        if module == 'inquiry':
            return restore_inquiry_log(log)
        elif module == 'video':
            return restore_video_log(log)
        elif module == 'photo':
            return restore_photo_log(log)
        elif module == 'employee':
            return restore_employee_log(log)
        else:
            return jsonify({
                "code": 400,
                "msg": f"该模块({module})暂不支持恢复操作",
                "data": None
            }), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"恢复操作失败: {str(e)}",
            "data": None
        }), 500


def restore_inquiry_log(log):
    """恢复询盘相关的日志"""
    from app.models.inquiry import Inquiry, InquiryCommunication

    # 解析日志详情
    details = log.operation_details if isinstance(log.operation_details, dict) else json.loads(log.operation_details) if log.operation_details else {}

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
                company_name=comm_data.get('company_name'),
                creator_id=comm_data.get('creator_id')
            )
            db.session.add(new_communication)

        db.session.commit()

        # 创建恢复操作日志
        from app.models.business_operation_log import add_inquiry_log
        restore_details = {
            "action": "restore",
            "user": user,
            "restored_data_type": "inquiry",
            "restored_inquiry_id": new_inquiry.id,
            "original_log_id": log.id,
            "inquiry_data": inquiry_data
        }

        add_inquiry_log(
            inquiry_id=new_inquiry.id,
            operation_type='restore',
            operator_id=get_user_id_from_token(),
            details=restore_details
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
        inquiry_id = int(log.biz_id) if log.biz_id and log.biz_id != '0' else None
        if not inquiry_id:
            return jsonify({
                "code": 400,
                "msg": "无法确定要恢复的询盘ID",
                "data": None
            }), 400

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
        from app.models.business_operation_log import add_inquiry_log
        restore_details = {
            "action": "restore",
            "user": user,
            "restored_data_type": "inquiry_update",
            "inquiry_id": inquiry_id,
            "original_log_id": log.id,
            "restored_fields": list(original_data.keys()),
            "inquiry_data": inquiry.to_dict()
        }

        add_inquiry_log(
                    inquiry_id=inquiry.id,
                    operation_type='restore',
                    operator_id=get_user_id_from_token(),
                    details=restore_details        )

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
        from app.models.business_operation_log import add_inquiry_log
        restore_details = {
            "action": "restore",
            "user": user,
            "restored_data_type": "communication",
            "restored_communication_data": communication_data,
            "original_log_id": log.id
        }

        # 获取关联的询盘对象用于记录日志
        inquiry = Inquiry.query.get(communication_data.get('inquiry_id'))

        add_inquiry_log(
            inquiry_id=communication_data.get('inquiry_id'),
            operation_type='restore',
            operator_id=get_user_id_from_token(),
            details=restore_details
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
        log_inquiry_id = int(log.biz_id) if log.biz_id else None
        communication_id = details.get('communication_id')
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
        from app.models.business_operation_log import add_inquiry_log
        restore_details = {
            "action": "restore",
            "user": user,
            "restored_data_type": "communication_update",
            "inquiry_id": log_inquiry_id,
            "original_log_id": log.id,
            "restored_fields": list(original_data.keys())
        }

        add_inquiry_log(
            inquiry_id=log_inquiry_id,
            operation_type='restore',
            operator_id=get_user_id_from_token(),
            details=restore_details
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


def restore_video_log(log):
    """恢复视频相关的日志"""
    from app.models.video import Video
    import json
    from datetime import datetime

    # 解析日志详情
    details = log.operation_details if isinstance(log.operation_details, dict) else json.loads(log.operation_details) if log.operation_details else {}

    action = details.get('action', '')
    user = details.get('user', '系统')

    if action == 'delete':
        # 恢复被删除的视频 - 通过修改现有记录的is_deleted字段
        video_data = details.get('video_data', {})

        # 根据日志中的biz_id查找原始视频记录
        video_id = int(log.biz_id) if log.biz_id and log.biz_id != '0' else None
        if not video_id:
            return jsonify({
                "code": 400,
                "msg": "无法确定要恢复的视频ID",
                "data": None
            }), 400

        # 查找已删除的视频记录
        video = Video.query.filter_by(id=video_id, is_deleted=1).first()
        if not video:
            # 如果找不到已删除的视频记录，可能需要根据其他信息查找
            # 首先尝试查找未删除的视频，以避免重复
            existing_video = Video.query.filter_by(id=video_id, is_deleted=0).first()
            if existing_video:
                return jsonify({
                    "code": 400,
                    "msg": "视频已存在，无法恢复",
                    "data": None
                }), 400

            # 如果找不到已删除的视频，尝试通过其他标识符查找
            video = Video.query.filter_by(id=video_id).first()
            if not video:
                return jsonify({
                    "code": 404,
                    "msg": "未找到要恢复的视频",
                    "data": None
                }), 404

        # 恢复视频：取消删除标记并清除删除信息
        video.is_deleted = 0
        video.delete_time = None
        video.delete_operator = None

        db.session.commit()

        # 创建恢复操作日志
        from app.models.business_operation_log import add_video_log
        restore_details = {
            "action": "restore",
            "user": user,
            "restored_data_type": "video",
            "restored_video_id": video.id,
            "original_log_id": log.id,
            "video_data": {
                "id": video.id,
                "title": video.title,
                "restore_message": f"通过日志恢复视频ID: {video.id}"
            }
        }

        add_video_log(
            video_id=video.id,
            operation_type='restore',
            operator_id=get_user_id_from_token(),
            details=restore_details
        )

        return jsonify({
            "code": 200,
            "msg": "视频恢复成功",
            "data": {"video_id": video.id}
        })

    elif action == 'update':
        # 恢复被修改的视频（使用旧数据）
        updated_fields = details.get('updated_fields', {})

        # 从更新字段中提取原始数据
        original_data = {}
        for field, values in updated_fields.items():
            original_data[field] = values.get('old')  # 使用旧值

        # 查找需要恢复的视频
        video_id = int(log.biz_id) if log.biz_id and log.biz_id != '0' else None
        if not video_id:
            return jsonify({
                "code": 400,
                "msg": "无法确定要恢复的视频ID",
                "data": None
            }), 400

        video = Video.query.get_or_404(video_id)

        # 恢复原始数据
        for field, value in original_data.items():
            if hasattr(video, field):
                setattr(video, field, value)

        # 更新搜索字段
        search_field = f"{video.title} {video.tags} {video.remark}"
        if video.machine_id:
            machine = Machine.query.filter_by(model=video.machine_id).first()
            if machine:
                search_field += f" {machine.model} {machine.original_model}"
        video.search_field = search_field

        db.session.commit()

        # 创建恢复操作日志
        from app.models.business_operation_log import add_video_log
        restore_details = {
            "action": "restore",
            "user": user,
            "restored_data_type": "video_update",
            "video_id": video_id,
            "original_log_id": log.id,
            "restored_fields": list(original_data.keys()),
            "video_data": video.to_dict()
        }

        add_video_log(
            video_id=video.id,
            operation_type='restore',
            operator_id=get_user_id_from_token(),
            details=restore_details
        )

        return jsonify({
            "code": 200,
            "msg": "视频修改恢复成功",
            "data": {"video_id": video.id}
        })

    elif action == 'physical_delete':
        # 物理删除的视频无法恢复，因为数据已被彻底删除
        return jsonify({
            "code": 400,
            "msg": "物理删除的视频无法恢复，数据已被彻底删除",
            "data": None
        }), 400

    else:
        return jsonify({
            "code": 400,
            "msg": "该日志类型不支持恢复操作",
            "data": None
        }), 400


def restore_photo_log(log):
    """恢复图片相关的日志"""
    from app.models.photo import Photo
    from app.models.machine_new import MachineNew as Machine
    import json
    from datetime import datetime

    # 解析日志详情
    details = log.operation_details if isinstance(log.operation_details, dict) else json.loads(log.operation_details) if log.operation_details else {}

    action = details.get('action', '')
    user = details.get('user', '系统')

    if action == 'delete':
        # 恢复被删除的照片 - 在当前实现中，照片删除是物理删除，无法恢复
        # 但我们可以记录操作尝试
        return jsonify({
            "code": 400,
            "msg": "照片删除是物理删除，无法通过日志恢复",
            "data": None
        }), 400

    elif action == 'update':
        # 恢复被修改的照片（使用旧数据）
        updated_fields = details.get('updated_fields', {})

        # 从更新字段中提取原始数据
        original_data = {}
        for field, values in updated_fields.items():
            original_data[field] = values.get('old')  # 使用旧值

        # 查找需要恢复的照片
        photo_id = int(log.biz_id) if log.biz_id and log.biz_id != '0' else None
        if not photo_id:
            return jsonify({
                "code": 400,
                "msg": "无法确定要恢复的照片ID",
                "data": None
            }), 400

        photo = Photo.query.get_or_404(photo_id)

        # 恢复原始数据
        for field, value in original_data.items():
            if hasattr(photo, field):
                setattr(photo, field, value)

        # 更新搜索字段
        search_field = f"{photo.title} {photo.tags} {photo.remark}"
        if photo.machine_id:
            machine = Machine.query.filter_by(model=photo.machine_id).first()
            if machine:
                search_field += f" {machine.model} {machine.original_model}"
        photo.search_field = search_field

        db.session.commit()

        # 创建恢复操作日志
        from app.models.business_operation_log import add_photo_log
        restore_details = {
            "action": "restore",
            "user": user,
            "restored_data_type": "photo_update",
            "photo_id": photo_id,
            "original_log_id": log.id,
            "restored_fields": list(original_data.keys()),
            "photo_data": photo.to_dict()
        }

        add_photo_log(
            photo_id=photo.id,
            operation_type='restore',
            operator_id=get_user_id_from_token(),
            details=restore_details
        )

        return jsonify({
            "code": 200,
            "msg": "照片修改恢复成功",
            "data": {"photo_id": photo.id}
        })

    else:
        return jsonify({
            "code": 400,
            "msg": "该日志类型不支持恢复操作",
            "data": None
        }), 400


def restore_employee_log(log):
    """恢复人员相关的日志"""
    # 人员恢复逻辑待实现
    return jsonify({
        "code": 400,
        "msg": "人员模块恢复功能待实现",
        "data": None
    }), 400


@log_bp.route('/reset-<module>-stats', methods=['POST'])
@route_permission(ROUTE_LOG_MANAGE)
def reset_statistics_by_module(module):
    """复位指定模块的统计数字（仅管理员）"""
    try:
        # 获取当前用户
        current_user = get_current_user()

        # 记录复位操作到日志
        details = {
            "action": "reset_stats",
            "user": current_user.name,
            "reset_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "module": module
        }

        # 创建复位操作日志
        log = BusinessOperationLog(
            module=module,
            biz_id="0",  # 统计复位不关联特定业务ID
            operation_type='reset_stats',
            operator_id=current_user.emp_id,
            operation_details=json.dumps(details, ensure_ascii=False)
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": f"{module}统计数字复位成功",
            "data": {
                "message": f"{module}统计数字复位成功",
                "reset_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"统计数字复位失败: {str(e)}",
            "data": None
        }), 500