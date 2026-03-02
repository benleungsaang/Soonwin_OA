from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from extensions import db
from app.models.attendance_operation import AttendanceOperation, OperationType, OperationStatus
from app.models.employee import Employee
from app.models.punch_record import PunchRecord
from app.utils.simple_auth_utils import route_permission
from app.constants.simple_permission_constants import ROUTE_ATTENDANCE
from app.utils.auth_utils import get_user_id_from_token, get_user_role_from_token
import json
from decimal import Decimal

# 创建蓝图
attendance_bp = Blueprint('attendance', __name__)

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

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

@attendance_bp.route('/attendance/operation', methods=['POST'])
@route_permission(ROUTE_ATTENDANCE)
def submit_operation():
    """提交考勤操作申请"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 获取当前用户信息
        current_user = get_current_user()
        if not current_user.emp_id:
            return jsonify({
                "code": 401,
                "msg": "无法获取当前用户信息",
                "data": None
            }), 401

        # 验证必要字段
        required_fields = ['operation_type', 'start_time', 'reason']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "code": 400,
                    "msg": f"缺少必要字段: {field}",
                    "data": None
                }), 400

        # 如果未提供emp_id或name，使用当前用户信息
        if 'emp_id' not in data:
            data['emp_id'] = current_user.emp_id
        if 'name' not in data:
            data['name'] = current_user.name

        # 验证操作类型
        valid_operation_types = [
            OperationType.LEAVE, OperationType.OVERTIME, OperationType.MAKE_UP,
            OperationType.APPEAL, OperationType.BUSINESS_TRIP, OperationType.ADJUST
        ]
        if data['operation_type'] not in valid_operation_types:
            return jsonify({
                "code": 400,
                "msg": "无效的操作类型",
                "data": None
            }), 400

        # 验证操作状态
        valid_status = [
            OperationStatus.DRAFT, OperationStatus.SUBMITTED, OperationStatus.APPROVING,
            OperationStatus.APPROVED, OperationStatus.REJECTED, OperationStatus.CANCELLED
        ]

        # 设置默认状态
        status = data.get('operation_status', OperationStatus.SUBMITTED)
        if status not in valid_status:
            return jsonify({
                "code": 400,
                "msg": "无效的操作状态",
                "data": None
            }), 400

        # 处理附件
        attachment = None
        if 'attachment' in data and data['attachment']:
            if isinstance(data['attachment'], list):
                attachment = ','.join(data['attachment'])
            else:
                attachment = data['attachment']

        # 处理扩展信息
        extend_info = None
        if 'extend_info' in data and data['extend_info']:
            import json
            extend_info = json.dumps(data['extend_info'], ensure_ascii=False)

        # 创建考勤操作记录
        attendance_operation = AttendanceOperation(
            emp_id=data['emp_id'],
            name=data['name'],
            operation_type=data['operation_type'],
            operation_status=status,
            start_time=datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S') if data['start_time'] else None,
            end_time=datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S') if data.get('end_time') else None,
            duration=data.get('duration'),
            reason=data['reason'],
            attachment=attachment,
            extend_info=extend_info
        )

        db.session.add(attendance_operation)
        db.session.commit()

        # 序列化创建的记录
        operation_data = attendance_operation.to_dict()

        from flask import Response
        response_data = {
            "code": 200,
            "msg": "考勤操作申请提交成功",
            "data": operation_data
        }
        # 使用自定义编码器处理特殊数据类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')

    except ValueError as ve:
        db.session.rollback()
        return jsonify({
            "code": 400,
            "msg": f"日期格式错误: {str(ve)}",
            "data": None
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"提交考勤操作申请失败: {str(e)}",
            "data": None
        }), 500


@attendance_bp.route('/attendance/my-operations', methods=['GET'])
@route_permission(ROUTE_ATTENDANCE)
def get_my_operations():
    """获取当前员工的考勤操作列表"""
    try:
        # 获取查询参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        operation_type = request.args.get('operation_type')
        status = request.args.get('status')

        # 获取当前用户信息
        current_user = get_current_user()
        if not current_user.emp_id:
            return jsonify({
                "code": 401,
                "msg": "无法获取当前用户信息",
                "data": None
            }), 401

        # 构建查询条件
        query = AttendanceOperation.query.filter_by(emp_id=current_user.emp_id)

        if start_time:
            start_time_obj = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            query = query.filter(AttendanceOperation.start_time >= start_time_obj)

        if end_time:
            end_time_obj = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            query = query.filter(AttendanceOperation.end_time <= end_time_obj)

        if operation_type:
            query = query.filter_by(operation_type=operation_type)

        if status:
            query = query.filter_by(operation_status=status)

        # 执行查询并返回结果
        operations = query.all()
        operations_data = [op.to_dict() for op in operations]

        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取考勤操作列表成功",
            "data": operations_data
        }
        # 使用自定义编码器处理特殊数据类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')

    except ValueError as ve:
        return jsonify({
            "code": 400,
            "msg": f"日期格式错误: {str(ve)}",
            "data": None
        }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取考勤操作列表失败: {str(e)}",
            "data": None
        }), 500


@attendance_bp.route('/attendance/approval-list', methods=['GET'])
@route_permission(ROUTE_ATTENDANCE)
def get_approval_list():
    """管理员获取待审批列表"""
    try:
        # 检查用户权限 - 只有管理员可以访问
        current_user = get_current_user()
        if current_user.user_role != 'admin':
            return jsonify({
                "code": 403,
                "msg": "权限不足，仅管理员可访问",
                "data": None
            }), 403

        # 获取查询参数
        status = request.args.get('status', OperationStatus.APPROVING)

        # 构建查询条件，只获取需要审批的记录
        query = AttendanceOperation.query

        if status:
            query = query.filter_by(operation_status=status)
        else:
            query = query.filter(AttendanceOperation.operation_status.in_([
                OperationStatus.SUBMITTED, OperationStatus.APPROVING
            ]))

        # 执行查询并返回结果
        operations = query.all()
        operations_data = [op.to_dict() for op in operations]

        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取审批列表成功",
            "data": operations_data
        }
        # 使用自定义编码器处理特殊数据类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取审批列表失败: {str(e)}",
            "data": None
        }), 500


@attendance_bp.route('/attendance/operation/<operation_id>/approve', methods=['PUT'])
@route_permission(ROUTE_ATTENDANCE)
def approve_operation(operation_id):
    """审批考勤操作"""
    try:
        # 检查用户权限 - 只有管理员可以访问
        current_user = get_current_user()
        if current_user.user_role != 'admin':
            return jsonify({
                "code": 403,
                "msg": "权限不足，仅管理员可访问",
                "data": None
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 验证必要字段
        if 'status' not in data:
            return jsonify({
                "code": 400,
                "msg": "缺少必要字段: status",
                "data": None
            }), 400

        # 验证状态值
        valid_status = [OperationStatus.APPROVED, OperationStatus.REJECTED]
        if data['status'] not in valid_status:
            return jsonify({
                "code": 400,
                "msg": "无效的操作状态",
                "data": None
            }), 400

        # 查找考勤操作记录
        # 将字符串类型的operation_id转换为UUID格式用于查询
        try:
            import uuid
            uuid_obj = uuid.UUID(operation_id)
            operation = AttendanceOperation.query.filter_by(id=uuid_obj).first()
        except ValueError:
            return jsonify({
                "code": 400,
                "msg": "无效的操作ID格式",
                "data": None
            }), 400

        if not operation:
            return jsonify({
                "code": 400,
                "msg": "考勤操作记录不存在",
                "data": None
            }), 400

        # 更新审批信息
        operation.operation_status = data['status']
        operation.approver_id = current_user.emp_id
        operation.approver_name = current_user.name
        operation.approve_time = datetime.now()
        operation.approve_opinion = data.get('opinion', '')

        db.session.commit()

        # 序列化更新后的记录
        operation_data = operation.to_dict()

        from flask import Response
        response_data = {
            "code": 200,
            "msg": "审批操作成功",
            "data": operation_data
        }
        # 使用自定义编码器处理特殊数据类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"审批操作失败: {str(e)}",
            "data": None
        }), 500


@attendance_bp.route('/attendance/operation/<operation_id>/adjust', methods=['PUT'])
@route_permission(ROUTE_ATTENDANCE)
def adjust_operation(operation_id):
    """管理员手动调整考勤记录"""
    try:
        # 检查用户权限 - 只有管理员可以访问
        current_user = get_current_user()
        if current_user.user_role != 'admin':
            return jsonify({
                "code": 403,
                "msg": "权限不足，仅管理员可访问",
                "data": None
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 查找考勤操作记录
        # 将字符串类型的operation_id转换为UUID格式用于查询
        try:
            import uuid
            uuid_obj = uuid.UUID(operation_id)
            operation = AttendanceOperation.query.filter_by(id=uuid_obj).first()
        except ValueError:
            return jsonify({
                "code": 400,
                "msg": "无效的操作ID格式",
                "data": None
            }), 400

        if not operation:
            return jsonify({
                "code": 400,
                "msg": "考勤操作记录不存在",
                "data": None
            }), 400

        # 更新允许的字段
        updatable_fields = [
            'operation_status', 'start_time', 'end_time', 'duration', 'reason',
            'approver_id', 'approver_name', 'approve_time', 'approve_opinion',
            'attachment', 'extend_info'
        ]

        for field in updatable_fields:
            if field in data:
                if field in ['start_time', 'end_time', 'approve_time']:
                    # 如果是日期时间字段，需要转换
                    if data[field]:
                        setattr(operation, field, datetime.strptime(data[field], '%Y-%m-%d %H:%M:%S'))
                    else:
                        setattr(operation, field, None)
                elif field == 'attachment':
                    # 处理附件字段
                    if isinstance(data[field], list):
                        setattr(operation, field, ','.join(data[field]))
                    else:
                        setattr(operation, field, data[field])
                elif field == 'extend_info':
                    # 处理扩展信息字段
                    import json
                    if data[field]:
                        setattr(operation, field, json.dumps(data[field], ensure_ascii=False))
                    else:
                        setattr(operation, field, None)
                else:
                    setattr(operation, field, data[field])

        db.session.commit()

        # 序列化更新后的记录
        operation_data = operation.to_dict()

        from flask import Response
        response_data = {
            "code": 200,
            "msg": "调整考勤记录成功",
            "data": operation_data
        }
        # 使用自定义编码器处理特殊数据类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')

    except ValueError as ve:
        db.session.rollback()
        return jsonify({
            "code": 400,
            "msg": f"日期格式错误: {str(ve)}",
            "data": None
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"调整考勤记录失败: {str(e)}",
            "data": None
        }), 500


@attendance_bp.route('/attendance/operations', methods=['GET'])
@route_permission(ROUTE_ATTENDANCE)
def get_operations():
    """获取考勤操作记录列表 - 管理员查看所有，普通用户查看自己的"""
    try:
        # 获取当前用户信息
        current_user = get_current_user()
        if not current_user.emp_id:
            return jsonify({
                "code": 401,
                "msg": "无法获取当前用户信息",
                "data": None
            }), 401

        # 获取查询参数
        emp_id = request.args.get('emp_id')
        operation_type = request.args.get('operation_type')
        status = request.args.get('status')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        # 构建查询条件
        query = AttendanceOperation.query

        # 根据用户角色决定查询范围
        if current_user.user_role != 'admin':
            # 普通用户只能查看自己的记录
            query = query.filter_by(emp_id=current_user.emp_id)
        else:
            # 管理员可以查看所有记录，但如果指定了emp_id参数，则按参数过滤
            if emp_id:
                query = query.filter_by(emp_id=emp_id)

        if operation_type:
            query = query.filter_by(operation_type=operation_type)

        if status:
            query = query.filter_by(operation_status=status)

        if start_time:
            start_time_obj = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            query = query.filter(AttendanceOperation.start_time >= start_time_obj)

        if end_time:
            end_time_obj = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            query = query.filter(AttendanceOperation.end_time <= end_time_obj)

        # 按创建时间倒序排列（最新在前）
        query = query.order_by(AttendanceOperation.create_time.desc())
        # 执行查询并返回结果
        operations = query.all()
        operations_data = [op.to_dict() for op in operations]

        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取考勤操作列表成功",
            "data": operations_data
        }
        # 使用自定义编码器处理特殊数据类型
        json_response = json.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')

    except ValueError as ve:
        return jsonify({
            "code": 400,
            "msg": f"日期格式错误: {str(ve)}",
            "data": None
        }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取考勤操作列表失败: {str(e)}",
            "data": None
        }), 500


@attendance_bp.route('/attendance/operation/<operation_id>', methods=['DELETE'])
@route_permission(ROUTE_ATTENDANCE)
def delete_operation(operation_id):
    """删除考勤操作申请"""
    try:
        from uuid import UUID
        import os

        # 验证操作ID格式
        try:
            uuid_obj = UUID(operation_id)
        except ValueError:
            return jsonify({
                "code": 400,
                "msg": "无效的考勤操作ID",
                "data": None
            }), 400

        # 获取当前用户信息
        current_user = get_current_user()
        if not current_user.emp_id:
            return jsonify({
                "code": 401,
                "msg": "无法获取当前用户信息",
                "data": None
            }), 401

        # 查找考勤操作记录 - 使用UUID对象进行查询
        operation = AttendanceOperation.query.filter_by(id=uuid_obj).first()
        if not operation:
            return jsonify({
                "code": 404,
                "msg": "考勤操作记录不存在",
                "data": None
            }), 404

        # 检查权限：管理员可删除所有记录，普通用户只能删除自己的记录
        if current_user.user_role != 'admin' and operation.emp_id != current_user.emp_id:
            return jsonify({
                "code": 403,
                "msg": "权限不足，无法删除该考勤操作",
                "data": None
            }), 403

        # 获取附件路径，准备删除文件
        attachments_to_delete = []
        if operation.attachment:
            # 如果附件字段存储的是逗号分隔的路径列表
            if isinstance(operation.attachment, str):
                attachments_to_delete = operation.attachment.split(',')
            else:
                attachments_to_delete = operation.attachment

        # 删除考勤操作记录
        db.session.delete(operation)
        db.session.commit()

        # 删除对应的附件文件
        deleted_files = []
        for attachment_path in attachments_to_delete:
            # 确保路径是安全的，防止路径遍历攻击
            attachment_path = attachment_path.strip()
            if attachment_path:
                # 构建完整路径，使用相对路径
                full_path = os.path.abspath(os.path.join(".", attachment_path.lstrip('/')))
                assets_dir = os.path.abspath(os.path.join(".", "assets"))

                # 验证路径是否在assets目录下，防止路径遍历攻击
                if full_path.startswith(assets_dir) and os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                        deleted_files.append(attachment_path)
                    except Exception as e:
                        print(f"删除附件失败 {attachment_path}: {str(e)}")
                        # 继续处理其他文件，不中断删除流程

        return jsonify({
            "code": 200,
            "msg": "考勤操作删除成功",
            "data": {
                "deleted_files": deleted_files
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除考勤操作失败: {str(e)}",
            "data": None
        }), 500


@attendance_bp.route('/attendance/export-json', methods=['GET'])
@route_permission(ROUTE_ATTENDANCE)
def export_attendance_json():
    """导出考勤数据到JSON格式"""
    try:
        from flask import request
        import json as json_module
        from datetime import datetime
        import calendar

        # 获取当前用户信息
        current_user = get_current_user()
        if current_user.user_role != 'admin':
            return jsonify({
                "code": 403,
                "msg": "权限不足，仅管理员可导出考勤数据",
                "data": None
            }), 403

        # 获取参数
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)

        if not year or not month:
            return jsonify({
                "code": 400,
                "msg": "年份和月份不能为空",
                "data": None
            }), 400

        # 获取当月的打卡记录
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        punch_records = PunchRecord.query.filter(
            PunchRecord.punch_time >= start_date,
            PunchRecord.punch_time < end_date
        ).all()

        # 获取当月的考勤操作
        attendance_ops = AttendanceOperation.query.filter(
            AttendanceOperation.start_time >= start_date,
            AttendanceOperation.start_time < end_date
        ).all()

        # 获取员工信息
        employees = Employee.query.all()

        # 准备返回数据
        result = {
            "export_info": {
                "year": year,
                "month": month,
                "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_employees": len(employees),
                "total_punch_records": len(punch_records),
                "total_attendance_ops": len(attendance_ops)
            },
            "employees": [
                {
                    "emp_id": emp.emp_id,
                    "name": emp.name,
                    "dept": emp.dept,
                    "inner_ip": emp.inner_ip,
                    "user_role": emp.user_role,
                    "status": emp.status,
                    "create_time": emp.create_time.strftime('%Y-%m-%d %H:%M:%S') if emp.create_time else None,
                    "update_time": emp.update_time.strftime('%Y-%m-%d %H:%M:%S') if emp.update_time else None
                } for emp in employees
            ],
            "punchRecords": [
                {
                    "id": pr.id,
                    "emp_id": pr.emp_id,
                    "name": pr.name,
                    "punch_type": pr.punch_type,
                    "punch_time": pr.punch_time.strftime('%Y-%m-%d %H:%M:%S') if pr.punch_time else None,
                    "inner_ip": pr.inner_ip,
                    "device_id": pr.device_id,
                    "last_login_time": pr.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if pr.last_login_time else None,
                    "login_device": pr.login_device
                } for pr in punch_records
            ],
            "attendanceOperations": [
                {
                    "id": str(op.id),
                    "emp_id": op.emp_id,
                    "name": op.name,
                    "operation_type": op.operation_type,
                    "operation_status": op.operation_status,
                    "start_time": op.start_time.strftime('%Y-%m-%d %H:%M:%S') if op.start_time else None,
                    "end_time": op.end_time.strftime('%Y-%m-%d %H:%M:%S') if op.end_time else None,
                    "duration": op.duration,
                    "reason": op.reason,
                    "approver_id": op.approver_id,
                    "approver_name": op.approver_name,
                    "approve_time": op.approve_time.strftime('%Y-%m-%d %H:%M:%S') if op.approve_time else None,
                    "approve_opinion": op.approve_opinion,
                    "attachment": op.attachment.split(",") if op.attachment else [],
                    "extend_info": json_module.loads(op.extend_info) if op.extend_info else {},
                    "create_time": op.create_time.strftime('%Y-%m-%d %H:%M:%S') if op.create_time else None,
                    "update_time": op.update_time.strftime('%Y-%m-%d %H:%M:%S') if op.update_time else None
                } for op in attendance_ops
            ]
        }

        # 返回JSON数据
        from flask import Response
        response_data = {
            "code": 200,
            "msg": "获取考勤导出数据成功",
            "data": result
        }
        # 使用自定义编码器处理特殊数据类型
        json_response = json_module.dumps(response_data, cls=DecimalEncoder, ensure_ascii=False)
        return Response(json_response, mimetype='application/json')

    except ValueError as ve:
        return jsonify({
            "code": 400,
            "msg": f"参数格式错误: {str(ve)}",
            "data": None
        }), 400
    except Exception as e:
        print(f"导出考勤数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "code": 500,
            "msg": f"导出考勤数据失败: {str(e)}",
            "data": None
        }), 500