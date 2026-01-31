"""add search_field to inquiry

Revision ID: 013_add_search_field_to_inquiry
Revises: 012_add_video_compression_fields
Create Date: 2026-01-30 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '013_add_search_field_to_inquiry'
down_revision = '012_add_video_compression_fields'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 search_field 字段
    with op.batch_alter_table('Inquiry', schema=None) as batch_op:
        batch_op.add_column(sa.Column('search_field', sa.Text, comment="冗余搜索字段，包含地区、来源、公司名、联系人、电话、邮箱、包装产品、需求类型"))
    
    # 更新现有数据，填充 search_field 字段
    connection = op.get_bind()
    
    # 查询所有询盘记录
    result = connection.execute(sa.text("SELECT id, area, inquiry_source, company_name, contact_person, phone, email, packaging_product, machine_type FROM Inquiry"))
    
    for row in result:
        # 组合所有相关字段到 search_field
        search_values = [
            row['area'] or '',
            row['inquiry_source'] or '',
            row['company_name'] or '',
            row['contact_person'] or '',
            row['phone'] or '',
            row['email'] or '',
            row['packaging_product'] or '',
            row['machine_type'] or ''
        ]
        
        # 过滤空值并连接成搜索字段
        search_field_value = ' '.join(filter(None, search_values))
        
        # 更新该条记录的 search_field 字段
        connection.execute(
            sa.text("UPDATE Inquiry SET search_field = :search_field WHERE id = :id"),
            {"search_field": search_field_value, "id": row['id']}
        )


def downgrade():
    # 删除 search_field 字段
    with op.batch_alter_table('Inquiry', schema=None) as batch_op:
        batch_op.drop_column('search_field')