"""add currency info to quotation temp

Revision ID: 038_20260309_100000
Revises: 037_20260308_100000_remove_quotation_temp_order_mark_unique_constraint
Create Date: 2026-03-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '038_20260309_100000'
down_revision = '037_20260308_100000_remove_quotation_temp_order_mark_unique_constraint'
branch_labels = None
depends_on = None


def upgrade():
    # 添加currency_info字段到QuotationTemp表
    with op.batch_alter_table('QuotationTemp', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency_info', sa.Text, comment='货币信息JSON，包含code, name, symbol, rate'))


def downgrade():
    # 删除currency_info字段
    with op.batch_alter_table('QuotationTemp', schema=None) as batch_op:
        batch_op.drop_column('currency_info')