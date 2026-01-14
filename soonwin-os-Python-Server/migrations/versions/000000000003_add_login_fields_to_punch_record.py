"""为PunchRecord表添加登录时间与设备字段

Revision ID: 000000000003
Revises: 000000000002
Create Date: 2026-01-14 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '000000000003'
down_revision = '000000000002'
branch_labels = None
depends_on = None


def upgrade():
    # 为PunchRecord表添加新列
    with op.batch_alter_table('PunchRecord', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_login_time', sa.DateTime(), nullable=True, comment="最后登录时间"))
        batch_op.add_column(sa.Column('login_device', sa.String(length=100), nullable=True, comment="登录设备"))


def downgrade():
    # 删除PunchRecord表的新列
    with op.batch_alter_table('PunchRecord', schema=None) as batch_op:
        batch_op.drop_column('login_device')
        batch_op.drop_column('last_login_time')