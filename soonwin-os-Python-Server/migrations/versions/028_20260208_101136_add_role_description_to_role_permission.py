"""
Add role description field to RolePermission table

Revision ID: 028_20260208_101136
Revises: 027_20260208_101135_add_role_permission_table
Create Date: 2026-02-08 10:11:36.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

# revision identifiers
revision = '028_20260208_101136_add_role_description_to_role_permission'
down_revision = '027_20260208_101135_add_role_permission_table'
branch_labels = None
depends_on = None


def upgrade():
    # 添加role_description列
    op.add_column('RolePermission', sa.Column('role_description', sa.String(100), nullable=True))
    
    # 扩展role_name列的长度
    op.alter_column('RolePermission', 'role_name', type_=sa.String(50), existing_type=sa.String(10))


def downgrade():
    # 删除role_description列
    op.drop_column('RolePermission', 'role_description')
    
    # 恢复role_name列的长度
    op.alter_column('RolePermission', 'role_name', type_=sa.String(10), existing_type=sa.String(50))