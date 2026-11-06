"""Add audit records for QR-authorized NAS uploads."""
from alembic import op
import sqlalchemy as sa


revision = 'nas_upload_log_20261106'
down_revision = 'device_binding_qr_sessions_20261009'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'nas_upload_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('upload_id', sa.String(length=32), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('operator_id', sa.String(length=20), nullable=True),
        sa.Column('operator_name', sa.String(length=50), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('target_dir', sa.String(length=255), nullable=False),
        sa.UniqueConstraint('upload_id', name='uq_nas_upload_log_upload_id'),
    )
    op.create_index('ix_nas_upload_log_uploaded_at', 'nas_upload_log', ['uploaded_at'])
    op.create_index('ix_nas_upload_log_filename', 'nas_upload_log', ['filename'])


def downgrade():
    op.drop_index('ix_nas_upload_log_filename', table_name='nas_upload_log')
    op.drop_index('ix_nas_upload_log_uploaded_at', table_name='nas_upload_log')
    op.drop_table('nas_upload_log')
