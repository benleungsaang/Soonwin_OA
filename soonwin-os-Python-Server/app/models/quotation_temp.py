from extensions import db
from datetime import datetime
from decimal import Decimal
import json


class QuotationTemp(db.Model):
    __tablename__ = "QuotationTemp"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_mark = db.Column(db.String(100), nullable=False, comment="订单标识")
    machine_list = db.Column(db.Text, comment="设备列表JSON字符串")
    temp_params = db.Column(db.Text, comment="自定义参数列表JSON字符串")
    total_amount = db.Column(db.Numeric(12, 2), default=0, comment="总金额")
    creator_id = db.Column(db.String(20), db.ForeignKey('Employee.emp_id'), comment="创建人ID")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    remark = db.Column(db.Text, comment="备注")

    def to_dict(self):
        """将对象转换为字典格式"""
        return {
            "id": self.id,
            "order_mark": self.order_mark,
            "machine_list": json.loads(self.machine_list) if self.machine_list else [],
            "temp_params": json.loads(self.temp_params) if self.temp_params else [],
            "total_amount": float(self.total_amount) if self.total_amount else 0.0,
            "creator_id": self.creator_id,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            "remark": self.remark
        }

    @staticmethod
    def from_dict(data):
        """从字典创建对象"""
        return QuotationTemp(
            order_mark=data.get('order_mark'),
            machine_list=json.dumps(data.get('machine_list', [])),
            temp_params=json.dumps(data.get('temp_params', [])),
            total_amount=data.get('total_amount', 0),
            creator_id=data.get('creator_id'),
            remark=data.get('remark', '')
        )