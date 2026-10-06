"""add delete_time and delete_operator fields to video table

Revision ID: 020_add_delete_time_to_video
Revises: 019_update_video_machine_id_to_string
Create Date: 2026-02-02 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '020_add_delete_time_to_video'
down_revision = '019_update_video_machine_id_to_string'
branch_labels = None
depends_on = None


def upgrade():
    # 添加delete_time字段到videos表
    op.add_column('videos', sa.Column('delete_time', sa.DateTime(), nullable=True))
    # 添加delete_operator字段到videos表
    op.add_column('videos', sa.Column('delete_operator', sa.String(100), nullable=True))


def downgrade():
    # 删除delete_operator字段
    op.drop_column('videos', 'delete_operator')
    # 删除delete_time字段
    op.drop_column('videos', 'delete_time')