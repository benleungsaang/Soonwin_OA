"""Add order status fields and log table

Revision ID: 005
Revises: 004_remove_display_mode_add_page_count
Create Date: 2026-01-22 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # 添加新字段到OrderInspection表
    with op.batch_alter_table('OrderInspection', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_status', sa.Integer(), nullable=True, default=1, comment='当前订单状态: 1-下单, 2-排产, 3-完成生产, 4-验收阶段, 5-发货'))
        batch_op.add_column(sa.Column('current_status_time', sa.DateTime(), nullable=True, comment='当前状态时间'))
        
        # 为现有记录设置默认值
        # 执行后设置所有现有记录的当前状态为1（下单）
        # 注意：在SQLite中，我们不能在ALTER语句中引用其他列，所以需要在代码中处理
    
    # 创建OrderInspectionStatusLog表
    op.create_table('OrderInspectionStatusLog',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('inspection_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Integer(), nullable=False),
        sa.Column('status_time', sa.DateTime(), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['OrderInspection.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='订单状态流水表'
    )
    
    # 为新表添加索引
    op.create_index('ix_order_inspection_status_log_inspection_id', 'OrderInspectionStatusLog', ['inspection_id'])
    op.create_index('ix_order_inspection_status_log_status', 'OrderInspectionStatusLog', ['status'])
    op.create_index('ix_order_inspection_status_log_status_time', 'OrderInspectionStatusLog', ['status_time'])
    
    # 更新现有记录的默认值
    # 由于SQLite限制，需要在upgrade完成后的应用代码中处理


def downgrade():
    # 删除OrderInspectionStatusLog表
    op.drop_table('OrderInspectionStatusLog')
    
    # 从OrderInspection表中删除新字段
    with op.batch_alter_table('OrderInspection', schema=None) as batch_op:
        batch_op.drop_column('current_status_time')
        batch_op.drop_column('current_status')