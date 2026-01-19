from extensions import db
from datetime import datetime
from .order import Order
import uuid


class OrderInspection(db.Model):
    """
    订单验收主表
    """
    __tablename__ = "OrderInspection"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    order_id = db.Column(db.Integer, db.ForeignKey('Order.id'), nullable=False, comment="关联订单ID")
    inspection_status = db.Column(db.String(20), default='pending', comment="验收状态: pending(待验收), in_progress(验收中), completed(已完成)")
    inspection_progress = db.Column(db.Integer, default=0, comment="验收进度百分比")
    total_items = db.Column(db.Integer, default=0, comment="总检查项数")
    completed_items = db.Column(db.Integer, default=0, comment="已完成检查项数")
    remarks = db.Column(db.Text, comment="备注信息")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联订单
    order = db.relationship('Order', backref=db.backref('inspections', lazy=True))
    
    def to_dict(self):
        order_data = self.order.to_dict() if self.order else {}
        return {
            "id": self.id,
            "order_id": self.order_id,
            "inspection_status": self.inspection_status,
            "inspection_progress": self.inspection_progress,
            "total_items": self.total_items,
            "completed_items": self.completed_items,
            "remarks": self.remarks,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            # 订单基础信息
            "contract_no": order_data.get('contract_no', ''),
            "order_no": order_data.get('order_no', ''),
            "machine_no": order_data.get('machine_no', ''),
            "machine_name": order_data.get('machine_name', ''),
            "machine_model": order_data.get('machine_model', ''),
            "machine_count": order_data.get('machine_count', 0),
            "order_time": order_data.get('order_time', ''),
            "ship_time": order_data.get('ship_time', ''),
        }


class InspectionItem(db.Model):
    """
    验收检查项表
    """
    __tablename__ = "InspectionItem"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    inspection_id = db.Column(db.Integer, db.ForeignKey('OrderInspection.id'), nullable=False, comment="关联验收ID")
    parent_id = db.Column(db.Integer, db.ForeignKey('InspectionItem.id'), nullable=True, comment="父级检查项ID（用于大项）")
    item_category = db.Column(db.String(50), nullable=False, comment="检查项类别（大项，如：配件、外观等）")
    item_name = db.Column(db.String(200), nullable=False, comment="检查项名称（细项，如：部件1、角度1等）")
    item_type = db.Column(db.String(20), default='sub', comment="类型: parent(大项), sub(细项)")
    inspection_result = db.Column(db.String(20), default='pending', comment="检查结果: pending(待检查), normal(正常), defect(缺陷), not_applicable(无此项)")
    photo_path = db.Column(db.String(500), comment="照片路径，多张图片路径以逗号分隔")
    description = db.Column(db.Text, comment="缺陷描述")
    sort_order = db.Column(db.Integer, default=0, comment="排序")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联验收记录
    inspection = db.relationship('OrderInspection', backref=db.backref('items', lazy=True))
    # 关联父级检查项（自关联）
    children = db.relationship('InspectionItem', backref=db.backref('parent', remote_side=[id]))
    
    def to_dict(self):
        return {
            "id": self.id,
            "inspection_id": self.inspection_id,
            "parent_id": self.parent_id,
            "item_category": self.item_category,
            "item_name": self.item_name,
            "item_type": self.item_type,
            "inspection_result": self.inspection_result,
            "photo_path": self.photo_path,
            "description": self.description,
            "sort_order": self.sort_order,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }