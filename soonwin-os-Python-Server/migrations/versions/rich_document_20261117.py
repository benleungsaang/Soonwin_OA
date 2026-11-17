"""Add private rich documents and their media."""
from alembic import op
import sqlalchemy as sa
revision = 'rich_document_20261117'
down_revision = 'display_image_manifest_20261111'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('rich_document', sa.Column('id', sa.Integer, primary_key=True), sa.Column('owner', sa.String(20), nullable=False), sa.Column('title', sa.String(200), nullable=False), sa.Column('html', sa.Text, nullable=False), sa.Column('watermark', sa.Text, nullable=False), sa.Column('version', sa.Integer, nullable=False), sa.Column('created_at', sa.DateTime, nullable=False), sa.Column('updated_at', sa.DateTime, nullable=False), sa.Column('deleted_at', sa.DateTime))
    op.create_index('ix_rich_document_owner', 'rich_document', ['owner'])
    op.create_table('rich_media', sa.Column('id', sa.String(32), primary_key=True), sa.Column('document_id', sa.Integer, sa.ForeignKey('rich_document.id'), nullable=False), sa.Column('filename', sa.String(255), nullable=False), sa.Column('mime', sa.String(80), nullable=False), sa.Column('size', sa.Integer, nullable=False))
    op.create_index('ix_rich_media_document_id', 'rich_media', ['document_id'])

def downgrade():
    op.drop_table('rich_media')
    op.drop_table('rich_document')
