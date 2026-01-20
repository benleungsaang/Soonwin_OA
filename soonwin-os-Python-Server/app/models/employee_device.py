from extensions import db
from datetime import datetime

class EmployeeDevice(db.Model):
    __tablename__ = "EmployeeDevice"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    emp_id = db.Column(db.String(20), db.ForeignKey('Employee.emp_id', ondelete='CASCADE'), nullable=False, comment="关联员工工号")
    device_mac = db.Column(db.String(20), unique=True, nullable=False, comment="设备MAC地址")
    device_ip = db.Column(db.String(20), comment="设备IP地址")
    device_type = db.Column(db.String(50), comment="设备类型")
    device_info = db.Column(db.String(200), comment="设备详细信息")
    is_primary = db.Column(db.Boolean, default=False, comment="是否为主设备")
    created_at = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 建立与Employee表的外键关系，配置级联删除
    employee = db.relationship('Employee', backref=db.backref('devices', lazy=True, cascade='all, delete-orphan'))