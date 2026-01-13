"""为Employee表添加登录设备和上次登录时间字段

Revision ID: 000000000001
Revises: b43ce6da1d5b
Create Date: 2026-01-13 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

# revision identifiers, used by Alembic.
revision = '000000000001'
down_revision = 'b43ce6da1d5b'
branch_labels = None
depends_on = None


def upgrade():
    # 为Employee表添加新列
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_login_time', sa.DateTime(), nullable=True, comment="上次登录时间"))
        batch_op.add_column(sa.Column('login_device', sa.String(length=100), nullable=True, comment="登录设备"))


def downgrade():
    # 删除Employee表的新列
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.drop_column('login_device')
        batch_op.drop_column('last_login_time')