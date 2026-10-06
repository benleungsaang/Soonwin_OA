"""合并订单收支记录表

Revision ID: 039
Revises: 038
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import json

# revision identifiers
revision = '039_20260429_100000_merge_order_record_items'
down_revision = '038_20260309_100000_add_currency_info_to_quotation_temp'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建新的 OrderRecordItem 表
    op.create_table(
        'OrderRecordItem',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='自增主键'),
        sa.Column('order_record_id', sa.Integer(), nullable=False, index=True, comment='订单记录ID'),
        sa.Column('type', sa.String(10), nullable=False, comment='收支类型：income-收入, expense-支出'),
        sa.Column('remark', sa.String(200), nullable=True, comment='备注信息'),
        sa.Column('amount', sa.Numeric(12, 2), nullable=True, default=0, comment='金额'),
        sa.Column('currency', sa.String(10), nullable=True, default='CNY', comment='币种'),
        sa.Column('exchange_rate', sa.Numeric(10, 4), nullable=True, default=1.0, comment='汇率'),
        sa.Column('screenshots', sa.Text(), nullable=True, comment='佐证截图路径（JSON数组）'),
        sa.Column('record_date', sa.Date(), nullable=True, comment='记录日期'),
        sa.Column('creator_id', sa.String(20), nullable=True, comment='创建人ID'),
        sa.Column('create_time', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updater_id', sa.String(20), nullable=True, comment='最后修改人ID'),
        sa.Column('update_time', sa.DateTime(), nullable=True, comment='最后修改时间'),
        sa.ForeignKeyConstraint(['order_record_id'], ['OrderRecord.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='订单记录收支明细表（合并版）'
    )

    # 2. 迁移 OrderRecordIncome 数据到 OrderRecordItem (type='income')
    connection = op.get_bind()
    connection.execute(text("""
        INSERT INTO OrderRecordItem (
            order_record_id, type, remark, amount, currency, exchange_rate,
            screenshots, record_date, creator_id, create_time, updater_id, update_time
        )
        SELECT
            order_record_id,
            'income',
            remark,
            amount,
            currency,
            exchange_rate,
            CASE WHEN screenshot IS NOT NULL AND screenshot != '' THEN json(screenshot) ELSE NULL END,
            record_date,
            creator_id,
            create_time,
            updater_id,
            update_time
        FROM OrderRecordIncome
    """))

    # 3. 迁移 OrderRecordExpense 数据到 OrderRecordItem (type='expense')
    connection.execute(text("""
        INSERT INTO OrderRecordItem (
            order_record_id, type, remark, amount, currency, exchange_rate,
            screenshots, record_date, creator_id, create_time, updater_id, update_time
        )
        SELECT
            order_record_id,
            'expense',
            remark,
            amount,
            currency,
            exchange_rate,
            CASE WHEN screenshot IS NOT NULL AND screenshot != '' THEN json(screenshot) ELSE NULL END,
            record_date,
            creator_id,
            create_time,
            updater_id,
            update_time
        FROM OrderRecordExpense
    """))

    # 4. 删除旧表
    op.drop_table('OrderRecordExpense')
    op.drop_table('OrderRecordIncome')


def downgrade():
    pass
