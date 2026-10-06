"""Standalone baseline generated from the reviewed 2026-10-06 schema snapshot."""
from alembic import op
import sqlalchemy as sa

revision = "baseline_20261006"
down_revision = None
branch_labels = None
depends_on = None

class _SQLiteDeclaredType(sa.types.UserDefinedType):
    """Preserve legacy SQLite declared types not represented by SQLAlchemy types."""
    cache_ok = True
    def __init__(self, declaration):
        self.declaration = declaration
    def get_col_spec(self, **kw):
        return self.declaration

def upgrade():
    op.create_table('AnnualTarget',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('target_year', sa.Integer(), nullable=False),
        sa.Column('target_amount', _SQLiteDeclaredType('NUMERIC(15, 2)'), nullable=True, server_default=sa.text("'10000000.00'")),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('AttendanceOperation',
        sa.Column('id', _SQLiteDeclaredType('UUID'), nullable=False),
        sa.Column('emp_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('operation_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('operation_status', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('start_time', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('end_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('duration', _SQLiteDeclaredType('FLOAT'), nullable=True),
        sa.Column('reason', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('approver_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('approver_name', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('approve_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('approve_opinion', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('attachment', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('extend_info', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('CostAllocation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cost_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('cost_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=False),
        sa.Column('cost_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('apply_scope', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('effective_date', _SQLiteDeclaredType('DATE'), nullable=False),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('Customer',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', _SQLiteDeclaredType('VARCHAR(200)'), nullable=False),
        sa.Column('contact_person', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('phone', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('email', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('area', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('customer_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('source', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('search_field', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('creator_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['creator_id'], ['Employee.emp_id'])
    )

    op.create_table('DisplayFile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', _SQLiteDeclaredType('VARCHAR(36)'), nullable=False),
        sa.Column('title', _SQLiteDeclaredType('VARCHAR(200)'), nullable=False),
        sa.Column('file_type', _SQLiteDeclaredType('VARCHAR(10)'), nullable=False),
        sa.Column('file_path', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('original_filename', _SQLiteDeclaredType('VARCHAR(200)'), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('created_by', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('updated_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index('ix_display_file_created_at', 'DisplayFile', ['created_at'], unique=False)
    op.create_index('ix_display_file_uuid', 'DisplayFile', ['uuid'], unique=False)

    op.create_table('Employee',
        sa.Column('id', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('emp_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('dept', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('device_id', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('inner_ip', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('user_role', _SQLiteDeclaredType('VARCHAR(10)'), nullable=True),
        sa.Column('status', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('remarks', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('last_login_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('login_device', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('emp_id')
    )

    op.create_table('EmployeeDevice',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emp_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('device_mac', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('device_ip', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('device_type', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('device_info', _SQLiteDeclaredType('VARCHAR(200)'), nullable=True),
        sa.Column('is_primary', _SQLiteDeclaredType('BOOLEAN'), nullable=True),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('updated_at', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_mac'),
        sa.ForeignKeyConstraint(['emp_id'], ['Employee.emp_id'], ondelete='CASCADE')
    )

    op.create_table('Expense',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=False),
        sa.Column('expense_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('target_year', sa.Integer(), nullable=False),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('occurred_date', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('ExpenseAllocation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('expense_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('allocated_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=False),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['expense_id'], ['Expense.id']),
        sa.ForeignKeyConstraint(['order_id'], ['OrderList.id'])
    )

    op.create_table('ExpenseCalculationRecord',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('calculation_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('target_year', sa.Integer(), nullable=False),
        sa.Column('status', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True, server_default=sa.text("'completed'")),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('IndividualExpense',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=False),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['Order.id'])
    )
    op.create_index('ix_IndividualExpense_order_id', 'IndividualExpense', ['order_id'], unique=False)

    op.create_table('Inquiry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('area', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('inquiry_date', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('inquiry_source', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('company_name', _SQLiteDeclaredType('VARCHAR(200)'), nullable=True),
        sa.Column('contact_person', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('phone', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('email', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('packaging_product', _SQLiteDeclaredType('VARCHAR(200)'), nullable=False),
        sa.Column('machine_type', _SQLiteDeclaredType('VARCHAR(200)'), nullable=False),
        sa.Column('creator_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('search_field', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('follower_id', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['creator_id'], ['Employee.emp_id']),
        sa.ForeignKeyConstraint(['customer_id'], ['Customer.id']),
        sqlite_autoincrement=True
    )

    op.create_table('InquiryCommunication',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inquiry_id', sa.Integer(), nullable=False),
        sa.Column('subject', _SQLiteDeclaredType('VARCHAR(200)'), nullable=False),
        sa.Column('content', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('communication_date', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('creator_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('company_name', _SQLiteDeclaredType('VARCHAR(200)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['creator_id'], ['Employee.emp_id']),
        sa.ForeignKeyConstraint(['inquiry_id'], ['Inquiry.id'], ondelete='CASCADE'),
        sqlite_autoincrement=True
    )

    op.create_table('InquiryCommunicationMedia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('communication_id', sa.Integer(), nullable=False),
        sa.Column('file_name', _SQLiteDeclaredType('VARCHAR(255)'), nullable=False),
        sa.Column('file_path', _SQLiteDeclaredType('VARCHAR(500)'), nullable=False),
        sa.Column('thumb_path', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_type', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('upload_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['communication_id'], ['InquiryCommunication.id'])
    )

    op.create_table('InquiryLog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inquiry_id', sa.Integer(), nullable=True),
        sa.Column('operation_type', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('operator_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('operation_details', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('total_inquiries', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('total_communications', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('new_inquiries', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('new_communications', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('company_name', _SQLiteDeclaredType('VARCHAR(200)'), nullable=True),
        sa.Column('new_inquiries_count', sa.Integer(), nullable=True),
        sa.Column('new_communications_count', sa.Integer(), nullable=True),
        sa.Column('reset_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['inquiry_id'], ['Inquiry.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['Employee.emp_id']),
        sqlite_autoincrement=True
    )

    op.create_table('MachinesNew',
        sa.Column('model', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('original_model', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('packing_speed', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('general_power', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('power_supply', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('air_source', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('machine_weight', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('dimensions', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('package_material', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('image', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('added_count', sa.Integer(), nullable=True),
        sa.Column('original_price', _SQLiteDeclaredType('DECIMAL(10, 2)'), nullable=True),
        sa.Column('show_price', _SQLiteDeclaredType('DECIMAL(10, 2)'), nullable=True),
        sa.Column('custom_attrs', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('is_deleted', sa.Integer(), nullable=True),
        sa.Column('delete_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('model')
    )

    op.create_table('Order',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_new', sa.Integer(), nullable=True),
        sa.Column('area', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('customer_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('customer_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('order_time', _SQLiteDeclaredType('DATE'), nullable=False),
        sa.Column('ship_time', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('ship_country', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('contract_no', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('order_no', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('machine_no', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('machine_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False, server_default=sa.text("'包装机'")),
        sa.Column('machine_model', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('machine_count', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('unit', _SQLiteDeclaredType('VARCHAR(10)'), nullable=False, server_default=sa.text("'set'")),
        sa.Column('contract_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text('0')),
        sa.Column('deposit', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text('0')),
        sa.Column('balance', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text('0')),
        sa.Column('tax_rate', _SQLiteDeclaredType('NUMERIC(5, 2)'), nullable=True, server_default=sa.text('13.0')),
        sa.Column('tax_refund_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text('0')),
        sa.Column('currency_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text('0')),
        sa.Column('payment_received', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text('0')),
        sa.Column('machine_cost', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text('0')),
        sa.Column('net_profit', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text('0')),
        sa.Column('gross_profit', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text('0')),
        sa.Column('pay_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True, server_default=sa.text("'T/T'")),
        sa.Column('commission', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text('0')),
        sa.Column('latest_ship_date', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('expected_delivery', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('order_dept', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('check_requirement', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('attachment_imgs', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('attachment_videos', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('proportionate_cost', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text("'0'")),
        sa.Column('individual_cost', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True, server_default=sa.text("'0'")),
        sa.Column('search_field', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('creator_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('inquiry_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )

    op.create_table('OrderList',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_new', sa.Integer(), nullable=True),
        sa.Column('area', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('customer_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('customer_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('order_time', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('ship_time', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('ship_country', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('contract_no', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('order_no', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('machine_no', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('machine_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('machine_model', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('machine_count', sa.Integer(), nullable=True),
        sa.Column('unit', _SQLiteDeclaredType('VARCHAR(10)'), nullable=True),
        sa.Column('contract_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('deposit', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('balance', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('tax_refund_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('currency_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('payment_received', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('direct_cost', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('commission', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('allocated_cost', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('custom_income', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('custom_expense', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('gross_profit', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('net_profit', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('pay_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('latest_ship_date', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('expected_delivery', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('order_dept', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('check_requirement', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('attachment_imgs', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('attachment_videos', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('OrderRecord',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_no', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('order_remark_name', _SQLiteDeclaredType('VARCHAR(200)'), nullable=True),
        sa.Column('order_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('order_date', _SQLiteDeclaredType('DATE'), nullable=False),
        sa.Column('creator_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('currency', _SQLiteDeclaredType('VARCHAR(10)'), nullable=True, server_default=sa.text('"CNY"')),
        sa.Column('exchange_rate', _SQLiteDeclaredType('NUMERIC(10, 4)'), nullable=True, server_default=sa.text('1.0')),
        sa.Column('is_completed', _SQLiteDeclaredType('BOOLEAN'), nullable=True, server_default=sa.text('0')),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_no'),
        sa.ForeignKeyConstraint(['customer_id'], ['Customer.id'])
    )

    op.create_table('OrderRecordExpense',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_record_id', sa.Integer(), nullable=False),
        sa.Column('remark', _SQLiteDeclaredType('VARCHAR(200)'), nullable=True),
        sa.Column('amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('currency', _SQLiteDeclaredType('VARCHAR(10)'), nullable=True),
        sa.Column('exchange_rate', _SQLiteDeclaredType('NUMERIC(10, 4)'), nullable=True),
        sa.Column('screenshot', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('record_date', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('creator_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('updater_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_record_id'], ['OrderRecord.id'])
    )
    op.create_index('ix_OrderRecordExpense_order_record_id', 'OrderRecordExpense', ['order_record_id'], unique=False)

    op.create_table('OrderRecordIncome',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_record_id', sa.Integer(), nullable=False),
        sa.Column('remark', _SQLiteDeclaredType('VARCHAR(200)'), nullable=True),
        sa.Column('amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('currency', _SQLiteDeclaredType('VARCHAR(10)'), nullable=True),
        sa.Column('exchange_rate', _SQLiteDeclaredType('NUMERIC(10, 4)'), nullable=True),
        sa.Column('screenshot', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('record_date', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('creator_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('updater_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_record_id'], ['OrderRecord.id'])
    )
    op.create_index('ix_OrderRecordIncome_order_record_id', 'OrderRecordIncome', ['order_record_id'], unique=False)

    op.create_table('OrderRecordItem',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_record_id', sa.Integer(), nullable=False),
        sa.Column('type', _SQLiteDeclaredType('VARCHAR(10)'), nullable=False),
        sa.Column('remark', _SQLiteDeclaredType('VARCHAR(200)'), nullable=True),
        sa.Column('amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('currency', _SQLiteDeclaredType('VARCHAR(10)'), nullable=True),
        sa.Column('exchange_rate', _SQLiteDeclaredType('NUMERIC(10, 4)'), nullable=True),
        sa.Column('screenshots', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('record_date', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('creator_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('updater_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_record_id'], ['OrderRecord.id'])
    )
    op.create_index('ix_OrderRecordItem_order_record_id', 'OrderRecordItem', ['order_record_id'], unique=False)

    op.create_table('PunchRecord',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emp_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('punch_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('punch_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('inner_ip', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('device_id', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('last_login_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('login_device', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )

    op.create_table('QuotationTemp',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_mark', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('machine_list', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('temp_params', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('total_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('creator_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('currency_info', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('is_public', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['creator_id'], ['Employee.emp_id'])
    )

    op.create_table('RolePermission',
        sa.Column('id', _SQLiteDeclaredType('UUID'), nullable=False),
        sa.Column('role_name', _SQLiteDeclaredType('VARCHAR(10)'), nullable=False),
        sa.Column('module_name', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('can_view', _SQLiteDeclaredType('BOOLEAN'), nullable=True),
        sa.Column('can_edit', _SQLiteDeclaredType('BOOLEAN'), nullable=True),
        sa.Column('can_delete', _SQLiteDeclaredType('BOOLEAN'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('role_description', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_name', 'module_name')
    )

    op.create_table('TotpUser',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emp_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('totp_secret', _SQLiteDeclaredType('VARCHAR(16)'), nullable=False),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('emp_id')
    )

    op.create_table('_migration_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('migration_name', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('applied_at', _SQLiteDeclaredType('TIMESTAMP'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )

    op.create_table('app_version_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('date', _SQLiteDeclaredType('DATE'), nullable=False),
        sa.Column('git_hash', _SQLiteDeclaredType('VARCHAR(40)'), nullable=True),
        sa.Column('description', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version'),
        sqlite_autoincrement=True
    )
    op.create_index('ix_app_version_history_date', 'app_version_history', ['date'], unique=False)

    op.create_table('blog_comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('author', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('author_id', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('content', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('is_deleted', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['post_id'], ['blog_post.id'])
    )

    op.create_table('blog_edit_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('content', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('media_snapshot', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('edited_by', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['post_id'], ['blog_post.id'])
    )

    op.create_table('blog_favorite',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id', 'user_id'),
        sa.ForeignKeyConstraint(['post_id'], ['blog_post.id'])
    )

    op.create_table('blog_like',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id', 'user_id'),
        sa.ForeignKeyConstraint(['post_id'], ['blog_post.id'])
    )

    op.create_table('blog_media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('media_type', _SQLiteDeclaredType('VARCHAR(10)'), nullable=False),
        sa.Column('file_path', _SQLiteDeclaredType('VARCHAR(500)'), nullable=False),
        sa.Column('thumbnail_path', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('original_filename', _SQLiteDeclaredType('VARCHAR(255)'), nullable=True),
        sa.Column('file_size', _SQLiteDeclaredType('BIGINT'), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('duration', _SQLiteDeclaredType('FLOAT'), nullable=True),
        sa.Column('compress_status', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('display_path', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True, server_default=sa.text("''")),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['post_id'], ['blog_post.id'])
    )

    op.create_table('blog_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('author', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('author_id', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('is_draft', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Integer(), nullable=False),
        sa.Column('repost_from', sa.Integer(), nullable=True),
        sa.Column('edit_version', sa.Integer(), nullable=False),
        sa.Column('search_field', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('updated_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('deleted_at', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('deleted_by', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('business_operation_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('biz_id', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('operation_type', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('operator_id', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('operation_details', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['operator_id'], ['Employee.emp_id']),
        sqlite_autoincrement=True
    )
    op.create_index('idx_create_time', 'business_operation_log', ['create_time'], unique=False)
    op.create_index('idx_module', 'business_operation_log', ['module'], unique=False)
    op.create_index('idx_operation_type', 'business_operation_log', ['operation_type'], unique=False)

    op.create_table('container_layout',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('container_json', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('author_id', _SQLiteDeclaredType('VARCHAR(32)'), nullable=False),
        sa.Column('author_name', _SQLiteDeclaredType('VARCHAR(64)'), nullable=False),
        sa.Column('is_deleted', sa.Integer(), nullable=False, server_default=sa.text("'0'")),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', _SQLiteDeclaredType('DATETIME'), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_container_layout_author_id', 'container_layout', ['author_id'], unique=False)
    op.create_index('ix_container_layout_is_deleted', 'container_layout', ['is_deleted'], unique=False)

    op.create_table('cost_allocation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cost_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('cost_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=False),
        sa.Column('cost_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('apply_scope', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('effective_date', _SQLiteDeclaredType('DATE'), nullable=False),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('data_change_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('stats_type', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('stats_value', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('reset_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )
    op.create_index('idx_module_stats_type', 'data_change_stats', ['module', 'stats_type'], unique=False)

    op.create_table('machines_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('original_model', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('machine_weight', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('dimensions', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('general_power', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('power_supply', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('image', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('added_count', sa.Integer(), nullable=True),
        sa.Column('show_price', _SQLiteDeclaredType('DECIMAL(10, 2)'), nullable=True),
        sa.Column('original_price', _SQLiteDeclaredType('DECIMAL(10, 2)'), nullable=True),
        sa.Column('machine_type', sa.Integer(), nullable=True),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('brand', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('search_key', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('custom_attrs', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('is_deleted', sa.Integer(), nullable=True),
        sa.Column('delete_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_show_price_manual', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('creator', _SQLiteDeclaredType('TEXT'), nullable=True, server_default=sa.text('NULL')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('module_visibility',
        sa.Column('module_key', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('hidden', _SQLiteDeclaredType('BOOLEAN'), nullable=False),
        sa.Column('updated_at', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('module_key')
    )

    op.create_table('order_list',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_new', sa.Integer(), nullable=True),
        sa.Column('area', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('customer_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('customer_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('order_time', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('ship_time', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('ship_country', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('contract_no', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('order_no', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('machine_no', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('machine_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('machine_model', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('machine_count', sa.Integer(), nullable=True),
        sa.Column('unit', _SQLiteDeclaredType('VARCHAR(10)'), nullable=True),
        sa.Column('contract_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('deposit', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('balance', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('tax_refund_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('currency_amount', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('payment_received', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('direct_cost', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('commission', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('allocated_cost', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('custom_income', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('custom_expense', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('gross_profit', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('net_profit', _SQLiteDeclaredType('NUMERIC(12, 2)'), nullable=True),
        sa.Column('pay_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('latest_ship_date', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('expected_delivery', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('order_dept', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('check_requirement', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('attachment_imgs', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('attachment_videos', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('creator_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('order_progress',
        sa.Column('id', _SQLiteDeclaredType('VARCHAR(36)'), nullable=False),
        sa.Column('order_id', _SQLiteDeclaredType('VARCHAR(36)'), nullable=False),
        sa.Column('current_status', _SQLiteDeclaredType('VARCHAR(50)'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id'),
        sa.ForeignKeyConstraint(['order_id'], ['Order.id'])
    )

    op.create_table('order_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('remarks', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('current_status', sa.Integer(), nullable=True),
        sa.Column('current_status_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('progress_status', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('progress_percent', sa.Integer(), nullable=True),
        sa.Column('total_tasks', sa.Integer(), nullable=True),
        sa.Column('completed_tasks', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['Order.id'])
    )

    op.create_table('order_status_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_status_id', sa.Integer(), nullable=False),
        sa.Column('status', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('start_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('expected_completion_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('actual_completion_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_status_id'], ['order_status.id'])
    )

    op.create_table('photos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('tags', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('machine_id', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('search_field', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('uploader', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('upload_time', _SQLiteDeclaredType('DATETIME'), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('original_path', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('thumbnail_path', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('normal_path', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('original_width', sa.Integer(), nullable=True),
        sa.Column('original_height', sa.Integer(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('compress_status', _SQLiteDeclaredType('TEXT'), nullable=True, server_default=sa.text("'pending'")),
        sa.Column('is_deleted', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('delete_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('delete_operator', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.model'], ondelete='SET NULL'),
        sqlite_autoincrement=True
    )
    op.create_index('idx_photos_compress', 'photos', ['compress_status'], unique=False)
    op.create_index('idx_photos_deleted', 'photos', ['is_deleted'], unique=False)
    op.create_index('idx_photos_machine', 'photos', ['machine_id'], unique=False)
    op.create_index('idx_photos_search', 'photos', ['search_field'], unique=False)
    op.create_index('idx_photos_uploader', 'photos', ['uploader'], unique=False)

    op.create_table('photos_fixed',
        sa.Column('id', _SQLiteDeclaredType('INT'), nullable=True),
        sa.Column('title', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('tags', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('machine_id', _SQLiteDeclaredType('INT'), nullable=True),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('search_field', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('uploader', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('upload_time', _SQLiteDeclaredType('NUM'), nullable=True),
        sa.Column('original_path', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('thumbnail_path', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('normal_path', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('original_width', _SQLiteDeclaredType('INT'), nullable=True),
        sa.Column('original_height', _SQLiteDeclaredType('INT'), nullable=True),
        sa.Column('file_size', _SQLiteDeclaredType('INT'), nullable=True),
        sa.Column('compress_status', _SQLiteDeclaredType('TEXT'), nullable=True)
    )

    op.create_table('progress_item',
        sa.Column('id', _SQLiteDeclaredType('VARCHAR(36)'), nullable=False),
        sa.Column('progress_id', _SQLiteDeclaredType('VARCHAR(36)'), nullable=False),
        sa.Column('title', _SQLiteDeclaredType('VARCHAR(200)'), nullable=False),
        sa.Column('status', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['progress_id'], ['order_progress.id'])
    )

    op.create_table('progress_media',
        sa.Column('id', _SQLiteDeclaredType('VARCHAR(36)'), nullable=False),
        sa.Column('item_id', _SQLiteDeclaredType('VARCHAR(36)'), nullable=False),
        sa.Column('file_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('file_url', _SQLiteDeclaredType('VARCHAR(500)'), nullable=False),
        sa.Column('file_name', _SQLiteDeclaredType('VARCHAR(200)'), nullable=True),
        sa.Column('upload_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['item_id'], ['progress_item.id'])
    )

    op.create_table('progress_status_detail',
        sa.Column('id', _SQLiteDeclaredType('VARCHAR(36)'), nullable=False),
        sa.Column('progress_id', _SQLiteDeclaredType('VARCHAR(36)'), nullable=False),
        sa.Column('status', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('start_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('expected_complete_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('actual_complete_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['progress_id'], ['order_progress.id'])
    )

    op.create_table('punch_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emp_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('punch_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('punch_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('inner_ip', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('phone_mac', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('remark', _SQLiteDeclaredType('VARCHAR(200)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table('role_permission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('route_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'])
    )

    op.create_table('role_permission_simple',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('route_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'])
    )

    op.create_table('status_task',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_status_id', sa.Integer(), nullable=False),
        sa.Column('status_log_id', sa.Integer(), nullable=False),
        sa.Column('category', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(200)'), nullable=False),
        sa.Column('is_completed', _SQLiteDeclaredType('BOOLEAN'), nullable=True),
        sa.Column('photo_path', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('description', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('sort', sa.Integer(), nullable=True),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('update_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('thumb_photo_path', _SQLiteDeclaredType("TEXT COMMENT '缩略图路径，多张缩略图路径以逗号分隔'"), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_status_id'], ['order_status.id']),
        sa.ForeignKeyConstraint(['status_log_id'], ['order_status_log.id'])
    )

    op.create_table('system_configs',
        sa.Column('key', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('value', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('description', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.PrimaryKeyConstraint('key')
    )

    op.create_table('task',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('author_id', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('author_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('content', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('status', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('completion_note', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('completion_image_url', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('todo_image_url', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('expected_date', _SQLiteDeclaredType('VARCHAR(10)'), nullable=True),
        sa.Column('background_color', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('like_count', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Integer(), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('updated_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('completed_at', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('task_comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('author_id', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('author_name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('content', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('is_deleted', sa.Integer(), nullable=False),
        sa.Column('deleted_at', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('deleted_by', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'])
    )

    op.create_table('task_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_json', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('modified_by', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.Column('modified_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'])
    )

    op.create_table('task_like',
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('user_id', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('task_id', 'user_id'),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'])
    )

    op.create_table('task_media_file',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('status_task_id', sa.Integer(), nullable=False),
        sa.Column('file_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('file_format', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('file_size', _SQLiteDeclaredType('BIGINT'), nullable=True),
        sa.Column('file_path', _SQLiteDeclaredType('VARCHAR(500)'), nullable=False),
        sa.Column('thumb_path', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('file_name', _SQLiteDeclaredType('VARCHAR(200)'), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('upload_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('sort', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('is_deleted', _SQLiteDeclaredType('BOOLEAN'), nullable=True, server_default=sa.text('0')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['status_task_id'], ['status_task.id']),
        sqlite_autoincrement=True
    )

    op.create_table('task_visibility',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('visibility_type', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('visibility_value', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'])
    )

    op.create_table('todo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('author_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('author_name', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('content', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('date', _SQLiteDeclaredType('VARCHAR(10)'), nullable=False),
        sa.Column('color', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('note', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('image_url', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('status', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('completion_note', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('completion_image_url', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('completed_at', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('is_deleted', sa.Integer(), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('updated_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_todo_author_id', 'todo', ['author_id'], unique=False)
    op.create_index('ix_todo_is_deleted', 'todo', ['is_deleted'], unique=False)

    op.create_table('todo_message',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('todo_id', sa.Integer(), nullable=False),
        sa.Column('author_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('author_name', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('content', _SQLiteDeclaredType('TEXT'), nullable=False),
        sa.Column('is_deleted', sa.Integer(), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('image_url', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['todo_id'], ['todo.id'])
    )
    op.create_index('ix_todo_message_todo_id', 'todo_message', ['todo_id'], unique=False)

    op.create_table('todo_message_read',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('todo_id', sa.Integer(), nullable=False),
        sa.Column('user_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('last_read_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('todo_id', 'user_id'),
        sa.ForeignKeyConstraint(['todo_id'], ['todo.id'])
    )
    op.create_index('ix_todo_message_read_todo_id', 'todo_message_read', ['todo_id'], unique=False)
    op.create_index('ix_todo_message_read_user_id', 'todo_message_read', ['user_id'], unique=False)

    op.create_table('todo_visibility',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('todo_id', sa.Integer(), nullable=False),
        sa.Column('user_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('todo_id', 'user_id'),
        sa.ForeignKeyConstraint(['todo_id'], ['todo.id'], ondelete='CASCADE')
    )
    op.create_index('ix_todo_visibility_todo_id', 'todo_visibility', ['todo_id'], unique=False)
    op.create_index('ix_todo_visibility_user_id', 'todo_visibility', ['user_id'], unique=False)

    op.create_table('totp_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emp_id', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('totp_secret', _SQLiteDeclaredType('VARCHAR(16)'), nullable=False),
        sa.Column('create_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('emp_id')
    )

    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False),
        sa.Column('password', _SQLiteDeclaredType('VARCHAR(255)'), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'])
    )

    op.create_table('user_role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', _SQLiteDeclaredType('VARCHAR(36)'), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'])
    )

    op.create_table('videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', _SQLiteDeclaredType('VARCHAR(255)'), nullable=False, server_default=sa.text("''")),
        sa.Column('tags', _SQLiteDeclaredType('VARCHAR(500)'), nullable=False, server_default=sa.text("''")),
        sa.Column('machine_id', _SQLiteDeclaredType('TEXT'), nullable=True, server_default=sa.text("''")),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=False, server_default=sa.text("''")),
        sa.Column('search_field', _SQLiteDeclaredType('TEXT'), nullable=False, server_default=sa.text("''")),
        sa.Column('uploader', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('original_path', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('thumbnail_path', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('compressed_path', _SQLiteDeclaredType('VARCHAR(500)'), nullable=True),
        sa.Column('original_width', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('original_height', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('duration', _SQLiteDeclaredType('FLOAT'), nullable=True, server_default=sa.text('0.0')),
        sa.Column('file_size', _SQLiteDeclaredType('BIGINT'), nullable=True, server_default=sa.text('0')),
        sa.Column('compress_status', _SQLiteDeclaredType('VARCHAR(50)'), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('upload_time', _SQLiteDeclaredType('DATETIME'), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_deleted', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('delete_time', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('delete_operator', _SQLiteDeclaredType('VARCHAR(100)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )

    op.create_table('warehouse_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('map_id', sa.Integer(), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(200)'), nullable=False),
        sa.Column('x_mm', sa.Integer(), nullable=False),
        sa.Column('y_mm', sa.Integer(), nullable=False),
        sa.Column('length_mm', sa.Integer(), nullable=False),
        sa.Column('width_mm', sa.Integer(), nullable=False),
        sa.Column('height_mm', sa.Integer(), nullable=False),
        sa.Column('rotation', sa.Integer(), nullable=False),
        sa.Column('owner_group', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('color', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('status', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('stocked_date', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('stocked_by', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('shipped_date', _SQLiteDeclaredType('DATE'), nullable=True),
        sa.Column('shipped_at', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('shipped_by', _SQLiteDeclaredType('VARCHAR(20)'), nullable=True),
        sa.Column('shipped_remark', _SQLiteDeclaredType('TEXT'), nullable=True),
        sa.Column('is_deleted', sa.Integer(), nullable=False),
        sa.Column('deleted_at', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('updated_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['map_id'], ['warehouse_maps.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shipped_by'], ['Employee.emp_id']),
        sa.ForeignKeyConstraint(['stocked_by'], ['Employee.emp_id'])
    )

    op.create_table('warehouse_maps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(100)'), nullable=False),
        sa.Column('width_mm', sa.Integer(), nullable=False),
        sa.Column('length_mm', sa.Integer(), nullable=False),
        sa.Column('grid_columns', sa.Integer(), nullable=False),
        sa.Column('grid_rows', sa.Integer(), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('active', sa.Integer(), nullable=False),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('updated_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('warehouse_objects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('map_id', sa.Integer(), nullable=False),
        sa.Column('name', _SQLiteDeclaredType('VARCHAR(200)'), nullable=False),
        sa.Column('type', _SQLiteDeclaredType('VARCHAR(30)'), nullable=False),
        sa.Column('x_mm', sa.Integer(), nullable=False),
        sa.Column('y_mm', sa.Integer(), nullable=False),
        sa.Column('length_mm', sa.Integer(), nullable=False),
        sa.Column('width_mm', sa.Integer(), nullable=False),
        sa.Column('rotation', sa.Integer(), nullable=False),
        sa.Column('show_text', sa.Integer(), nullable=False),
        sa.Column('pattern', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('blocks_cargo', sa.Integer(), nullable=False),
        sa.Column('color', _SQLiteDeclaredType('VARCHAR(20)'), nullable=False),
        sa.Column('is_deleted', sa.Integer(), nullable=False),
        sa.Column('deleted_at', _SQLiteDeclaredType('DATETIME'), nullable=True),
        sa.Column('created_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.Column('updated_at', _SQLiteDeclaredType('DATETIME'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['map_id'], ['warehouse_maps.id'], ondelete='CASCADE')
    )

def downgrade():
    op.drop_table('warehouse_objects')
    op.drop_table('warehouse_maps')
    op.drop_table('warehouse_items')
    op.drop_table('videos')
    op.drop_table('user_role')
    op.drop_table('user')
    op.drop_table('totp_user')
    op.drop_table('todo_visibility')
    op.drop_table('todo_message_read')
    op.drop_table('todo_message')
    op.drop_table('todo')
    op.drop_table('task_visibility')
    op.drop_table('task_media_file')
    op.drop_table('task_like')
    op.drop_table('task_history')
    op.drop_table('task_comment')
    op.drop_table('task')
    op.drop_table('system_configs')
    op.drop_table('status_task')
    op.drop_table('role_permission_simple')
    op.drop_table('role_permission')
    op.drop_table('role')
    op.drop_table('punch_record')
    op.drop_table('progress_status_detail')
    op.drop_table('progress_media')
    op.drop_table('progress_item')
    op.drop_table('photos_fixed')
    op.drop_table('photos')
    op.drop_table('order_status_log')
    op.drop_table('order_status')
    op.drop_table('order_progress')
    op.drop_table('order_list')
    op.drop_table('module_visibility')
    op.drop_table('machines_new')
    op.drop_table('data_change_stats')
    op.drop_table('cost_allocation')
    op.drop_table('container_layout')
    op.drop_table('business_operation_log')
    op.drop_table('blog_post')
    op.drop_table('blog_media')
    op.drop_table('blog_like')
    op.drop_table('blog_favorite')
    op.drop_table('blog_edit_history')
    op.drop_table('blog_comment')
    op.drop_table('app_version_history')
    op.drop_table('_migration_history')
    op.drop_table('TotpUser')
    op.drop_table('RolePermission')
    op.drop_table('QuotationTemp')
    op.drop_table('PunchRecord')
    op.drop_table('OrderRecordItem')
    op.drop_table('OrderRecordIncome')
    op.drop_table('OrderRecordExpense')
    op.drop_table('OrderRecord')
    op.drop_table('OrderList')
    op.drop_table('Order')
    op.drop_table('MachinesNew')
    op.drop_table('InquiryLog')
    op.drop_table('InquiryCommunicationMedia')
    op.drop_table('InquiryCommunication')
    op.drop_table('Inquiry')
    op.drop_table('IndividualExpense')
    op.drop_table('ExpenseCalculationRecord')
    op.drop_table('ExpenseAllocation')
    op.drop_table('Expense')
    op.drop_table('EmployeeDevice')
    op.drop_table('Employee')
    op.drop_table('DisplayFile')
    op.drop_table('Customer')
    op.drop_table('CostAllocation')
    op.drop_table('AttendanceOperation')
    op.drop_table('AnnualTarget')
