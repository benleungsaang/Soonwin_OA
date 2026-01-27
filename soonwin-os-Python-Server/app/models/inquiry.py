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
            "creator_id": self.creator_id,
            "creator_name": self.creator.name if self.creator else None,
            "creator_role": self.creator.user_role if self.creator else None,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class InquiryCommunication(db.Model):
    __tablename__ = "InquiryCommunication"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    inquiry_id = db.Column(db.Integer, db.ForeignKey('Inquiry.id'), nullable=False, comment="关联询盘ID")
    inquiry = db.relationship('Inquiry', backref=db.backref('communications', lazy=True, cascade='all, delete-orphan'))
    subject = db.Column(db.String(200), nullable=False, comment="主题")
    content = db.Column(db.Text, comment="内容")
    communication_date = db.Column(db.Date, comment="沟通日期")
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
            "creator_id": self.creator_id,
            "creator_name": self.creator.name if self.creator else None,
            "creator_role": self.creator.user_role if self.creator else None,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }


class InquiryLog(db.Model):
    __tablename__ = "InquiryLog"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    inquiry_id = db.Column(db.Integer, db.ForeignKey('Inquiry.id'), comment="关联询盘ID")
    operation_type = db.Column(db.String(50), nullable=False, comment="操作类型: create, update, delete")
    operator_id = db.Column(db.String(20), db.ForeignKey('Employee.emp_id'), nullable=False, comment="操作人ID")
    operator = db.relationship('Employee')
    operation_details = db.Column(db.Text, comment="操作详情")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "inquiry_id": self.inquiry_id,
            "operation_type": self.operation_type,
            "operator_id": self.operator_id,
            "operator_name": self.operator.name if self.operator else None,
            "operator_role": self.operator.user_role if self.operator else None,
            "operation_details": self.operation_details,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }