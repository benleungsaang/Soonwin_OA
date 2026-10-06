"""add app version history table

Revision ID: 045_add_app_version_history
Revises: 044_add_todo_visibility
Create Date: 2026-09-30 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '045_add_app_version_history'
down_revision = '044_add_todo_visibility'
branch_labels = None
depends_on = None


def upgrade():
    """创建版本历史表；已有表时不修改任何现有对象。"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'app_version_history' in inspector.get_table_names():
        return

    op.create_table(
        'app_version_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('git_hash', sa.String(length=40), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version', name='uq_app_version_history_version'),
    )
    op.create_index('ix_app_version_history_date', 'app_version_history', ['date'])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'app_version_history' in inspector.get_table_names():
        op.drop_table('app_version_history')
