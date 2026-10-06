"""remove order progress related tables

Revision ID: 029_20260225_100000_remove_order_progress_tables
Revises: 028_20260208_101136_add_role_description_to_role_permission
Create Date: 2026-02-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers
revision = '029_20260225_100000_remove_order_progress_tables'
down_revision = '028_20260208_101136_add_role_description_to_role_permission'
branch_labels = None
depends_on = None


def upgrade():
    # 删除progress_media表（因为它依赖progress_item）
    op.drop_table('progress_media')
    
    # 删除progress_item表（它依赖order_progress）
    op.drop_table('progress_item')
    
    # 删除progress_status_detail表（它依赖order_progress）
    op.drop_table('progress_status_detail')
    
    # 最后删除order_progress表
    op.drop_table('order_progress')


def downgrade():
    # 重新创建这些表（逆向操作）
    # 由于这些表已被废弃，我们不提供降级功能
    pass