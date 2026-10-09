"""Add short-lived administrator QR device binding sessions."""
from alembic import op
import sqlalchemy as sa

revision = 'device_binding_qr_sessions_20261009'
down_revision = 'baseline_20261006'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'device_binding_session',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('token', sa.String(length=128), nullable=False),
        sa.Column('emp_id', sa.String(length=20), nullable=False),
        sa.Column('created_by', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('device_id', sa.String(length=100), nullable=True),
        sa.Column('device_info', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('scanned_at', sa.DateTime(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('decided_by', sa.String(length=20), nullable=True),
        sa.UniqueConstraint('token'),
    )
    op.create_index('ix_device_binding_session_emp_id', 'device_binding_session', ['emp_id'])
    op.create_index('ix_device_binding_session_created_by', 'device_binding_session', ['created_by'])
    op.create_index('ix_device_binding_session_status', 'device_binding_session', ['status'])
    op.create_index('ix_device_binding_session_expires_at', 'device_binding_session', ['expires_at'])


def downgrade():
    op.drop_index('ix_device_binding_session_expires_at', table_name='device_binding_session')
    op.drop_index('ix_device_binding_session_status', table_name='device_binding_session')
    op.drop_index('ix_device_binding_session_created_by', table_name='device_binding_session')
    op.drop_index('ix_device_binding_session_emp_id', table_name='device_binding_session')
    op.drop_table('device_binding_session')
