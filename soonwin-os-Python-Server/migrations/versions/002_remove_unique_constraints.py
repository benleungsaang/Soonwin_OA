"""remove unique constraints on MAC addresses

Revision ID: 002
Revises: 001
Create Date: 2026-01-21 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # 移除Employee表中phone_mac字段的唯一约束
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.drop_constraint('uq_employee_phone_mac', type_='unique')

    # 移除EmployeeDevice表中device_mac字段的唯一约束
    with op.batch_alter_table('EmployeeDevice', schema=None) as batch_op:
        batch_op.drop_constraint('uq_employeedevice_device_mac', type_='unique')


def downgrade():
    # 恢复Employee表中phone_mac字段的唯一约束
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_employee_phone_mac', ['phone_mac'])

    # 恢复EmployeeDevice表中device_mac字段的唯一约束
    with op.batch_alter_table('EmployeeDevice', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_employeedevice_device_mac', ['device_mac'])