"""
add business operation log table

Revision ID: 021_add_business_operation_log_table
Revises: 020_add_delete_time_to_video
Create Date: 2026-02-02 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '021_add_business_operation_log_table'
down_revision = '020_add_delete_time_to_video'
branch_labels = None
depends_on = None


def upgrade():
    # 创建business_operation_log表
    op.create_table(
        'business_operation_log',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('module', sa.String(length=50), nullable=False),
        sa.Column('biz_id', sa.String(length=50), nullable=False),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('operator_id', sa.String(length=20), nullable=False),
        sa.Column('operation_details', sa.Text(), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False, default=datetime.now),
        sa.PrimaryKeyConstraint('id'),
        comment='通用业务操作日志表（适配询盘/视频/图片/人员等所有管理功能）'
    )
    
    # 创建索引以提高查询性能
    op.create_index('idx_module', 'business_operation_log', ['module'])
    op.create_index('idx_operation_type', 'business_operation_log', ['operation_type'])
    op.create_index('idx_create_time', 'business_operation_log', ['create_time'])
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_business_operation_log_operator',
        'business_operation_log',
        'Employee',
        ['operator_id'],
        ['emp_id']
    )


def downgrade():
    # 删除外键约束
    op.drop_constraint(
        'fk_business_operation_log_operator',
        'business_operation_log',
        type_='foreignkey'
    )
    
    # 删除索引
    op.drop_index('idx_create_time', table_name='business_operation_log')
    op.drop_index('idx_operation_type', table_name='business_operation_log')
    op.drop_index('idx_module', table_name='business_operation_log')
    
    # 删除表
    op.drop_table('business_operation_log')