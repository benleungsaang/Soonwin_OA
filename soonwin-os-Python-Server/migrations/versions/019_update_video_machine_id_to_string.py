"""update video machine_id to string

Revision ID: 019_update_video_machine_id_to_string
Revises: 018_add_search_field_to_order
Create Date: 2026-02-02 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '019_update_video_machine_id_to_string'
down_revision = '018_add_search_field_to_order'
branch_labels = None
depends_on = None


def upgrade():
    # 修改videos表的machine_id字段从整数改为字符串
    with op.batch_alter_table('videos') as batch_op:
        batch_op.alter_column('machine_id', 
                             existing_type=sa.Integer(),
                             type_=sa.String(length=255),
                             existing_nullable=True,
                             existing_server_default='0')


def downgrade():
    # 恢复videos表的machine_id字段从字符串改回整数
    with op.batch_alter_table('videos') as batch_op:
        batch_op.alter_column('machine_id',
                             existing_type=sa.String(length=255),
                             type_=sa.Integer(),
                             existing_nullable=True,
                             existing_server_default='0')