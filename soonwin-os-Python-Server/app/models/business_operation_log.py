"""
通用业务操作日志模型
适配询盘/视频/图片/人员等所有管理功能
"""
from extensions import db
from datetime import datetime
from app.models.employee import Employee
import json


class BusinessOperationLog(db.Model):
    """
    通用业务操作日志表（适配询盘/视频/图片/人员等所有管理功能）
    """
    __tablename__ = "business_operation_log"  # 统一表名，避免模块专属命名

    # 通用核心字段（所有模块必选）
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    module = db.Column(db.String(50), nullable=False, comment="业务模块：inquiry(询盘)/video(视频)/image(图片)/employee(人员)")
    biz_id = db.Column(db.String(50), nullable=False, comment="业务关联ID（如询盘ID/视频ID/人员ID，统一字符串类型兼容不同模块主键类型）")
    operation_type = db.Column(db.String(50), nullable=False, comment="操作类型：create/update/delete/reset_stats/upload/delete_file等")
    operator_id = db.Column(db.String(20), db.ForeignKey('Employee.emp_id'), nullable=False, comment="操作人ID")
    operator = db.relationship('Employee', lazy='joined')  # 关联操作人信息，lazy=joined减少查询次数
    operation_details = db.Column(db.Text, comment="操作详情（JSON字符串，存储原始数据，用于溯源/恢复/前端转译）")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="日志创建时间")

    def to_dict(self):
        """
        通用序列化方法，适配所有模块
        前端可根据module+operation_type解析operation_details中的JSON数据进行转译展示
        """
        # 解析JSON格式的操作详情，失败则返回原始字符串
        try:
            operation_details = json.loads(self.operation_details) if self.operation_details else {}
        except json.JSONDecodeError:
            operation_details = self.operation_details

        return {
            "id": self.id,
            "module": self.module,
            "biz_id": self.biz_id,
            "operation_type": self.operation_type,
            "operator_info": {
                "id": self.operator_id,
                "name": self.operator.name if self.operator else None,
                "role": self.operator.user_role if self.operator else None
            },
            "operation_details": operation_details,  # 解析后的JSON（前端可直接转译）
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }


# ------------------------------
# 兼容原有询盘日志的适配器函数（平滑迁移）
# ------------------------------
def add_inquiry_log(inquiry_id, operation_type, operator_id, details):
    """
    新增询盘日志（适配通用日志表）
    :param inquiry_id: 询盘ID
    :param operation_type: 操作类型（create/update/delete/reset_stats）
    :param operator_id: 操作人ID
    :param details: 询盘专属详情（dict），不包含统计信息，仅记录操作详情
    """
    # 确保details是字典格式
    if isinstance(details, str):
        try:
            details_dict = json.loads(details)
        except json.JSONDecodeError:
            details_dict = {"raw_details": details}
    else:
        details_dict = details if details else {}

    log = BusinessOperationLog(
        module="inquiry",  # 模块标识：询盘
        biz_id=str(inquiry_id),  # 统一转为字符串，兼容不同模块主键类型
        operation_type=operation_type,
        operator_id=operator_id,
        operation_details=json.dumps(details_dict, ensure_ascii=False)  # 原始数据JSON化存储
    )
    db.session.add(log)
    db.session.commit()
    return log


# ------------------------------
# 视频管理日志适配器函数
# ------------------------------
def add_video_log(video_id, operation_type, operator_id, details):
    """
    新增视频日志
    :param video_id: 视频ID
    :param operation_type: 操作类型（upload/delete/edit/gen_thumbnail等）
    :param operator_id: 操作人ID
    :param details: 视频专属详情（dict），如文件路径、大小、分辨率等
    """
    # 确保details是字典格式
    if isinstance(details, str):
        try:
            details_dict = json.loads(details)
        except json.JSONDecodeError:
            details_dict = {"raw_details": details}
    else:
        details_dict = details if details else {}

    log = BusinessOperationLog(
        module="video",  # 模块标识：视频
        biz_id=str(video_id),
        operation_type=operation_type,
        operator_id=operator_id,
        operation_details=json.dumps(details_dict, ensure_ascii=False)
    )
    db.session.add(log)
    db.session.commit()
    return log


