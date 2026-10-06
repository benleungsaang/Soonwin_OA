"""add company_name to inquiry log

Revision ID: 016_add_company_name_to_inquiry_log
Revises: 015_add_company_name_to_communication
Create Date: 2026-01-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '016_add_company_name_to_inquiry_log'
down_revision = '015_add_company_name_to_communication'
branch_labels = None
depends_on = None


def upgrade():
    # 为 InquiryLog 表添加 company_name 字段
    # 首先检查字段是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('InquiryLog')]
    
    if 'company_name' not in columns:
        with op.batch_alter_table('InquiryLog') as batch_op:
            batch_op.add_column(sa.Column('company_name', sa.String(length=200), nullable=True, comment="公司名称"))


def downgrade():
    # 删除 company_name 字段（如果存在）
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('InquiryLog')]
    
    if 'company_name' in columns:
        with op.batch_alter_table('InquiryLog') as batch_op:
            batch_op.drop_column('company_name')