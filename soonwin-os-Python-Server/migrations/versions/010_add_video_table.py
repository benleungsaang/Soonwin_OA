"""add video table

Revision ID: 010
Revises: 009_add_photo_table_and_soft_delete_machines
Create Date: 2026-01-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '010'
down_revision = '009_add_photo_table_and_soft_delete_machines'
branch_labels = None
depends_on = None


def upgrade():
    # 创建videos表
    op.create_table(
        'videos',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('title', sa.String(length=255), nullable=False, default=''),
        sa.Column('tags', sa.String(length=500), nullable=False, default=''),
        sa.Column('machine_id', sa.Integer(), nullable=True, default=0),
        sa.Column('remark', sa.Text(), nullable=False, default=''),
        sa.Column('search_field', sa.Text(), nullable=False, default=''),
        sa.Column('uploader', sa.String(length=100), nullable=False),
        sa.Column('original_path', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('compressed_path', sa.String(length=500), nullable=True),
        sa.Column('original_width', sa.Integer(), nullable=True, default=0),
        sa.Column('original_height', sa.Integer(), nullable=True, default=0),
        sa.Column('duration', sa.Float(), nullable=True, default=0.0),
        sa.Column('file_size', sa.BigInteger(), nullable=True, default=0),
        sa.Column('compress_status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('upload_time', sa.DateTime(), nullable=False, default=datetime.now),
        sa.Column('is_deleted', sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # 删除videos表
    op.drop_table('videos')