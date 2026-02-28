from extensions import db
from datetime import datetime
import uuid
import json


# 操作类型枚举（覆盖所有考勤操作）
class OperationType:
    LEAVE = "leave"  # 请假
    OVERTIME = "overtime"  # 加班
    MAKE_UP = "make_up"  # 补卡
    APPEAL = "appeal"  # 迟到/早退申诉
    BUSINESS_TRIP = "business_trip"  # 出差
    ADJUST = "adjust"  # 管理员手动调整


# 操作状态枚举
class OperationStatus:
    DRAFT = "draft"  # 草稿
    SUBMITTED = "submitted"  # 已提交
    APPROVING = "approving"  # 审批中
    APPROVED = "approved"  # 审批通过
    REJECTED = "rejected"  # 审批驳回
    CANCELLED = "cancelled"  # 已撤销


class AttendanceOperation(db.Model):
    __tablename__ = "AttendanceOperation"  # 对应数据库表名
    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4, comment="UUID主键")
    emp_id = db.Column(db.String(20), nullable=False, comment="关联员工工号（关联Employee表）")
    name = db.Column(db.String(50), nullable=False, comment="员工姓名（冗余存储，避免联表查询）")
    operation_type = db.Column(db.String(20), nullable=False, comment=f"操作类型：{','.join([OperationType.LEAVE, OperationType.OVERTIME, OperationType.MAKE_UP, OperationType.APPEAL, OperationType.BUSINESS_TRIP, OperationType.ADJUST])}")
    operation_status = db.Column(db.String(20), default=OperationStatus.DRAFT, comment=f"操作状态：{','.join([OperationStatus.DRAFT, OperationStatus.SUBMITTED, OperationStatus.APPROVING, OperationStatus.APPROVED, OperationStatus.REJECTED, OperationStatus.CANCELLED])}")
    start_time = db.Column(db.DateTime, nullable=False, comment="操作开始时间（如请假开始、补卡日期）")
    end_time = db.Column(db.DateTime, comment="操作结束时间（如请假结束、加班结束；补卡可与start_time一致）")
    duration = db.Column(db.Float, comment="操作时长（小时/天，如请假2天、加班3.5小时）")
    reason = db.Column(db.Text, nullable=False, comment="操作原因/事由")
    approver_id = db.Column(db.String(20), comment="审批人工号（关联Employee表的emp_id）")
    approver_name = db.Column(db.String(50), comment="审批人姓名（冗余存储）")
    approve_time = db.Column(db.DateTime, comment="审批通过/驳回时间")
    approve_opinion = db.Column(db.Text, comment="审批意见")
    attachment = db.Column(db.Text, comment="附件路径（多个附件用英文逗号分隔，如'/uploads/1.pdf,/uploads/2.png'）")
    # 扩展字段：存储各操作的差异化信息（SQLite无JSON类型，用Text存储JSON字符串）
    extend_info = db.Column(db.Text, comment="扩展信息（JSON字符串，存储各操作特有字段）")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="记录创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="记录最后修改时间")

    # 序列化方法，适配前端数据格式
    def to_dict(self):
        # 解析JSON扩展字段，避免前端处理字符串
        extend_info = json.loads(self.extend_info) if self.extend_info else {}
        return {
            "id": str(self.id),
            "emp_id": self.emp_id,
            "name": self.name,
            "operation_type": self.operation_type,
            "operation_status": self.operation_status,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None,
            "duration": self.duration,
            "reason": self.reason,
            "approver_id": self.approver_id,
            "approver_name": self.approver_name,
            "approve_time": self.approve_time.strftime("%Y-%m-%d %H:%M:%S") if self.approve_time else None,
            "approve_opinion": self.approve_opinion,
            "attachment": self.attachment.split(",") if self.attachment else [],  # 转成数组方便前端展示
            "extend_info": extend_info,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None
        }

    # 便捷方法：设置扩展信息（传入字典自动转JSON）
    def set_extend_info(self, info_dict):
        self.extend_info = json.dumps(info_dict, ensure_ascii=False)