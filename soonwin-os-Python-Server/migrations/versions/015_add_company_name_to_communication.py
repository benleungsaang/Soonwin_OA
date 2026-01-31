"""add company_name to communication

Revision ID: 015_add_company_name_to_communication
Revises: 014_add_statistics_fields_to_inquiry_log
Create Date: 2026-01-30 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '015_add_company_name_to_communication'
down_revision = '014_add_statistics_fields_to_inquiry_log'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 company_name 字段
    with op.batch_alter_table('InquiryCommunication') as batch_op:
        batch_op.add_column(sa.Column('company_name', sa.String(length=200), nullable=True))


def downgrade():
    # 移除 company_name 字段
    with op.batch_alter_table('InquiryCommunication') as batch_op:
        batch_op.drop_column('company_name')