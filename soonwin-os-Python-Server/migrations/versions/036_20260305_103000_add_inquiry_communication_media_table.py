"""添加询盘沟通记录媒体文件表

Revision ID: 036
Revises: 035_20260305_100000_add_occurred_date_to_expense
Create Date: 2026-03-05 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import os

# revision identifiers, used by Alembic.
revision = '036'
down_revision = '035_20260305_100000_add_occurred_date_to_expense'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 InquiryCommunicationMedia 表
    op.create_table(
        'InquiryCommunicationMedia',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('communication_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('thumb_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('upload_time', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['communication_id'], ['InquiryCommunication.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='询盘沟通记录媒体文件表'
    )
    
    # 创建索引以提高查询性能
    op.create_index(op.f('ix_InquiryCommunicationMedia_communication_id'), 'InquiryCommunicationMedia', ['communication_id'])
    op.create_index(op.f('ix_InquiryCommunicationMedia_file_type'), 'InquiryCommunicationMedia', ['file_type'])
    op.create_index(op.f('ix_InquiryCommunicationMedia_upload_time'), 'InquiryCommunicationMedia', ['upload_time'])


def downgrade():
    # 删除索引
    op.drop_index(op.f('ix_InquiryCommunicationMedia_upload_time'), table_name='InquiryCommunicationMedia')
    op.drop_index(op.f('ix_InquiryCommunicationMedia_file_type'), table_name='InquiryCommunicationMedia')
    op.drop_index(op.f('ix_InquiryCommunicationMedia_communication_id'), table_name='InquiryCommunicationMedia')
    
    # 删除 InquiryCommunicationMedia 表
    op.drop_table('InquiryCommunicationMedia')