"""为Employee表添加备注字段

Revision ID: 000000000002
Revises: 000000000001
Create Date: 2026-01-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

# revision identifiers, used by Alembic.
revision = '000000000002'
down_revision = '000000000001'
branch_labels = None
depends_on = None


def upgrade():
    # 为Employee表添加备注列
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.add_column(sa.Column('remarks', sa.Text(), nullable=True, comment="备注信息"))


def downgrade():
    # 删除Employee表的备注列
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.drop_column('remarks')