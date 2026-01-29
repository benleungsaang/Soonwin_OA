"""Add photo table and update machines table for soft delete

Revision ID: 009_add_photo_table_and_soft_delete_machines
Revises: 008_add_machine_and_part_types_tables
Create Date: 2026-01-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '009_add_photo_table_and_soft_delete_machines'
down_revision = '008_add_machine_and_part_types_tables'
branch_labels = None
depends_on = None


def upgrade():
    # 添加机器表逻辑删除字段
    op.add_column('machines', sa.Column('is_deleted', sa.Integer, default=0))
    op.add_column('machines', sa.Column('delete_time', sa.DateTime))
    
    # 创建照片表
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            tags TEXT,
            machine_id TEXT,
            remark TEXT,
            search_field TEXT,
            uploader TEXT NOT NULL,
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            original_path TEXT,
            thumbnail_path TEXT NOT NULL,
            normal_path TEXT NOT NULL,
            original_width INTEGER,
            original_height INTEGER,
            file_size INTEGER,
            compress_status TEXT DEFAULT 'pending',
            FOREIGN KEY (machine_id) REFERENCES machines(model) ON DELETE SET NULL
        )
    """))
    
    # 创建索引以优化查询
    op.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_search ON photos(search_field)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_machine ON photos(machine_id)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_uploader ON photos(uploader)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_compress ON photos(compress_status)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS idx_machines_deleted ON machines(is_deleted)"))


def downgrade():
    # 删除照片表
    op.execute(text("DROP TABLE IF EXISTS photos"))
    
    # 删除机器表的逻辑删除字段
    op.drop_column('machines', 'is_deleted')
    op.drop_column('machines', 'delete_time')