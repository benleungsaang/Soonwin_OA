"""add video compression fields

Revision ID: 012_add_video_compression_fields
Revises: 011_update_file_paths
Create Date: 2026-01-30 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '012_add_video_compression_fields'
down_revision = '011_update_file_paths'
branch_labels = None
depends_on = None


def upgrade():
    # 检查并添加缺失的字段
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('videos')]
    
    # 添加压缩后路径字段（如果不存在）
    if 'compressed_path' not in columns:
        op.add_column('videos', sa.Column('compressed_path', sa.String(500), nullable=True))
    
    # 确保压缩状态字段存在
    if 'compress_status' not in columns:
        op.add_column('videos', sa.Column('compress_status', sa.String(50), nullable=False, server_default='pending'))
    
    # 添加实际宽高字段（如果不存在）
    if 'actual_width' not in columns:
        op.add_column('videos', sa.Column('actual_width', sa.Integer, nullable=True, default=0))
    if 'actual_height' not in columns:
        op.add_column('videos', sa.Column('actual_height', sa.Integer, nullable=True, default=0))


def downgrade():
    # 删除添加的字段
    op.drop_column('videos', 'compressed_path')
    op.drop_column('videos', 'compress_status')
    op.drop_column('videos', 'actual_width')
    op.drop_column('videos', 'actual_height')