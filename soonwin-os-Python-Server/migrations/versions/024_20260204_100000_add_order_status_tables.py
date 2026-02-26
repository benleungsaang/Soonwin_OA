"""add order status tables

Revision ID: 20260204_100000_add_order_status_tables
Revises: 20260203_154500_add_order_progress_tables
Create Date: 2026-02-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

# revision identifiers
revision = '024_20260204_100000_add_order_status_tables'
down_revision = '20260203_153000'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 order_status 表
    op.create_table(
        'order_status',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('current_status', sa.Integer(), nullable=True, default=1, comment="当前订单状态: 1-下单, 2-排产, 3-完成生产, 4-验收阶段, 5-发货"),
        sa.Column('current_status_time', sa.DateTime(), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False, default=datetime.now),
        sa.Column('update_time', sa.DateTime(), nullable=False, default=datetime.now, onupdate=datetime.now),
        sa.Column('progress_status', sa.String(20), nullable=True, default='pending', comment="进度状态: pending(待开始), in_progress(进行中), completed(已完成)"),
        sa.Column('progress_percent', sa.Integer(), nullable=True, default=0, comment="进度百分比（0-100）"),
        sa.Column('total_tasks', sa.Integer(), nullable=True, default=0, comment="总任务项数"),
        sa.Column('completed_tasks', sa.Integer(), nullable=True, default=0, comment="已完成任务项数"),
        sa.ForeignKeyConstraint(['order_id'], ['Order.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='订单进度主表'
    )

    # 创建 order_status_log 表
    op.create_table(
        'order_status_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_status_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, comment="状态值: 下单、排产、完成生产、验收阶段、发货"),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('expected_completion_time', sa.DateTime(), nullable=True),
        sa.Column('actual_completion_time', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_status_id'], ['order_status.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='订单状态流水表'
    )

    # 创建 status_task 表
    op.create_table(
        'status_task',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_status_id', sa.Integer(), nullable=False),
        sa.Column('status_log_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, comment="任务类别（如：配件、外观、性能等）"),
        sa.Column('name', sa.String(200), nullable=False, comment="任务名称（如：部件1、角度1、运行速度等）"),
        sa.Column('is_completed', sa.Boolean(), nullable=True, default=False, comment="是否完成任务：False-未完成，True-完成"),
        sa.Column('photo_path', sa.String(500), nullable=True, comment="照片路径，多张图片路径以逗号分隔"),
        sa.Column('description', sa.Text(), nullable=True, comment="描述（可记录任务结果、异常信息等）"),
        sa.Column('sort', sa.Integer(), nullable=True, default=0, comment="排序序号"),
        sa.Column('create_time', sa.DateTime(), nullable=False, default=datetime.now),
        sa.Column('update_time', sa.DateTime(), nullable=False, default=datetime.now, onupdate=datetime.now),
        sa.ForeignKeyConstraint(['order_status_id'], ['order_status.id'], ),
        sa.ForeignKeyConstraint(['status_log_id'], ['order_status_log.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='进度任务项表'
    )

    # 为 order_status 表添加索引
    op.create_index('idx_order_status_order_id', 'order_status', ['order_id'])
    op.create_index('idx_order_status_current_status', 'order_status', ['current_status'])

    # 为 order_status_log 表添加索引
    op.create_index('idx_order_status_log_order_status_id', 'order_status_log', ['order_status_id'])

    # 为 status_task 表添加索引
    op.create_index('idx_status_task_order_status_id', 'status_task', ['order_status_id'])
    op.create_index('idx_status_task_status_log_id', 'status_task', ['status_log_id'])


def downgrade():
    # 删除 status_task 表
    op.drop_index('idx_status_task_status_log_id', table_name='status_task')
    op.drop_index('idx_status_task_order_status_id', table_name='status_task')
    op.drop_table('status_task')

    # 删除 order_status_log 表
    op.drop_index('idx_order_status_log_order_status_id', table_name='order_status_log')
    op.drop_table('order_status_log')

    # 删除 order_status 表
    op.drop_index('idx_order_status_current_status', table_name='order_status')
    op.drop_index('idx_order_status_order_id', table_name='order_status')
    op.drop_table('order_status')