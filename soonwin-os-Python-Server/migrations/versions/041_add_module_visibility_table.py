"""add module_visibility table

手动编写迁移（参考 040 风格，绕过 alembic autogenerate，避免与 dev 库中
已存在的 module_visibility 表产生不期望的 DROP/CREATE 行为）。

Revision ID: 041_add_module_visibility_table
Revises: 040_add_container_layout_table
Create Date: 2026-07-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '041_add_module_visibility_table'
down_revision = '040_add_container_layout_table'
branch_labels = None
depends_on = None


def upgrade():
    """创建 module_visibility 表（自检：若已存在则跳过）

    字段说明：
    - module_key: camelCase 字符串（如 photoManage），主键
    - hidden: 是否隐藏（True=对全员隐藏）
    - updated_at: 更新时间戳
    - updated_by: 操作人 emp_id（用于审计，可为空）
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 防御性检查：表已存在则直接返回（避免重复创建报错）
    if 'module_visibility' in existing_tables:
        return

    op.create_table(
        'module_visibility',
        sa.Column('module_key', sa.String(length=50), nullable=False),
        sa.Column('hidden', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('module_key'),
    )


def downgrade():
    """回滚：删除 module_visibility 表"""
    op.drop_table('module_visibility')
