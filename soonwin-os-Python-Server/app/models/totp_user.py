from extensions import db
from datetime import datetime

class TotpUser(db.Model):
    __tablename__ = "TotpUser"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    emp_id = db.Column(db.String(20), unique=True, nullable=False, comment="关联员工工号")
    name = db.Column(db.String(50), nullable=False, comment="员工姓名")
    totp_secret = db.Column(db.String(16), nullable=False, comment="TOTP密钥（唯一）")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")