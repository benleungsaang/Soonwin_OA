from extensions import db
from datetime import datetime

class CostAllocation(db.Model):
    __tablename__ = "cost_allocation"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    cost_name = db.Column(db.String(100), nullable=False, comment="费用名称（如物料损耗、房租）")
    cost_amount = db.Column(db.Numeric(12, 2), nullable=False, comment="费用金额（元）")
    cost_type = db.Column(db.String(20), nullable=False, comment="费用类型（一次性/每月/每季/每年）")
    apply_scope = db.Column(db.String(20), nullable=False, comment="适用范围（全局/单个订单）")
    order_id = db.Column(db.Integer, nullable=True, comment="关联订单ID（仅单个订单费用填写）")
    effective_date = db.Column(db.Date, nullable=False, comment="生效日期")
    remark = db.Column(db.Text, comment="备注（费用用途）")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")