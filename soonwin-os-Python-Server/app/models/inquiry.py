from extensions import db
from datetime import datetime
from app.models.employee import Employee


class Inquiry(db.Model):
    __tablename__ = "Inquiry"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    area = db.Column(db.String(100), comment="地区")
    inquiry_date = db.Column(db.Date, comment="询盘日期")
    inquiry_source = db.Column(db.String(100), comment="询盘来源")
    company_name = db.Column(db.String(200), comment="公司名")
    contact_person = db.Column(db.String(100), nullable=False, comment="联系人")
    phone = db.Column(db.String(50), comment="电话")
    email = db.Column(db.String(100), comment="邮箱")
    packaging_product = db.Column(db.String(200), nullable=False, comment="包装产品")
    machine_type = db.Column(db.String(200), nullable=False, comment="需求机器类型")
    search_field = db.Column(db.Text, comment="冗余搜索字段，包含地区、来源、公司名、联系人、电话、邮箱、包装产品、需求类型")
    creator_id = db.Column(db.String(20), db.ForeignKey('Employee.emp_id'), nullable=False, comment="创建人ID")
    creator = db.relationship('Employee', backref=db.backref('inquiries', lazy=True))
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "area": self.area,
            "inquiry_date": self.inquiry_date.strftime('%Y-%m-%d') if self.inquiry_date else None,
            "inquiry_source": self.inquiry_source,
            "company_name": self.company_name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "packaging_product": self.packaging_product,
            "machine_type": self.machine_type,
            "search_field": self.search_field,
            "creator_id": self.creator_id,
            "creator_name": self.creator.name if self.creator else None,
            "creator_role": self.creator.user_role if self.creator else None,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }

    def update_search_field(self):
        """更新冗余搜索字段，组合所有相关字段"""
        search_values = [
            self.area or '',
            self.inquiry_source or '',
            self.company_name or '',
            self.contact_person or '',
            self.phone or '',
            self.email or '',
            self.packaging_product or '',
            self.machine_type or ''
        ]
        # 过滤空值并连接成搜索字段
        self.search_field = ' '.join(filter(None, search_values))

    def has_associated_orders(self):
        """检查此询盘是否已关联订单"""
        from app.models.order import Order
        associated_orders = Order.query.filter_by(inquiry_id=self.id).all()
        return len(associated_orders) > 0


class InquiryCommunication(db.Model):
    __tablename__ = "InquiryCommunication"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    inquiry_id = db.Column(db.Integer, db.ForeignKey('Inquiry.id'), nullable=False, comment="关联询盘ID")
    inquiry = db.relationship('Inquiry', backref=db.backref('communications', lazy=True, cascade='all, delete-orphan'))
    subject = db.Column(db.String(200), nullable=False, comment="主题")
    content = db.Column(db.Text, comment="内容")
    communication_date = db.Column(db.Date, comment="沟通日期")
    company_name = db.Column(db.String(200), comment="公司名称")
    creator_id = db.Column(db.String(20), db.ForeignKey('Employee.emp_id'), nullable=False, comment="创建人ID")
    creator = db.relationship('Employee')
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "inquiry_id": self.inquiry_id,
            "subject": self.subject,
            "content": self.content,
            "communication_date": self.communication_date.strftime('%Y-%m-%d') if self.communication_date else None,
            "company_name": self.company_name,
            "creator_id": self.creator_id,
            "creator_name": self.creator.name if self.creator else None,
            "creator_role": self.creator.user_role if self.creator else None,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }