"""add occurred_date to Expense

Revision ID: 035_20260305_100000
Revises: 034_20260302_100000
Create Date: 2026-03-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import json


# revision identifiers, used by Alembic.
revision = '035_20260305_100000_add_occurred_date_to_expense'
down_revision = '034_20260302_100000_add_inquiry_relation_to_order'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 occurred_date 字段到 Expense 表
    with op.batch_alter_table('Expense', schema=None) as batch_op:
        batch_op.add_column(sa.Column('occurred_date', sa.Date(), nullable=True, comment='费用发生日期'))


def downgrade():
    # 删除 occurred_date 字段
    with op.batch_alter_table('Expense', schema=None) as batch_op:
        batch_op.drop_column('occurred_date')