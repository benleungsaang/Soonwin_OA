"""update file paths to use Media directory

Revision ID: 011_update_file_paths
Revises: 010_add_video_table
Create Date: 2026-01-30 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String

# revision identifiers
revision = '011_update_file_paths'
down_revision = '010_add_video_table'
branch_labels = None
depends_on = None


def upgrade():
    # 更新照片表中的文件路径
    photos_table = table('photos',
        column('thumbnail_path', String),
        column('original_path', String),
        column('normal_path', String)
    )
    
    # 将 MachinePhoto 路径更新为 Media/Photos
    op.execute(
        photos_table.update()
        .where(photos_table.c.thumbnail_path.like('%MachinePhoto%'))
        .values(thumbnail_path=sa.func.replace(photos_table.c.thumbnail_path, 'MachinePhoto', 'Media/Photos'))
    )
    
    op.execute(
        photos_table.update()
        .where(photos_table.c.original_path.like('%MachinePhoto%'))
        .values(original_path=sa.func.replace(photos_table.c.original_path, 'MachinePhoto', 'Media/Photos'))
    )
    
    op.execute(
        photos_table.update()
        .where(photos_table.c.normal_path.like('%MachinePhoto%'))
        .values(normal_path=sa.func.replace(photos_table.c.normal_path, 'MachinePhoto', 'Media/Photos'))
    )


def downgrade():
    # 将 Media/Photos 路径还原为 MachinePhoto
    photos_table = table('photos',
        column('thumbnail_path', String),
        column('original_path', String),
        column('normal_path', String)
    )
    
    op.execute(
        photos_table.update()
        .where(photos_table.c.thumbnail_path.like('%Media/Photos%'))
        .values(thumbnail_path=sa.func.replace(photos_table.c.thumbnail_path, 'Media/Photos', 'MachinePhoto'))
    )
    
    op.execute(
        photos_table.update()
        .where(photos_table.c.original_path.like('%Media/Photos%'))
        .values(original_path=sa.func.replace(photos_table.c.original_path, 'Media/Photos', 'MachinePhoto'))
    )
    
    op.execute(
        photos_table.update()
        .where(photos_table.c.normal_path.like('%Media/Photos%'))
        .values(normal_path=sa.func.replace(photos_table.c.normal_path, 'Media/Photos', 'MachinePhoto'))
    )