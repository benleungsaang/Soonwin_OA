"""Add machine and part_type tables

Revision ID: 008_add_machine_and_part_types_tables
Revises: 007_rename_phone_mac_to_device_id
Create Date: 2026-01-28 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '008_add_machine_and_part_types_tables'
down_revision = '007_rename_phone_mac_to_device_id'
branch_labels = None
depends_on = None


def upgrade():
    # 创建machines表
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS machines (
            model TEXT PRIMARY KEY,
            original_model TEXT,
            packing_speed TEXT,
            general_power TEXT,
            power_supply TEXT,
            air_source TEXT,
            machine_weight TEXT,
            dimensions TEXT,
            package_material TEXT,
            image TEXT,
            added_count INTEGER DEFAULT 0,
            original_price DECIMAL(10,2),
            show_price DECIMAL(10,2),
            custom_attrs TEXT
        )
    """))
    
    # 创建part_types表
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS part_types (
            part_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_model TEXT UNIQUE NOT NULL,
            original_price DECIMAL(10,2),
            show_price DECIMAL(10,2),
            image TEXT
        )
    """))


def downgrade():
    # 删除machines表
    op.drop_table('machines')
    
    # 删除part_types表
    op.drop_table('part_types')