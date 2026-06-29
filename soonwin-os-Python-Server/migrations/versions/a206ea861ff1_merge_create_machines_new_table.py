"""merge create_machines_new_table

Revision ID: a206ea861ff1
Revises: 001_create_machines_new_table, 039_20260429_100000_merge_order_record_items
Create Date: 2026-06-29 20:27:31.171235

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a206ea861ff1'
down_revision = ('001_create_machines_new_table', '039_20260429_100000_merge_order_record_items')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
