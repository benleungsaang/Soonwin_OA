"""添加订单搜索字段

Revision ID: 018_add_search_field_to_order
Revises: 017_add_reset_time_to_inquiry_log
Create Date: 2026-01-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '018_add_search_field_to_order'
down_revision = '017_add_reset_time_to_inquiry_log'
branch_labels = None
depends_on = None


def upgrade():
    # 添加search_field字段到订单表
    with op.batch_alter_table('Order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('search_field', sa.Text, comment='搜索字段，由多个字段内容组合而成'))


def downgrade():
    # 删除search_field字段
    with op.batch_alter_table('Order', schema=None) as batch_op:
        batch_op.drop_column('search_field')