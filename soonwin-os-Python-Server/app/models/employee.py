from extensions import db
from datetime import datetime
import uuid

class UserStatus:
    """用户状态枚举"""
    PENDING_BINDING = "pending_binding"  # 待绑定
    PENDING_APPROVAL = "pending_approval"  # 待审批
    ACTIVE = "active"  # 激活
    INACTIVE = "inactive"  # 停用

class Employee(db.Model):
    __tablename__ = "Employee"  # 对应数据库表名
    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4, comment="UUID主键")
    name = db.Column(db.String(50), nullable=False, comment="员工姓名")
    emp_id = db.Column(db.String(20), unique=True, nullable=False, comment="工号（唯一标识）")
    dept = db.Column(db.String(50), comment="部门")
    device_id = db.Column(db.String(100), comment="设备ID")
    inner_ip = db.Column(db.String(20), nullable=False, comment="内网IP")
    user_role = db.Column(db.String(10), default='user', comment="用户角色（admin/sales/user）")
    status = db.Column(db.String(20), default=UserStatus.PENDING_BINDING, comment="用户状态")
    remarks = db.Column(db.Text, comment="备注信息")
    last_login_time = db.Column(db.DateTime, comment="上次登录时间")
    login_device = db.Column(db.String(100), comment="登录设备")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")

    # 定义序列化方法，便于接口返回JSON数据
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "emp_id": self.emp_id,
            "dept": self.dept,
            "device_id": self.device_id,
            "inner_ip": self.inner_ip,
            "user_role": self.user_role,
            "status": self.status,
            "remarks": self.remarks,
            "last_login_time": self.last_login_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_login_time else None,
            "login_device": self.login_device,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }