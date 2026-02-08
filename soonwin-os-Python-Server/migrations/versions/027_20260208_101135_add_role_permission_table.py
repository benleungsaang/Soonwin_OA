"""添加角色权限表

Revision ID: 027_20260208_101135_add_role_permission_table
Revises: 026_20260207_160000_add_media_file_table
Create Date: 2026-02-08 10:11:35.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '027_20260208_101135_add_role_permission_table'
down_revision = '026_20260207_160000_add_media_file_table'
branch_labels = None
depends_on = None


def generate_uuid():
    return str(uuid.uuid4())


def upgrade():
    # 创建RolePermission表
    op.create_table('RolePermission',
        sa.Column('id', sa.String(36), nullable=False),  # 使用字符串存储UUID
        sa.Column('role_name', sa.String(length=10), nullable=False),
        sa.Column('module_name', sa.String(length=50), nullable=False),
        sa.Column('can_view', sa.Boolean(), nullable=False, default=True),
        sa.Column('can_edit', sa.Boolean(), nullable=False, default=False),
        sa.Column('can_delete', sa.Boolean(), nullable=False, default=False),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('update_time', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_name', 'module_name', name='uq_role_module')
    )
    
    # 添加默认数据
    connection = op.get_bind()
    
    # 管理员权限：所有模块都有全部权限
    connection.execute(
        sa.text("""
        INSERT INTO RolePermission (id, role_name, module_name, can_view, can_edit, can_delete, create_time) 
        VALUES (?, 'admin', 'employee_manage', 1, 1, 1, ?)
        """), (generate_uuid(), datetime.now())
    )
    
    connection.execute(
        sa.text("""
        INSERT INTO RolePermission (id, role_name, module_name, can_view, can_edit, can_delete, create_time) 
        VALUES (?, 'admin', 'device_manage', 1, 1, 1, ?)
        """), (generate_uuid(), datetime.now())
    )
    
    connection.execute(
        sa.text("""
        INSERT INTO RolePermission (id, role_name, module_name, can_view, can_edit, can_delete, create_time) 
        VALUES (?, 'admin', 'permission_manage', 1, 1, 1, ?)
        """), (generate_uuid(), datetime.now())
    )
    
    # 销售权限：只能查看和编辑设备管理，不能删除
    connection.execute(
        sa.text("""
        INSERT INTO RolePermission (id, role_name, module_name, can_view, can_edit, can_delete, create_time) 
        VALUES (?, 'sales', 'device_manage', 1, 1, 0, ?)
        """), (generate_uuid(), datetime.now())
    )
    
    connection.execute(
        sa.text("""
        INSERT INTO RolePermission (id, role_name, module_name, can_view, can_edit, can_delete, create_time) 
        VALUES (?, 'sales', 'employee_manage', 1, 0, 0, ?)
        """), (generate_uuid(), datetime.now())
    )
    
    # 普通用户权限：只能查看自己相关的信息
    connection.execute(
        sa.text("""
        INSERT INTO RolePermission (id, role_name, module_name, can_view, can_edit, can_delete, create_time) 
        VALUES (?, 'user', 'device_manage', 1, 0, 0, ?)
        """), (generate_uuid(), datetime.now())
    )


def downgrade():
    # 删除RolePermission表
    op.drop_table('RolePermission')