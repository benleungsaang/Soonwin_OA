"""Add expense management tables

Revision ID: 98a4b7c5d1e2
Revises: 000000000003
Create Date: 2026-01-14 15:50:02.437200

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql, sqlite

# revision identifiers, used by Alembic.
revision = '98a4b7c5d1e2'
down_revision = '000000000003'
branch_labels = None
depends_on = None


def upgrade():
    # 创建Expense表
    op.create_table('Expense',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='自增主键'),
    sa.Column('name', sa.String(length=100), nullable=False, comment='费用名称'),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False, comment='费用金额（元，可正可负）'),
    sa.Column('expense_type', sa.String(length=20), nullable=False, comment='费用类型（全面分摊）'),
    sa.Column('target_year', sa.Integer(), nullable=False, comment='目标年份'),
    sa.Column('remark', sa.Text(), nullable=True, comment='备注信息'),
    sa.Column('create_time', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('update_time', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.PrimaryKeyConstraint('id')
    )
    
    # 为更新时间添加默认值函数（仅SQLite）
    try:
        # 对于SQLite，需要特别处理onupdate
        op.execute("CREATE TRIGGER expense_update_time_trigger UPDATE OF name, amount, expense_type, target_year, remark ON Expense "
                   "BEGIN UPDATE Expense SET update_time = datetime('now') WHERE id = NEW.id; END;")
    except:
        # 如果失败，继续执行
        pass
    
    # 创建ExpenseCalculationRecord表
    op.create_table('ExpenseCalculationRecord',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='自增主键'),
    sa.Column('calculation_time', sa.DateTime(), nullable=True, comment='计算时间'),
    sa.Column('target_year', sa.Integer(), nullable=False, comment='计算目标年份'),
    sa.Column('status', sa.String(length=20), server_default='completed', nullable=True, comment='计算状态（completed/failed）'),
    sa.Column('remark', sa.Text(), nullable=True, comment='备注信息'),
    sa.PrimaryKeyConstraint('id')
    )
    
    # 创建ExpenseAllocation表
    op.create_table('ExpenseAllocation',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='自增主键'),
    sa.Column('expense_id', sa.Integer(), nullable=False, comment='费用记录ID'),
    sa.Column('order_id', sa.Integer(), nullable=False, comment='订单ID'),
    sa.Column('allocated_amount', sa.Numeric(precision=12, scale=2), nullable=False, comment='分摊金额'),
    sa.Column('create_time', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.ForeignKeyConstraint(['expense_id'], ['Expense.id'], ),
    sa.ForeignKeyConstraint(['order_id'], ['OrderList.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # 删除ExpenseAllocation表
    op.drop_table('ExpenseAllocation')
    
    # 删除ExpenseCalculationRecord表
    op.drop_table('ExpenseCalculationRecord')
    
    # 删除Expense表
    op.drop_table('Expense')