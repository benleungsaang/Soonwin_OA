"""add media file table

Revision ID: 026_20260207_160000
Revises: 025_20260205_110000_rename_task_folder_structure
Create Date: 2026-02-07 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

# revision identifiers
revision = '026_20260207_160000'
down_revision = '025_20260205_110000_rename_task_folder_structure'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 task_media_file 表
    op.create_table(
        'task_media_file',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('status_task_id', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False),
        sa.Column('file_format', sa.String(length=20), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('thumb_path', sa.String(length=500), nullable=True),
        sa.Column('file_name', sa.String(length=200), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('upload_time', sa.DateTime(), nullable=True),
        sa.Column('sort', sa.Integer(), default=0, nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=True),
        sa.ForeignKeyConstraint(['status_task_id'], ['status_task.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='任务项多媒体文件表（存储图片/视频）'
    )

    # 添加外键约束的注释
    op.execute("PRAGMA foreign_keys = ON")

    # 添加表注释（SQLite不直接支持，但保留以备将来使用）
    print("已创建 task_media_file 表")

    # 可选：迁移旧数据到新表（如果需要）
    # 这里可以添加将旧的 photo_path 和 thumb_photo_path 数据迁移到新表的逻辑
    # 但这需要在应用层面实现，因为需要处理文件移动


def downgrade():
    # 删除 task_media_file 表
    op.drop_table('task_media_file')