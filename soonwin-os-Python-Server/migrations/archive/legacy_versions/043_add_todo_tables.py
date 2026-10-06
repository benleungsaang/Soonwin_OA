"""add todo tables

待办事项模块：3 张表迁移
- todo: 主表（任务正文、日期、颜色、附图、完成记录、状态）
- todo_message: 管理员留言（仅管理员可创建，纯文字，支持 emoji）
- todo_message_read: 红点未读记录（每用户每 todo 一条）

Revision ID: 043_add_todo_tables
Revises: 042_add_task_tables
Create Date: 2026-07-13 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '043_add_todo_tables'
down_revision = '042_add_task_tables'
branch_labels = None
depends_on = None


def upgrade():
    """创建 3 张待办事项相关表（每张表前都加防御性检查，已存在则跳过）"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # ============ 1. todo 主表 ============
    if 'todo' not in existing_tables:
        op.create_table(
            'todo',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('author_id', sa.String(length=20), nullable=False, comment='创建人 emp_id（用于用户隔离）'),
            sa.Column('author_name', sa.String(length=50), nullable=False, server_default=''),
            sa.Column('content', sa.Text(), nullable=False, server_default=''),
            sa.Column('date', sa.String(length=10), nullable=False, server_default=''),
            sa.Column('color', sa.String(length=20), nullable=False, server_default='white'),
            sa.Column('note', sa.Text(), nullable=False, server_default=''),
            sa.Column('image_url', sa.String(length=500), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('completion_note', sa.Text(), nullable=True),
            sa.Column('completion_image_url', sa.String(length=500), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('is_deleted', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_todo_author_id', 'todo', ['author_id'])
        op.create_index('ix_todo_is_deleted', 'todo', ['is_deleted'])

    # ============ 2. todo_message 留言表 ============
    if 'todo_message' not in existing_tables:
        op.create_table(
            'todo_message',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('todo_id', sa.Integer(), nullable=False),
            sa.Column('author_id', sa.String(length=20), nullable=False, server_default=''),
            sa.Column('author_name', sa.String(length=50), nullable=False, server_default='管理员'),
            sa.Column('content', sa.Text(), nullable=False, server_default=''),
            sa.Column('is_deleted', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['todo_id'], ['todo.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_todo_message_todo_id', 'todo_message', ['todo_id'])

    # ============ 3. todo_message_read 已读表 ============
    if 'todo_message_read' not in existing_tables:
        op.create_table(
            'todo_message_read',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('todo_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.String(length=20), nullable=False),
            sa.Column('last_read_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['todo_id'], ['todo.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('todo_id', 'user_id', name='uq_todo_message_read_user_todo'),
        )
        op.create_index('ix_todo_message_read_user_id', 'todo_message_read', ['user_id'])
        op.create_index('ix_todo_message_read_todo_id', 'todo_message_read', ['todo_id'])


def downgrade():
    """删除 3 张 todo 表"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'todo_message_read' in existing_tables:
        op.drop_table('todo_message_read')
    if 'todo_message' in existing_tables:
        op.drop_table('todo_message')
    if 'todo' in existing_tables:
        op.drop_table('todo')
