"""
订单记录模块数据模型
用于追踪订单的收入和支出情况（收支合并版）
"""

from extensions import db
from datetime import datetime
import json


class OrderRecord(db.Model):
    """订单记录主表"""
    __tablename__ = "OrderRecord"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    order_no = db.Column(db.String(50), unique=True, nullable=False, comment="订单号")
    order_remark_name = db.Column(db.String(200), comment="订单备注名")
    order_amount = db.Column(db.Numeric(12, 2), default=0, comment="订单金额")
    currency = db.Column(db.String(10), default='CNY', comment="币种")
    exchange_rate = db.Column(db.Numeric(10, 4), default=1.0, comment="汇率")
    order_date = db.Column(db.Date, nullable=False, comment="订单创建日期")
    is_completed = db.Column(db.Boolean, default=False, comment="是否已完成")
    creator_id = db.Column(db.String(20), comment="创建人ID")
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), nullable=True, comment="关联客户ID")
    customer = db.relationship('Customer', backref=db.backref('order_records', lazy=True))
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联收支记录（合并后的统一表）
    items = db.relationship('OrderRecordItem', backref='order_record', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_relations=False):
        # 订单金额换算为人民币
        order_amount_cny = float(self.order_amount or 0) * float(self.exchange_rate or 1.0)

        result = {
            "id": self.id,
            "order_no": self.order_no,
            "order_remark_name": self.order_remark_name,
            "order_amount": float(self.order_amount) if self.order_amount else 0.0,
            "currency": self.currency,
            "exchange_rate": float(self.exchange_rate) if self.exchange_rate else 1.0,
            "order_amount_cny": order_amount_cny,
            "order_date": self.order_date.strftime('%Y-%m-%d') if self.order_date else None,
            "is_completed": self.is_completed if self.is_completed is not None else False,
            "creator_id": self.creator_id,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }

        if include_relations:
            # 计算汇总数据（按汇率换算为人民币）
            items_list = [item.to_dict() for item in self.items]
            incomes = [item for item in items_list if item['type'] == 'income']
            expenses = [item for item in items_list if item['type'] == 'expense']

            total_income = sum(float(inc['amount_cny']) for inc in incomes)
            total_expense = sum(float(exp['amount_cny']) for exp in expenses)
            order_profit = order_amount_cny - total_expense
            actual_profit = total_income - total_expense

            result.update({
                "total_income": total_income,
                "total_expense": total_expense,
                "order_profit": order_profit,
                "actual_profit": actual_profit,
                "incomes": incomes,
                "expenses": expenses,
            })

        return result


class OrderRecordItem(db.Model):
    """
    订单记录收支明细表（合并收入/支出）
    type 区分收支类型：income = 收入, expense = 支出
    screenshots 存储多张截图路径（JSON数组）
    """
    __tablename__ = "OrderRecordItem"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    order_record_id = db.Column(db.Integer, db.ForeignKey('OrderRecord.id'), nullable=False, index=True, comment="订单记录ID")
    type = db.Column(db.String(10), nullable=False, comment="收支类型：income-收入, expense-支出")
    remark = db.Column(db.String(200), comment="备注信息（如：订金收入）")
    amount = db.Column(db.Numeric(12, 2), default=0, comment="金额")
    currency = db.Column(db.String(10), default='CNY', comment="币种")
    exchange_rate = db.Column(db.Numeric(10, 4), default=1.0, comment="汇率")
    screenshots = db.Column(db.Text, comment="佐证截图路径（JSON数组格式）")
    record_date = db.Column(db.Date, comment="记录日期")
    creator_id = db.Column(db.String(20), comment="创建人ID")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    updater_id = db.Column(db.String(20), comment="最后修改人ID")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="最后修改时间")

    def to_dict(self):
        # 解析 screenshots JSON 数组
        screenshots_list = json.loads(self.screenshots) if self.screenshots else []

        return {
            "id": self.id,
            "order_record_id": self.order_record_id,
            "type": self.type,
            "remark": self.remark,
            "amount": float(self.amount) if self.amount else 0.0,
            "currency": self.currency,
            "exchange_rate": float(self.exchange_rate) if self.exchange_rate else 1.0,
            "screenshots": screenshots_list,
            # 第一张图用于列表显示
            "first_screenshot": screenshots_list[0] if screenshots_list else None,
            "record_date": self.record_date.strftime('%Y-%m-%d') if self.record_date else None,
            "creator_id": self.creator_id,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "updater_id": self.updater_id,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            # 换算后人民币金额
            "amount_cny": float(self.amount or 0) * float(self.exchange_rate or 1.0)
        }


# ========== 以下为旧模型，保留用于数据迁移参考，迁移完成后可删除 ==========

class OrderRecordIncome(db.Model):
    """订单记录收入明细表（旧版，迁移后删除）"""
    __tablename__ = "OrderRecordIncome"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    order_record_id = db.Column(db.Integer, db.ForeignKey('OrderRecord.id'), nullable=False, index=True, comment="订单记录ID")
    remark = db.Column(db.String(200), comment="备注信息（如：订金收入）")
    amount = db.Column(db.Numeric(12, 2), default=0, comment="金额")
    currency = db.Column(db.String(10), default='CNY', comment="币种")
    exchange_rate = db.Column(db.Numeric(10, 4), default=1.0, comment="汇率")
    screenshot = db.Column(db.String(500), comment="佐证截图路径")
    record_date = db.Column(db.Date, comment="记录日期")
    creator_id = db.Column(db.String(20), comment="创建人ID")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    updater_id = db.Column(db.String(20), comment="最后修改人ID")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="最后修改时间")


class OrderRecordExpense(db.Model):
    """订单记录支出明细表（旧版，迁移后删除）"""
    __tablename__ = "OrderRecordExpense"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    order_record_id = db.Column(db.Integer, db.ForeignKey('OrderRecord.id'), nullable=False, index=True, comment="订单记录ID")
    remark = db.Column(db.String(200), comment="备注信息（如：买XX机器支出）")
    amount = db.Column(db.Numeric(12, 2), default=0, comment="金额")
    currency = db.Column(db.String(10), default='CNY', comment="币种")
    exchange_rate = db.Column(db.Numeric(10, 4), default=1.0, comment="汇率")
    screenshot = db.Column(db.String(500), comment="佐证截图路径")
    record_date = db.Column(db.Date, comment="记录日期")
    creator_id = db.Column(db.String(20), comment="创建人ID")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    updater_id = db.Column(db.String(20), comment="最后修改人ID")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="最后修改时间")
