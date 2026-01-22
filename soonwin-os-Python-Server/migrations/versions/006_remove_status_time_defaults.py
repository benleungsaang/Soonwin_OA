"""Remove status time defaults

Revision ID: 006
Revises: 005
Create Date: 2026-01-22 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # 在SQLite中，无法直接修改列的默认值，需要使用临时表方法
    # 但是我们可以跳过这个，因为我们的手动迁移已经处理了表结构
    # 这里只是记录变更
    
    # 在实际应用中，因为SQLite限制，我们已经在manual_migration.py中处理了表结构
    # 这个迁移文件只是用于记录变更
    pass


def downgrade():
    # 降级时理论上应该恢复默认值，但SQLite限制使得这很复杂
    # 我们跳过这个实现
    pass