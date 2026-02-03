"""创建订单进度跟踪相关表

Revision ID: 20260203_154500_add_order_progress_tables
Revises: 20260203_153000_modify_order_inspection_status_log_table_structure
Create Date: 2026-02-03 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime

# revision identifiers
revision = '20260203_154500_add_order_progress_tables'
down_revision = '20260203_153000_modify_order_inspection_status_log_table_structure'
branch_labels = None
depends_on = None

def generate_uuid():
    return str(uuid.uuid4())

def upgrade():
    # 创建订单进度表
    op.create_table(
        'order_progress',
        sa.Column('id', sa.String(36), primary_key=True, default=generate_uuid, comment='进度表ID'),
        sa.Column('order_id', sa.String(36), sa.ForeignKey('Order.id'), unique=True, nullable=False, comment='关联订单ID'),
        sa.Column('current_status', sa.String(50), comment='当前进度状态：下单/采购/排产/生产/发货/完成'),
        sa.Column('create_time', sa.DateTime, default=datetime.now, comment='进度表创建时间')
    )

    # 创建进度状态详情表
    op.create_table(
        'progress_status_detail',
        sa.Column('id', sa.String(36), primary_key=True, default=generate_uuid, comment='状态详情ID'),
        sa.Column('progress_id', sa.String(36), sa.ForeignKey('order_progress.id'), nullable=False, comment='关联进度表ID'),
        sa.Column('status', sa.String(50), nullable=False, comment='状态名称：下单/采购/排产...'),
        sa.Column('start_time', sa.DateTime, comment='状态开始时间'),
        sa.Column('expected_complete_time', sa.DateTime, comment='预计完成时间'),
        sa.Column('actual_complete_time', sa.DateTime, comment='实际完成时间')
    )

    # 创建进度项表
    op.create_table(
        'progress_item',
        sa.Column('id', sa.String(36), primary_key=True, default=generate_uuid, comment='进度项ID'),
        sa.Column('progress_id', sa.String(36), sa.ForeignKey('order_progress.id'), nullable=False, comment='关联进度表ID'),
        sa.Column('title', sa.String(200), nullable=False, comment='进度项标题'),
        sa.Column('status', sa.String(20), default='未完成', comment='进度项状态：未完成/已完成'),
        sa.Column('remark', sa.Text, comment='备注信息'),
        sa.Column('create_time', sa.DateTime, default=datetime.now, comment='创建时间'),
        sa.Column('update_time', sa.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    )

    # 创建进度项多媒体文件表
    op.create_table(
        'progress_media',
        sa.Column('id', sa.String(36), primary_key=True, default=generate_uuid, comment='多媒体文件ID'),
        sa.Column('item_id', sa.String(36), sa.ForeignKey('progress_item.id'), nullable=False, comment='关联进度项ID'),
        sa.Column('file_type', sa.String(20), comment='文件类型：image/video'),
        sa.Column('file_url', sa.String(500), nullable=False, comment='文件存储路径/URL'),
        sa.Column('file_name', sa.String(200), comment='原始文件名'),
        sa.Column('upload_time', sa.DateTime, default=datetime.now, comment='上传时间')
    )


def downgrade():
    # 删除进度项多媒体文件表
    op.drop_table('progress_media')
    
    # 删除进度项表
    op.drop_table('progress_item')
    
    # 删除进度状态详情表
    op.drop_table('progress_status_detail')
    
    # 删除订单进度表
    op.drop_table('order_progress')