# ------------------------------
# 人员管理日志适配器函数
# ------------------------------
def add_employee_log(emp_id, operation_type, operator_id, details):
    """
    新增人员管理日志
    :param emp_id: 人员ID
    :param operation_type: 操作类型（create/update/delete/change_role等）
    :param operator_id: 操作人ID
    :param details: 人员专属详情（dict），如姓名、角色、部门变更等
    """
    # 确保details是字典格式
    if isinstance(details, str):
        try:
            details_dict = json.loads(details)
        except json.JSONDecodeError:
            details_dict = {"raw_details": details}
    else:
        details_dict = details if details else {}

    log = BusinessOperationLog(
        module="employee",  # 模块标识：人员
        biz_id=str(emp_id),
        operation_type=operation_type,
        operator_id=operator_id,
        operation_details=json.dumps(details_dict, ensure_ascii=False)
    )
    db.session.add(log)
    db.session.commit()
    return log


# ------------------------------
# 图片管理日志适配器函数
# ------------------------------
def add_photo_log(photo_id, operation_type, operator_id, details):
    """
    新增图片日志
    :param photo_id: 图片ID
    :param operation_type: 操作类型（upload/delete/edit等）
    :param operator_id: 操作人ID
    :param details: 图片专属详情（dict），如文件路径、尺寸、关联机器等
    """
    # 确保details是字典格式
    if isinstance(details, str):
        try:
            details_dict = json.loads(details)
        except json.JSONDecodeError:
            details_dict = {"raw_details": details}
    else:
        details_dict = details if details else {}

    log = BusinessOperationLog(
        module="photo",  # 模块标识：图片
        biz_id=str(photo_id),
        operation_type=operation_type,
        operator_id=operator_id,
        operation_details=json.dumps(details_dict, ensure_ascii=False)
    )
    db.session.add(log)
    db.session.commit()
    return log


# ------------------------------
# 订单管理日志适配器函数
# ------------------------------
def add_order_log(order_id, operation_type, operator_id, details):
    """
    新增订单日志
    :param order_id: 订单ID
    :param operation_type: 操作类型（create/update/delete等）
    :param operator_id: 操作人ID
    :param details: 订单专属详情（dict），如订单信息、变更字段等
    """
    # 确保details是字典格式
    if isinstance(details, str):
        try:
            details_dict = json.loads(details)
        except json.JSONDecodeError:
            details_dict = {"raw_details": details}
    else:
        details_dict = details if details else {}

    log = BusinessOperationLog(
        module="order",  # 模块标识：订单
        biz_id=str(order_id),
        operation_type=operation_type,
        operator_id=operator_id,
        operation_details=json.dumps(details_dict, ensure_ascii=False)
    )
    db.session.add(log)
    db.session.commit()
    return log


# ------------------------------
# 通用查询函数
# ------------------------------
def get_logs_by_module(module_name, page=1, size=10, operation_type=None, operator_name=None, start_date=None, end_date=None):
    """
    根据模块查询日志
    :param module_name: 模块名称
    :param page: 页码
    :param size: 每页数量
    :param operation_type: 操作类型
    :param operator_name: 操作人姓名
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 日志列表和总数
    """
    query = BusinessOperationLog.query.filter(BusinessOperationLog.module == module_name)

    # 应用筛选条件
    if operation_type:
        query = query.filter(BusinessOperationLog.operation_type.contains(operation_type))
    if operator_name:
        query = query.join(Employee).filter(Employee.name.contains(operator_name))
    if start_date:
        query = query.filter(BusinessOperationLog.create_time >= start_date)
    if end_date:
        query = query.filter(BusinessOperationLog.create_time < end_date)

    # 计算总数
    total = query.count()

    # 应用分页和排序
    logs = query.order_by(BusinessOperationLog.create_time.desc()).offset((page - 1) * size).limit(size).all()

    return logs, total


def delete_logs_by_module(module_name, log_id=None):
    """
    删除指定模块的日志
    :param module_name: 模块名称
    :param log_id: 日志ID，如果为None则删除该模块的所有日志
    :return: 删除的记录数
    """
    if log_id:
        query = BusinessOperationLog.query.filter(
            BusinessOperationLog.module == module_name,
            BusinessOperationLog.id == log_id
        )
    else:
        query = BusinessOperationLog.query.filter(BusinessOperationLog.module == module_name)

    deleted_count = query.delete()
    db.session.commit()
    return deleted_count