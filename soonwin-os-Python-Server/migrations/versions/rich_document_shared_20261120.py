"""Add rich document sharing flag."""
from alembic import op
import sqlalchemy as sa

revision = 'rich_document_shared_20261120'
down_revision = 'rich_document_20261117'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('rich_document', sa.Column('is_shared', sa.Boolean(), nullable=False, server_default=sa.false()))

def downgrade():
    with op.batch_alter_table('rich_document') as batch:
        batch.drop_column('is_shared')
