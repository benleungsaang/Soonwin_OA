"""add statistics fields to inquiry log

Revision ID: 014_add_statistics_fields_to_inquiry_log
Revises: 013_add_search_field_to_inquiry
Create Date: 2026-01-30 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '014_add_statistics_fields_to_inquiry_log'
down_revision = '013_add_search_field_to_inquiry'
branch_labels = None
depends_on = None


def upgrade():
    # 添加统计字段
    with op.batch_alter_table('InquiryLog', schema=None) as batch_op:
        batch_op.add_column(sa.Column('total_inquiries', sa.Integer, comment="总询盘数"))
        batch_op.add_column(sa.Column('total_communications', sa.Integer, comment="总沟通记录数"))
        batch_op.add_column(sa.Column('new_inquiries_count', sa.Integer, comment="新增询盘数"))
        batch_op.add_column(sa.Column('new_communications_count', sa.Integer, comment="新增沟通记录数"))


def downgrade():
    # 删除统计字段
    with op.batch_alter_table('InquiryLog', schema=None) as batch_op:
        batch_op.drop_column('total_inquiries')
        batch_op.drop_column('total_communications')
        batch_op.drop_column('new_inquiries_count')
        batch_op.drop_column('new_communications_count')