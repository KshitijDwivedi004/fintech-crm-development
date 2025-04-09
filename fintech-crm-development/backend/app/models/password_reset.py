import sqlalchemy as sa
from app.db.session import metadata

otp_table = sa.Table(
    "otp_storage",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("email", sa.String, nullable=False),
    sa.Column("otp", sa.String, nullable=False),
    sa.Column("created_on", sa.DateTime(timezone=True), default=sa.func.now()),    
    sa.Column("expires_at", sa.DateTime, nullable=False),
    sa.Column("is_used", sa.Boolean, default=False)
)
