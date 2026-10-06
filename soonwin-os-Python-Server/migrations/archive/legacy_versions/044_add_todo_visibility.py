"""add todo visibility table

待办事项可见性配置表迁移
- todo_visibility: 管理员设置的可见性记录（员工级共享）

Revision ID: 044_add_todo_visibility
Revises: 043_add_todo_tables
Create Date: 2026-07-21 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '044_add_todo_visibility'
down_revision = '043_add_todo_tables'
branch_labels = None
depends_on = None


def upgrade():
    """创建 todo_visibility 表（防御性检查，已存在则跳过）"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'todo_visibility' not in existing_tables:
        op.create_table(
            'todo_visibility',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('todo_id', sa.Integer(), nullable=False, comment='关联 todo id'),
            sa.Column('user_id', sa.String(length=20), nullable=False, comment='可见员工 emp_id'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['todo_id'], ['todo.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('todo_id', 'user_id', name='uq_todo_visibility'),
        )
        op.create_index('ix_todo_visibility_todo_id', 'todo_visibility', ['todo_id'])
        op.create_index('ix_todo_visibility_user_id', 'todo_visibility', ['user_id'])


def downgrade():
    """删除 todo_visibility 表"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'todo_visibility' in existing_tables:
        op.drop_table('todo_visibility')
