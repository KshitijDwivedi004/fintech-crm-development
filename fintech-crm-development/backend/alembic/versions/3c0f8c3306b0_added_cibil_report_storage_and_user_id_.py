"""added cibil report storage and user id storage column

Revision ID: 3c0f8c3306b0
Revises: f60753ec3d29
Create Date: 2025-03-12 13:02:07.360831

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3c0f8c3306b0'
down_revision = 'f60753ec3d29'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('razorpay')
    op.drop_index('ix_password_history_id', table_name='password_history')
    op.drop_index('ix_password_history_user_id', table_name='password_history')
    op.drop_table('password_history')
    op.drop_table('reminders')
    op.drop_table('messages')
    op.drop_table('templates')
    op.drop_table('contacts')
    op.add_column('credit_reports', sa.Column('user_id', sa.String(length=100), nullable=True))
    op.add_column('credit_reports', sa.Column('lead_source', sa.String(length=50), server_default='Website', nullable=True))
    op.create_index(op.f('ix_credit_reports_user_id'), 'credit_reports', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_credit_reports_user_id'), table_name='credit_reports')
    op.drop_column('credit_reports', 'lead_source')
    op.drop_column('credit_reports', 'user_id')
    op.create_table('contacts',
    sa.Column('phone_number', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('email_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('phone_number', name='contacts_pkey')
    )
    op.create_table('templates',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('template_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('template_json', sa.TEXT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='templates_pkey')
    )
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
    sa.ForeignKeyConstraint(['phone_number'], ['users.phone_number'], name='fk_messages_users', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='messages_pkey')
    )
    op.create_table('reminders',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_phone', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('reminder_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('message', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
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
    # ### end Alembic commands ###
