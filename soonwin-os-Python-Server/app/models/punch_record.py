from extensions import db
from datetime import datetime

class PunchRecord(db.Model):
    __tablename__ = "PunchRecord"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    emp_id = db.Column(db.String(20), nullable=False, comment="关联员工工号")
    name = db.Column(db.String(50), nullable=False, comment="员工姓名")
    punch_type = db.Column(db.String(20), nullable=False, comment="打卡类型（上班/下班）")
    punch_time = db.Column(db.DateTime, default=datetime.now, comment="打卡时间")
    inner_ip = db.Column(db.String(20), comment="打卡设备IP")
    phone_mac = db.Column(db.String(20), comment="打卡设备MAC地址")