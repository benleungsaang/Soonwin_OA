"""add task tables

任务跟踪模块：5 张表迁移
- task: 主表（待办内容、状态、附图、底色、点赞计数等）
- task_comment: 留言（软删除）
- task_visibility: 可见性（role / employee）
- task_like: 点赞（复合主键 task_id + user_id）
- task_history: 修改历史（JSON 快照）

Revision ID: 042_add_task_tables
Revises: 041_add_module_visibility_table
Create Date: 2026-07-11 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '042_add_task_tables'
down_revision = '041_add_module_visibility_table'
branch_labels = None
depends_on = None


def upgrade():
    """创建 5 张任务跟踪相关表（每张表前都加防御性检查，已存在则跳过）"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # ============ 1. task 主表 ============
    if 'task' not in existing_tables:
        op.create_table(
            'task',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('author_id', sa.String(length=100), nullable=False, server_default=''),
            sa.Column('author_name', sa.String(length=100), nullable=False, server_default=''),
            sa.Column('content', sa.Text(), nullable=False, server_default=''),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('completion_note', sa.Text(), nullable=True),
            sa.Column('completion_image_url', sa.String(length=500), nullable=True),
            sa.Column('todo_image_url', sa.String(length=500), nullable=True),
            sa.Column('expected_date', sa.String(length=10), nullable=True),
            sa.Column('background_color', sa.String(length=20), nullable=True),
            sa.Column('like_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('is_deleted', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_task_author_id', 'task', ['author_id'])
        op.create_index('ix_task_status', 'task', ['status'])
        op.create_index('ix_task_created_at', 'task', ['created_at'])

    # ============ 2. task_comment 留言表 ============
    if 'task_comment' not in existing_tables:
        op.create_table(
            'task_comment',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('task_id', sa.Integer(), nullable=False),
            sa.Column('author_id', sa.String(length=100), nullable=True, server_default=''),
            sa.Column('author_name', sa.String(length=100), nullable=False, server_default='匿名'),
            sa.Column('content', sa.Text(), nullable=False, server_default=''),
            sa.Column('is_deleted', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_by', sa.String(length=100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['task_id'], ['task.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_task_comment_task_id', 'task_comment', ['task_id'])

    # ============ 3. task_visibility 可见性表 ============
    if 'task_visibility' not in existing_tables:
        op.create_table(
            'task_visibility',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('task_id', sa.Integer(), nullable=False),
            sa.Column('visibility_type', sa.String(length=20), nullable=False),
            sa.Column('visibility_value', sa.String(length=100), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['task_id'], ['task.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_task_visibility_task_id', 'task_visibility', ['task_id'])
        op.create_index('ix_task_visibility_type_value', 'task_visibility',
                        ['visibility_type', 'visibility_value'])

    # ============ 4. task_like 点赞表 ============
    if 'task_like' not in existing_tables:
        op.create_table(
            'task_like',
            sa.Column('task_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.String(length=100), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['task_id'], ['task.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('task_id', 'user_id'),
            sa.UniqueConstraint('task_id', 'user_id', name='uq_task_user_like'),
        )
        op.create_index('ix_task_like_user_id', 'task_like', ['user_id'])

    # ============ 5. task_history 修改历史表 ============
    if 'task_history' not in existing_tables:
        op.create_table(
            'task_history',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('task_id', sa.Integer(), nullable=False),
            sa.Column('snapshot_json', sa.Text(), nullable=False, server_default=''),
            sa.Column('modified_by', sa.String(length=100), nullable=True, server_default=''),
            sa.Column('modified_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['task_id'], ['task.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_task_history_task_id', 'task_history', ['task_id'])


def downgrade():
    """回滚：按相反顺序删除 5 张表"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'task_history' in existing_tables:
        op.drop_table('task_history')
    if 'task_like' in existing_tables:
        op.drop_table('task_like')
    if 'task_visibility' in existing_tables:
        op.drop_table('task_visibility')
    if 'task_comment' in existing_tables:
        op.drop_table('task_comment')
    if 'task' in existing_tables:
        op.drop_table('task')