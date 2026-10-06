"""add reset_time to inquiry log

Revision ID: 017_add_reset_time_to_inquiry_log
Revises: 016_add_company_name_to_inquiry_log
Create Date: 2026-01-31 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '017_add_reset_time_to_inquiry_log'
down_revision = '016_add_company_name_to_inquiry_log'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 reset_time 字段
    with op.batch_alter_table('InquiryLog') as batch_op:
        batch_op.add_column(sa.Column('reset_time', sa.DateTime, nullable=True, comment="统计复位时间"))


def downgrade():
    # 移除 reset_time 字段
    with op.batch_alter_table('InquiryLog') as batch_op:
        batch_op.drop_column('reset_time')