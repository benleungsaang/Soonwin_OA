"""add container_layout table

手动编写迁移（绕过 alembic autogenerate，避免 ExpenseAllocation 等已存在问题表的连带检查）。

Revision ID: 040_add_container_layout_table
Revises: a206ea861ff1
Create Date: 2026-06-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '040_add_container_layout_table'
down_revision = 'a206ea861ff1'
branch_labels = None
depends_on = None


def upgrade():
    """创建 container_layout 表"""
    op.create_table(
        'container_layout',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('container_json', sa.Text(), nullable=False),
        sa.Column('author_id', sa.String(length=32), nullable=False),
        sa.Column('author_name', sa.String(length=64), nullable=False),
        sa.Column('is_deleted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    # 索引：按作者/删除标志/更新时间查询加速
    op.create_index('ix_container_layout_author_id', 'container_layout', ['author_id'])
    op.create_index('ix_container_layout_is_deleted', 'container_layout', ['is_deleted'])


def downgrade():
    """回滚"""
    op.drop_index('ix_container_layout_is_deleted', table_name='container_layout')
    op.drop_index('ix_container_layout_author_id', table_name='container_layout')
    op.drop_table('container_layout')