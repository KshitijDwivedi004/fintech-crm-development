"""Add call functionality tables

Revision ID: fd90823b76de
Revises: 3c0f8c3306b0
Create Date: 2025-03-21 12:15:27.141911

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fd90823b76de'
down_revision = '3c0f8c3306b0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('messages')
    op.drop_index('ix_call_logs_call_status', table_name='call_logs')
    op.drop_index('ix_call_logs_call_type', table_name='call_logs')
    op.drop_index('ix_call_logs_contact_name', table_name='call_logs')
    op.drop_index('ix_call_logs_date_time', table_name='call_logs')
    op.drop_index('ix_call_logs_id', table_name='call_logs')
    op.drop_index('ix_call_logs_phone_number', table_name='call_logs')
    op.drop_index('ix_call_logs_user_id', table_name='call_logs')
    op.drop_table('call_logs')
    op.drop_index('ix_call_dispositions_disposition_type', table_name='call_dispositions')
    op.drop_index('ix_call_dispositions_id', table_name='call_dispositions')
    op.drop_index('ix_call_dispositions_user_id', table_name='call_dispositions')
    op.drop_table('call_dispositions')
    op.drop_table('razorpay')
    op.drop_table('templates')
    op.drop_index('ix_call_notes_id', table_name='call_notes')
    op.drop_index('ix_call_notes_user_id', table_name='call_notes')
    op.drop_table('call_notes')
    op.drop_index('ix_password_history_id', table_name='password_history')
    op.drop_index('ix_password_history_user_id', table_name='password_history')
    op.drop_table('password_history')
    op.drop_table('reminders')
    op.drop_index('ix_consolidate_users_id', table_name='consolidate_users')
    op.drop_index('ix_consolidate_users_phone_number', table_name='consolidate_users')
    op.drop_table('consolidate_users')
    op.drop_table('contacts')
    op.drop_index('ix_notifications_id', table_name='notifications')
    op.drop_index('ix_notifications_type', table_name='notifications')
    op.drop_table('notifications')
    op.drop_column('users', 'auditor_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('auditor_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.create_table('notifications',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('type', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('formatted_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('original_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('read_status', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='notifications_pkey')
    )
    op.create_index('ix_notifications_type', 'notifications', ['type'], unique=False)
    op.create_index('ix_notifications_id', 'notifications', ['id'], unique=False)
    op.create_table('contacts',
    sa.Column('phone_number', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('email_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('phone_number', name='contacts_pkey')
    )
    op.create_table('consolidate_users',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('full_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('phone_number', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('country_code', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('org_Name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('pan_number', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('filling_status', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('service_selected', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('tax_payer_type', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('tax_slab', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('income_slab', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('regime_opted', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('gst_number', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('category', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('role', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('last_communicated', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('source', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('loan_amount', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('employment_type', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('company_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('monthly_income', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('loan_purpose', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('loan_tenure', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('cibil_score', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('subscription_status', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('location', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_on', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_on', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='consolidate_users_pkey')
    )
    op.create_index('ix_consolidate_users_phone_number', 'consolidate_users', ['phone_number'], unique=False)
    op.create_index('ix_consolidate_users_id', 'consolidate_users', ['id'], unique=False)
    op.create_table('reminders',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_phone', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('reminder_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('message', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_phone'], ['users.phone_number'], name='reminders_user_phone_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='reminders_pkey')
    )
    op.create_table('password_history',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('password_hash', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['auditor.id'], name='password_history_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='password_history_pkey')
    )
    op.create_index('ix_password_history_user_id', 'password_history', ['user_id'], unique=False)
    op.create_index('ix_password_history_id', 'password_history', ['id'], unique=False)
    op.create_table('call_notes',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('call_log_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['call_log_id'], ['call_logs.id'], name='call_notes_call_log_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='call_notes_pkey')
    )
    op.create_index('ix_call_notes_user_id', 'call_notes', ['user_id'], unique=False)
    op.create_index('ix_call_notes_id', 'call_notes', ['id'], unique=False)
    op.create_table('templates',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('category', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('wa_name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=100), server_default=sa.text("'DRAFT'::character varying"), autoincrement=False, nullable=False),
    sa.Column('structure', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='templates_pkey')
    )
    op.create_table('razorpay',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('event_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('user_phone', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('user_email', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('order_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('payment_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('amount', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('currency', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('method', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('error_code', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('error_source', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('error_description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='razorpay_pkey')
    )
    op.create_table('call_dispositions',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('call_log_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('disposition_type', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('follow_up_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('additional_details', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['call_log_id'], ['call_logs.id'], name='call_dispositions_call_log_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='call_dispositions_pkey')
    )
    op.create_index('ix_call_dispositions_user_id', 'call_dispositions', ['user_id'], unique=False)
    op.create_index('ix_call_dispositions_id', 'call_dispositions', ['id'], unique=False)
    op.create_index('ix_call_dispositions_disposition_type', 'call_dispositions', ['disposition_type'], unique=False)
    op.create_table('call_logs',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('contact_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('phone_number', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('call_type', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('duration', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('date_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('call_status', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='call_logs_pkey')
    )
    op.create_index('ix_call_logs_user_id', 'call_logs', ['user_id'], unique=False)
    op.create_index('ix_call_logs_phone_number', 'call_logs', ['phone_number'], unique=False)
    op.create_index('ix_call_logs_id', 'call_logs', ['id'], unique=False)
    op.create_index('ix_call_logs_date_time', 'call_logs', ['date_time'], unique=False)
    op.create_index('ix_call_logs_contact_name', 'call_logs', ['contact_name'], unique=False)
    op.create_index('ix_call_logs_call_type', 'call_logs', ['call_type'], unique=False)
    op.create_index('ix_call_logs_call_status', 'call_logs', ['call_status'], unique=False)
    op.create_table('messages',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('phone_number', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('message_text', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('message_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('message_type', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('message_sender', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('timestamp', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('media_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('latitude', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('longitude', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('read', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('variables', postgresql.ARRAY(sa.TEXT()), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['phone_number'], ['users.phone_number'], name='messages_phone_number_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='messages_pkey')
    )
    # ### end Alembic commands ###
