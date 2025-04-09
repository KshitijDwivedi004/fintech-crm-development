import sqlalchemy

from app.core.config import settings
from app.db.session import metadata

consolidate_users = sqlalchemy.Table(
    "consolidate_users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("full_name", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("phone_number", sqlalchemy.String, index=True, nullable=True, unique=True),
    sqlalchemy.Column("country_code", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("email", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("org_Name", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("pan_number", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("filling_status", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("service_selected", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("tax_payer_type", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("tax_slab", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("income_slab", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("regime_opted", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("gst_number", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("category", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("status", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean),
    sqlalchemy.Column("role", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("last_communicated", sqlalchemy.String),
    sqlalchemy.Column("source", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("loan_amount", sqlalchemy.Float, nullable=True),
    sqlalchemy.Column("employment_type", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("company_name", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("monthly_income", sqlalchemy.Float, nullable=True),
    sqlalchemy.Column("loan_purpose", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("loan_tenure", sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column("raw_data", sqlalchemy.JSON, nullable=True),
    sqlalchemy.Column("cibil_score", sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column("subscription_status", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("location", sqlalchemy.String, nullable=True),

    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column(
        "updated_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
)
