"""add data_change_stats table

Revision ID: 022_add_data_change_stats_table
Revises: 021_add_business_operation_log_table.py
Create Date: 2026-02-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '022_add_data_change_stats_table'
down_revision = '021_add_business_operation_log_table'
branch_labels = None
depends_on = None


def upgrade():
    # 创建数据变化统计表
    op.execute(text("""
        CREATE TABLE data_change_stats (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            module VARCHAR(50) NOT NULL,
            stats_type VARCHAR(50) NOT NULL,
            stats_value INTEGER DEFAULT 0,
            reset_time DATETIME,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    # 创建索引
    op.create_index('idx_module_stats_type', 'data_change_stats', ['module', 'stats_type'], unique=True)


def downgrade():
    # 删除索引
    op.drop_index('idx_module_stats_type', table_name='data_change_stats')
    
    # 删除表
    op.drop_table('data_change_stats')