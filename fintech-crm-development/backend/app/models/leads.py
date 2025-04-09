import sqlalchemy
from sqlalchemy.dialects.postgresql import JSONB
from app.db.session import metadata

leads = sqlalchemy.Table(
    "leads",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("full_name", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("email", sqlalchemy.String, index=True, nullable=True),
    sqlalchemy.Column("phone_number", sqlalchemy.String, index=True, nullable=True),
    sqlalchemy.Column("source", sqlalchemy.String, nullable=False),  # strapi, beehiiv, whatsapp
    sqlalchemy.Column("source_id", sqlalchemy.String, nullable=True),  # Original ID from source
    sqlalchemy.Column("loan_amount", sqlalchemy.Float, nullable=True),
    sqlalchemy.Column("employment_type", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("status", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("metadata", JSONB, nullable=True),  # Store source-specific data
    sqlalchemy.Column("created_at", sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.func.now()),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime(timezone=True), onupdate=sqlalchemy.func.now()),
    sqlalchemy.Column("last_contact", sqlalchemy.DateTime(timezone=True), nullable=True),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean, default=True)
)