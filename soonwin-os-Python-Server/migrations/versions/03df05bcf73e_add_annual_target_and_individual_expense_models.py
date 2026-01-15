"""Add AnnualTarget and IndividualExpense models, modify Order model

Revision ID: 03df05bcf73e
Revises: 98a4b7c5d1e2
Create Date: 2026-01-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '03df05bcf73e'
down_revision = '98a4b7c5d1e2'
branch_labels = None
depends_on = None


def upgrade():
    # 创建AnnualTarget表
    op.create_table('AnnualTarget',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('target_year', sa.Integer(), nullable=False, comment='目标年份'),
        sa.Column('target_amount', sa.Numeric(precision=15, scale=2), server_default='10000000.00', nullable=True, comment='年度目标金额（元）'),
        sa.Column('create_time', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('update_time', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 为AnnualTarget表的更新时间添加触发器（仅SQLite）
    try:
        op.execute("CREATE TRIGGER annual_target_update_time_trigger UPDATE OF target_year, target_amount ON AnnualTarget "
                   "BEGIN UPDATE AnnualTarget SET update_time = datetime('now') WHERE id = NEW.id; END;")
    except:
        pass
    
    # 创建IndividualExpense表
    op.create_table('IndividualExpense',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('order_id', sa.Integer(), nullable=False, comment='订单ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='费用名称'),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False, comment='费用金额（元，可正可负）'),
        sa.Column('remark', sa.Text(), nullable=True, comment='备注信息'),
        sa.Column('create_time', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('update_time', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['order_id'], ['Order.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 为IndividualExpense表创建索引
    op.create_index('ix_IndividualExpense_order_id', 'IndividualExpense', ['order_id'], unique=False)
    
    # 为IndividualExpense表的更新时间添加触发器（仅SQLite）
    try:
        op.execute("CREATE TRIGGER individual_expense_update_time_trigger UPDATE OF name, amount, remark ON IndividualExpense "
                   "BEGIN UPDATE IndividualExpense SET update_time = datetime('now') WHERE id = NEW.id; END;")
    except:
        pass
    
    # 修改Order表，添加新字段
    op.add_column('Order', sa.Column('proportionate_cost', sa.Numeric(precision=12, scale=2), server_default='0', nullable=True, comment='摊分费用'))
    op.add_column('Order', sa.Column('individual_cost', sa.Numeric(precision=12, scale=2), server_default='0', nullable=True, comment='个别费用之和'))
    
    # 如果operational_cost列存在，则删除它（需要先备份数据）
    # 这里我们先备份operational_cost的值到proportionate_cost
    try:
        # 获取现有operational_cost的数据并保存
        connection = op.get_bind()
        result = connection.execute(sa.text("SELECT id, operational_cost FROM `Order`"))
        rows = result.fetchall()
        for row in rows:
            op.execute(sa.text(f"UPDATE `Order` SET proportionate_cost = {row.operational_cost or 0} WHERE id = {row.id}"))
    except Exception as e:
        print(f"处理operational_cost数据时出错: {e}")
    
    # 删除operational_cost列
    try:
        op.drop_column('Order', 'operational_cost')
    except Exception as e:
        print(f"删除operational_cost列时出错: {e}")
    
    # 修复ExpenseAllocation表的外键约束（将其指向正确的Order表）
    # 由于Alembic无法直接修改外键，我们先记录需要手动处理


def downgrade():
    # 重新添加operational_cost列
    op.add_column('Order', sa.Column('operational_cost', sa.Numeric(precision=12, scale=2), server_default='0', nullable=True, comment='运营成本'))
    
    # 将proportionate_cost的值复制回operational_cost（作为临时处理）
    try:
        connection = op.get_bind()
        result = connection.execute(sa.text("SELECT id, proportionate_cost FROM `Order`"))
        rows = result.fetchall()
        for row in rows:
            op.execute(sa.text(f"UPDATE `Order` SET operational_cost = {row.proportionate_cost or 0} WHERE id = {row.id}"))
    except Exception as e:
        print(f"恢复operational_cost数据时出错: {e}")
    
    # 删除新添加的列
    op.drop_column('Order', 'individual_cost')
    op.drop_column('Order', 'proportionate_cost')
    
    # 删除IndividualExpense表
    op.drop_table('IndividualExpense')
    
    # 删除AnnualTarget表
    op.drop_table('AnnualTarget')