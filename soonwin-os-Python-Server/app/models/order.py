from extensions import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = "Order"  # 使用新表名
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键（序号）")
    is_new = db.Column(db.Integer, comment="新旧（1=新/0=旧）")
    area = db.Column(db.String(50), nullable=False, comment="地区")
    customer_name = db.Column(db.String(100), nullable=False, comment="客户名称")
    customer_type = db.Column(db.String(20), nullable=False, comment="经销商或终端")
    order_time = db.Column(db.Date, nullable=False, comment="下单时间")
    ship_time = db.Column(db.Date, comment="出货时间")
    ship_country = db.Column(db.String(50), comment="发运国家")
    contract_no = db.Column(db.String(50), nullable=False, comment="合同编号")
    order_no = db.Column(db.String(50), comment="订单编号")
    machine_no = db.Column(db.String(50), comment="包装机单号")
    machine_name = db.Column(db.String(100), nullable=False, default="包装机", comment="名称")
    machine_model = db.Column(db.String(50), nullable=False, comment="机型")
    machine_count = db.Column(db.Integer, nullable=False, default=1, comment="主机数量")
    unit = db.Column(db.String(10), nullable=False, default="set", comment="单位")
    contract_amount = db.Column(db.Numeric(12, 2), default=0, comment="合同人民币金额（元）")
    deposit = db.Column(db.Numeric(12, 2), default=0, comment="定金（元）")
    balance = db.Column(db.Numeric(12, 2), default=0, comment="尾款（元）")
    tax_rate = db.Column(db.Numeric(5, 2), default=13.0, comment="预估开票产生税费（%）")
    tax_refund_amount = db.Column(db.Numeric(12, 2), default=0, comment="退税后总金额")
    currency_amount = db.Column(db.Numeric(12, 2), default=0, comment="原始发票价（USD/RMB...）")
    payment_received = db.Column(db.Numeric(12, 2), default=0, comment="回款（RMB)")
    machine_cost = db.Column(db.Numeric(12, 2), default=0, comment="机器成本")
    net_profit = db.Column(db.Numeric(12, 2), default=0, comment="净利")
    proportionate_cost = db.Column(db.Numeric(12, 2), default=0, comment="摊分费用")
    individual_cost = db.Column(db.Numeric(12, 2), default=0, comment="个别费用之和")
    gross_profit = db.Column(db.Numeric(12, 2), default=0, comment="毛利")
    pay_type = db.Column(db.String(20), default="T/T", comment="T/T OR LC")
    commission = db.Column(db.Numeric(12, 2), default=0, comment="佣金")
    latest_ship_date = db.Column(db.Date, comment="最迟装运期")
    expected_delivery = db.Column(db.Date, comment="预计交期")
    order_dept = db.Column(db.String(50), comment="下单部门")
    check_requirement = db.Column(db.Text, comment="验收要求")
    attachment_imgs = db.Column(db.String(500), comment="验收图片路径（多图逗号分隔）")
    attachment_videos = db.Column(db.String(500), comment="验收视频路径（多视频逗号分隔）")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 定义序列化方法，便于接口返回JSON数据
    def to_dict(self):
        return {
            "id": self.id,
            "is_new": self.is_new,
            "area": self.area,
            "customer_name": self.customer_name,
            "customer_type": self.customer_type,
            "order_time": self.order_time.strftime('%Y-%m-%d') if self.order_time else None,
            "ship_time": self.ship_time.strftime('%Y-%m-%d') if self.ship_time else None,
            "ship_country": self.ship_country,
            "contract_no": self.contract_no,
            "order_no": self.order_no,
            "machine_no": self.machine_no,
            "machine_name": self.machine_name,
            "machine_model": self.machine_model,
            "machine_count": self.machine_count,
            "unit": self.unit,
            "contract_amount": float(self.contract_amount) if self.contract_amount else 0.0,
            "deposit": float(self.deposit) if self.deposit else 0.0,
            "balance": float(self.balance) if self.balance else 0.0,
            "tax_rate": float(self.tax_rate) if self.tax_rate else 13.0,
            "tax_refund_amount": float(self.tax_refund_amount) if self.tax_refund_amount else 0.0,
            "currency_amount": float(self.currency_amount) if self.currency_amount else 0.0,
            "payment_received": float(self.payment_received) if self.payment_received else 0.0,
            "machine_cost": float(self.machine_cost) if self.machine_cost else 0.0,
            "net_profit": float(self.net_profit) if self.net_profit else 0.0,
            "proportionate_cost": float(self.proportionate_cost) if self.proportionate_cost else 0.0,
            "individual_cost": float(self.individual_cost) if self.individual_cost else 0.0,
            "gross_profit": float(self.gross_profit) if self.gross_profit else 0.0,
            "pay_type": self.pay_type,
            "commission": float(self.commission) if self.commission else 0.0,
            "latest_ship_date": self.latest_ship_date.strftime('%Y-%m-%d') if self.latest_ship_date else None,
            "expected_delivery": self.expected_delivery.strftime('%Y-%m-%d') if self.expected_delivery else None,
            "order_dept": self.order_dept,
            "check_requirement": self.check_requirement,
            "attachment_imgs": self.attachment_imgs,
            "attachment_videos": self.attachment_videos,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }