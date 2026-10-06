"""添加考勤管理权限

Revision ID: 033_20260228_100000
Revises: 032_20260226_110000_add_creator_id_to_order
Create Date: 2026-02-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '033_20260228_100000'
down_revision = '032_20260226_110000_add_creator_id_to_order'
branch_labels = None
depends_on = None


def upgrade():
    # 添加考勤管理权限到权限表
    # 根据数据库中实际存在的表结构，使用role_permission_simple表
    connection = op.get_bind()
    
    # 获取admin角色的ID
    result = connection.execute(
        sa.text("SELECT id FROM role WHERE name = 'admin'")
    ).fetchone()
    
    if result:
        admin_role_id = result[0]
        
        # 插入考勤管理路由权限
        connection.execute(
            sa.text("""
            INSERT INTO role_permission_simple (role_id, route_name) 
            VALUES (:role_id, :route_name)
            """),
            {
                'role_id': admin_role_id,
                'route_name': 'attendance'  # 考勤相关路由权限
            }
        )
    
    # 获取user角色的ID
    result = connection.execute(
        sa.text("SELECT id FROM role WHERE name = 'user'")
    ).fetchone()
    
    if result:
        user_role_id = result[0]
        
        # 为普通用户添加考勤相关权限
        connection.execute(
            sa.text("""
            INSERT INTO role_permission_simple (role_id, route_name) 
            VALUES (:role_id, :route_name)
            """),
            {
                'role_id': user_role_id,
                'route_name': 'attendance'  # 考勤相关路由权限
            }
        )


def downgrade():
    # 删除考勤管理权限
    connection = op.get_bind()
    
    connection.execute(
        sa.text("DELETE FROM role_permission_simple WHERE route_name = 'attendance'")
    )