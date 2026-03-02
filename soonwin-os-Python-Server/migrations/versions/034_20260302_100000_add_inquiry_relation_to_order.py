"""add inquiry relation to order

Revision ID: 034_20260302_100000_add_inquiry_relation_to_order
Revises: 033_20260228_100000_add_attendance_permission
Create Date: 2026-03-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '034_20260302_100000_add_inquiry_relation_to_order'
down_revision = '033_20260228_100000_add_attendance_permission'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 inquiry_id 字段到 Order 表
    with op.batch_alter_table('Order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('inquiry_id', sa.Integer(), nullable=False, comment='关联询盘ID'))
        # 设置外键约束
        batch_op.create_foreign_key('fk_order_inquiry_id', 'Inquiry', ['inquiry_id'], ['id'])


def downgrade():
    # 移除外键约束
    with op.batch_alter_table('Order', schema=None) as batch_op:
        batch_op.drop_constraint('fk_order_inquiry_id', type_='foreignkey')
        batch_op.drop_column('inquiry_id')