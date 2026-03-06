"""create machines_new table

Revision ID: 001_create_machines_new_table
Revises: 
Create Date: 2026-03-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, TEXT, Integer, DECIMAL, DateTime


# revision identifiers
revision = '001_create_machines_new_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建machines_new表
    op.create_table('machines_new',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model', sa.TEXT(), nullable=True),
        sa.Column('original_model', sa.TEXT(), nullable=True),
        sa.Column('machine_weight', sa.TEXT(), nullable=True),
        sa.Column('dimensions', sa.TEXT(), nullable=True),
        sa.Column('general_power', sa.TEXT(), nullable=True),
        sa.Column('power_supply', sa.TEXT(), nullable=True),
        sa.Column('image', sa.TEXT(), nullable=True),
        sa.Column('added_count', sa.Integer(), nullable=True),
        sa.Column('show_price', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('original_price', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('machine_type', sa.Integer(), nullable=True),
        sa.Column('remark', sa.TEXT(), nullable=True),
        sa.Column('brand', sa.TEXT(), nullable=True),
        sa.Column('search_key', sa.TEXT(), nullable=True),
        sa.Column('custom_attrs', sa.TEXT(), nullable=True),
        sa.Column('is_deleted', sa.Integer(), nullable=True),
        sa.Column('delete_time', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('idx_machines_new_model', 'machines_new', ['model'], unique=False)
    op.create_index('idx_machines_new_search_key', 'machines_new', ['search_key'], unique=False)
    op.create_index('idx_machines_new_is_deleted', 'machines_new', ['is_deleted'], unique=False)


def downgrade():
    # 删除machines_new表
    op.drop_table('machines_new')