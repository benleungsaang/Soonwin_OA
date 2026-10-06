"""Remove unique constraint from order_mark in QuotationTemp table

Revision ID: 037_20260308_100000
Revises: 036_20260305_103000_add_inquiry_communication_media_table
Create Date: 2026-03-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '037_20260308_100000_remove_quotation_temp_order_mark_unique_constraint'
down_revision = '036_20260305_103000_add_inquiry_communication_media_table'
branch_labels = None
depends_on = None


def upgrade():
    # 对于SQLite，删除唯一性约束需要使用 ALTER TABLE ... DROP CONSTRAINT
    # 但是SQLite不直接支持删除约束，所以我们将使用批量操作
    with op.batch_alter_table('QuotationTemp') as batch_op:
        # 获取当前所有唯一约束并删除包含order_mark的约束
        try:
            # 尝试删除可能的唯一性约束名称
            constraint_names = [
                'uq_quotationtemp_order_mark',
                'QuotationTemp_order_mark_key',
                'sqlite_autoindex_QuotationTemp_1'  # SQLite的自动索引
            ]
            
            for constraint_name in constraint_names:
                try:
                    batch_op.drop_constraint(constraint_name, type_='unique')
                    print(f"成功删除约束: {constraint_name}")
                    break
                except Exception as e:
                    print(f"删除约束 {constraint_name} 失败: {str(e)}")
                    continue
        except Exception as e:
            print(f"处理约束时出错: {str(e)}")


def downgrade():
    # 重新添加唯一性约束
    with op.batch_alter_table('QuotationTemp') as batch_op:
        try:
            batch_op.create_unique_constraint('uq_quotationtemp_order_mark', ['order_mark'])
            print("成功添加唯一性约束")
        except Exception as e:
            print(f"添加唯一性约束失败: {str(e)}")