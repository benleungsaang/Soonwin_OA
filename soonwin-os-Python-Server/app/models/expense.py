from extensions import db
from datetime import datetime


class Expense(db.Model):
    """
    费用记录模型
    用于记录需要分摊到订单中的费用
    """
    __tablename__ = "Expense"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    name = db.Column(db.String(100), nullable=False, comment="费用名称")
    amount = db.Column(db.Numeric(12, 2), nullable=False, comment="费用金额（元，可正可负）")
    expense_type = db.Column(db.String(20), nullable=False, comment="费用类型（全面分摊）")
    target_year = db.Column(db.Integer, nullable=False, comment="目标年份")
    remark = db.Column(db.Text, comment="备注信息")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")


class ExpenseAllocation(db.Model):
    """
    费用分摊记录模型
    记录每笔费用如何分摊到各个订单
    """
    __tablename__ = "ExpenseAllocation"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    expense_id = db.Column(db.Integer, db.ForeignKey('Expense.id'), nullable=False, comment="费用记录ID")
    order_id = db.Column(db.Integer, db.ForeignKey('OrderList.id'), nullable=False, comment="订单ID")
    allocated_amount = db.Column(db.Numeric(12, 2), nullable=False, comment="分摊金额")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    
    # 关联关系
    expense = db.relationship('Expense', backref=db.backref('allocations', lazy=True))
    order = db.relationship('OrderList', backref=db.backref('expense_allocations', lazy=True))


class ExpenseCalculationRecord(db.Model):
    """
    费用计算记录模型
    记录每次费用分摊计算的时间和状态
    """
    __tablename__ = "ExpenseCalculationRecord"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    calculation_time = db.Column(db.DateTime, default=datetime.now, comment="计算时间")
    target_year = db.Column(db.Integer, nullable=False, comment="计算目标年份")
    status = db.Column(db.String(20), default='completed', comment="计算状态（completed/failed）")
    remark = db.Column(db.Text, comment="备注信息")