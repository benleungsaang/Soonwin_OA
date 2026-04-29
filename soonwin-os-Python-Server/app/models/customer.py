"""
客户信息模块数据模型
用于集中管理客户基础信息，支持从询盘或订单记录导入
"""

from extensions import db
from datetime import datetime


class Customer(db.Model):
    """客户信息表"""
    __tablename__ = "Customer"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="客户ID")
    company_name = db.Column(db.String(200), nullable=False, comment="公司名称")
    contact_person = db.Column(db.String(100), nullable=False, comment="联系人")
    phone = db.Column(db.String(50), comment="电话")
    email = db.Column(db.String(100), comment="邮箱")
    area = db.Column(db.String(100), comment="地区")
    customer_type = db.Column(db.String(20), comment="客户类型(经销商/终端)")
    source = db.Column(db.String(20), comment="客户来源(inquiry/order_record/manual)")
    source_id = db.Column(db.Integer, comment="来源记录ID(询盘或订单记录ID)")
    remark = db.Column(db.Text, comment="备注")
    search_field = db.Column(db.Text, comment="搜索字段")
    creator_id = db.Column(db.String(20), db.ForeignKey('Employee.emp_id'), comment="创建人ID")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联
    creator = db.relationship('Employee', foreign_keys=[creator_id], backref=db.backref('customers', lazy=True))

    def update_search_field(self):
        """更新搜索字段"""
        search_values = [
            self.company_name or '',
            self.contact_person or '',
            self.phone or '',
            self.email or '',
            self.area or '',
            self.customer_type or '',
        ]
        self.search_field = ' '.join(filter(None, search_values))

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "area": self.area,
            "customer_type": self.customer_type,
            "source": self.source,
            "source_id": self.source_id,
            "remark": self.remark,
            "search_field": self.search_field,
            "creator_id": self.creator_id,
            "creator_name": self.creator.name if self.creator else None,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }

    def to_simple_dict(self):
        """返回简单信息，用于快速展示"""
        return {
            "id": self.id,
            "company_name": self.company_name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "area": self.area,
        }
