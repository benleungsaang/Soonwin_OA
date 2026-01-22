"""Remove display_mode and add page_count to DisplayFile

Revision ID: 004
Revises: 003_add_display_file_table
Create Date: 2026-01-22 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # 删除 display_mode 字段
    with op.batch_alter_table('DisplayFile', schema=None) as batch_op:
        batch_op.drop_column('display_mode')

    # 添加 page_count 字段
    with op.batch_alter_table('DisplayFile', schema=None) as batch_op:
        batch_op.add_column(sa.Column('page_count', sa.Integer, nullable=True, comment='页数'))
        

def downgrade():
    # 恢复 display_mode 字段
    with op.batch_alter_table('DisplayFile', schema=None) as batch_op:
        batch_op.add_column(sa.Column('display_mode', mysql.VARCHAR(length=20), nullable=False, comment='展示方式（pagination/waterfall）'))

    # 删除 page_count 字段
    with op.batch_alter_table('DisplayFile', schema=None) as batch_op:
        batch_op.drop_column('page_count')