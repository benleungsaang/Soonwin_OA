"""Record original names and upload order for display image groups."""
from alembic import op
import sqlalchemy as sa

revision = 'display_image_manifest_20261111'
down_revision = 'nas_upload_log_20261106'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('DisplayFile', sa.Column('image_manifest', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('DisplayFile', 'image_manifest')
