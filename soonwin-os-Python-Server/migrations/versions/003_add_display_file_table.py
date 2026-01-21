"""add display file table

Revision ID: 003
Revises: 002
Create Date: 2026-01-21 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid


# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # 创建DisplayFile表
    op.create_table('DisplayFile',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('file_type', sa.String(10), nullable=False),
        sa.Column('display_mode', sa.String(20), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('original_filename', sa.String(200), nullable=False),
        sa.Column('created_by', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.now),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.now, onupdate=datetime.now),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 为DisplayFile表的uuid创建唯一索引
    op.create_index('ix_display_file_uuid', 'DisplayFile', ['uuid'], unique=True)
    
    # 为DisplayFile表的created_at创建索引
    op.create_index('ix_display_file_created_at', 'DisplayFile', ['created_at'])


def downgrade():
    # 删除索引
    op.drop_index('ix_display_file_uuid')
    op.drop_index('ix_display_file_created_at')
    
    # 删除DisplayFile表
    op.drop_table('DisplayFile')