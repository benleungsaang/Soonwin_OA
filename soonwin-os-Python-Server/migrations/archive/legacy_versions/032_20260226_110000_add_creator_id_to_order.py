"""
Add creator_id field to Order table

Revision ID: 032_20260226_110000_add_creator_id_to_order
Revises: 031_20260226_110000_add_logic_delete_to_photos
Create Date: 2026-02-26 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '032_20260226_110000_add_creator_id_to_order'
down_revision = '031_20260226_110000_add_logic_delete_to_photos'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 creator_id 字段到 Order 表
    op.add_column('Order', sa.Column('creator_id', sa.String(20), nullable=True))
    
    # 创建外键约束
    op.create_foreign_key(
        'fk_order_creator_id',
        'Order', 
        'Employee', 
        ['creator_id'], 
        ['emp_id']
    )


def downgrade():
    # 删除外键约束
    op.drop_constraint('fk_order_creator_id', 'Order', type_='foreignkey')
    
    # 删除 creator_id 字段
    op.drop_column('Order', 'creator_id')