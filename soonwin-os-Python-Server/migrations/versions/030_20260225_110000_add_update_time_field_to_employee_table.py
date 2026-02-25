"""add update_time field to Employee table

Revision ID: 030_20260225_110000
Revises: 029_20260225_100000
Create Date: 2026-02-25 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '030_20260225_110000'
down_revision = '029_20260225_100000'  # 上一个版本
branch_labels = None
depends_on = None


def upgrade():
    # 为Employee表添加update_time字段
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.add_column(sa.Column('update_time', sa.DateTime(), nullable=True, default=datetime.now))
    
    # 更新现有记录的update_time字段为create_time
    op.execute("UPDATE Employee SET update_time = create_time WHERE update_time IS NULL")


def downgrade():
    # 删除update_time字段
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.drop_column('update_time')