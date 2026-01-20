"""add device management tables and improve existing tables

Revision ID: 001
Revises: 
Create Date: 2026-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建EmployeeDevice表，用于管理多设备绑定
    op.create_table('EmployeeDevice',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('emp_id', sa.String(20), nullable=False),
        sa.Column('device_mac', sa.String(20), nullable=False),
        sa.Column('device_ip', sa.String(20), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('device_info', sa.String(200), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.now),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.now, onupdate=datetime.now),
        sa.ForeignKeyConstraint(['emp_id'], ['Employee.emp_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 为EmployeeDevice表的device_mac创建唯一索引
    op.create_index('ix_employee_device_mac', 'EmployeeDevice', ['device_mac'], unique=True)
    
    # 为EmployeeDevice表的emp_id创建索引
    op.create_index('ix_employee_device_emp_id', 'EmployeeDevice', ['emp_id'])


def downgrade():
    # 删除索引
    op.drop_index('ix_employee_device_mac')
    op.drop_index('ix_employee_device_emp_id')
    
    # 删除EmployeeDevice表
    op.drop_table('EmployeeDevice')