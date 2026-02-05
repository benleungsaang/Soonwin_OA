"""
Modify OrderInspectionStatusLog table structure

Revision ID: 20260203_153000
Revises: 022_add_data_change_stats_table
Create Date: 2026-02-03 15:30:00.000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

# revision identifiers
revision = '20260203_153000'
down_revision = '022_add_data_change_stats_table'
branch_labels = None
depends_on = None

def upgrade():
    # 这新表结构已在数据库中手动修改，此迁移文件仅用于同步Alembic版本
    pass

def downgrade():
    # 降级操作（还原到旧结构）
    # 1. 重命名当前表
    op.execute('ALTER TABLE OrderInspectionStatusLog RENAME TO OrderInspectionStatusLog_old')
    
    # 2. 创建旧表结构
    op.execute('''
        CREATE TABLE OrderInspectionStatusLog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_id INTEGER NOT NULL,
            status INTEGER NOT NULL,
            status_time DATETIME,
            create_time DATETIME DEFAULT (datetime('now')),
            FOREIGN KEY (inspection_id) REFERENCES OrderInspection(id)
        )
    ''')
    
    # 3. 转换数据（将文本状态转换回数字状态）
    op.execute('''
        INSERT INTO OrderInspectionStatusLog (inspection_id, status, status_time, create_time)
        SELECT 
            inspection_id,
            CASE 
                WHEN status = '下单' THEN 1
                WHEN status = '采购' THEN 2
                WHEN status = '排产' THEN 3
                WHEN status = '完成生产' THEN 4
                WHEN status = '验收' THEN 5
                WHEN status = '发货' THEN 6
                ELSE 2  -- 默认为采购
            END,
            start_time,
            datetime('now')
        FROM OrderInspectionStatusLog_old
    ''')
    
    # 4. 删除临时表
    op.execute('DROP TABLE OrderInspectionStatusLog_old')