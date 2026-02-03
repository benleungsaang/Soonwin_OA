from extensions import db
from datetime import datetime
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class OrderProgress(db.Model):
    __tablename__ = 'order_progress'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid, comment='进度表ID')
    order_id = db.Column(db.String(36), db.ForeignKey('Order.id'), unique=True, nullable=False, comment='关联订单ID')
    current_status = db.Column(db.String(50), comment='当前进度状态：下单/采购/排产/生产/发货/完成')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='进度表创建时间')

    # 关联状态详情和进度项
    status_details = db.relationship('ProgressStatusDetail', backref='progress', cascade='all, delete-orphan')
    items = db.relationship('ProgressItem', backref='progress', cascade='all, delete-orphan')


class ProgressStatusDetail(db.Model):
    __tablename__ = 'progress_status_detail'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid, comment='状态详情ID')
    progress_id = db.Column(db.String(36), db.ForeignKey('order_progress.id'), nullable=False, comment='关联进度表ID')
    status = db.Column(db.String(50), nullable=False, comment='状态名称：下单/采购/排产...')
    start_time = db.Column(db.DateTime, comment='状态开始时间')
    expected_complete_time = db.Column(db.DateTime, comment='预计完成时间')
    actual_complete_time = db.Column(db.DateTime, comment='实际完成时间')


class ProgressItem(db.Model):
    __tablename__ = 'progress_item'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid, comment='进度项ID')
    progress_id = db.Column(db.String(36), db.ForeignKey('order_progress.id'), nullable=False, comment='关联进度表ID')
    title = db.Column(db.String(200), nullable=False, comment='进度项标题')
    status = db.Column(db.String(20), default='未完成', comment='进度项状态：未完成/已完成')
    remark = db.Column(db.Text, comment='备注信息')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关联多媒体文件
    media_files = db.relationship('ProgressMedia', backref='item', cascade='all, delete-orphan')


class ProgressMedia(db.Model):
    __tablename__ = 'progress_media'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid, comment='多媒体文件ID')
    item_id = db.Column(db.String(36), db.ForeignKey('progress_item.id'), nullable=False, comment='关联进度项ID')
    file_type = db.Column(db.String(20), comment='文件类型：image/video')
    file_url = db.Column(db.String(500), nullable=False, comment='文件存储路径/URL')
    file_name = db.Column(db.String(200), comment='原始文件名')
    upload_time = db.Column(db.DateTime, default=datetime.now, comment='上传时间')