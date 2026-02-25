"""Add logic delete fields to photos table

Revision ID: 031_20260226_110000_add_logic_delete_to_photos
Revises: 030_20260225_110000_add_update_time_field_to_employee_table
Create Date: 2026-02-26 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '031_20260226_110000_add_logic_delete_to_photos'
down_revision = '030_20260225_110000_add_update_time_field_to_employee_table'
branch_labels = None
depends_on = None


def upgrade():
    # 添加逻辑删除相关字段
    op.add_column('photos', sa.Column('is_deleted', sa.Integer, default=0, comment='是否删除：0-正常，1-已删除'))
    op.add_column('photos', sa.Column('delete_time', sa.DateTime, comment='删除时间'))
    op.add_column('photos', sa.Column('delete_operator', sa.String(100), comment='删除操作人'))
    
    # 创建索引以优化查询
    op.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_deleted ON photos(is_deleted)"))


def downgrade():
    # 删除逻辑删除相关字段
    op.drop_column('photos', 'is_deleted')
    op.drop_column('photos', 'delete_time')
    op.drop_column('photos', 'delete_operator')
    
    # 删除索引
    op.execute(text("DROP INDEX IF EXISTS idx_photos_deleted"))