import sqlalchemy

from app.core.config import settings
from app.db.session import metadata

users = sqlalchemy.Table(
    "users",
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
    sqlalchemy.Column("is_active", sqlalchemy.Boolean,default=True),
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
    sqlalchemy.Column("auditor_id", sqlalchemy.String, nullable=True), 
    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column(
        "updated_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
)


# Define the documents table
documents = sqlalchemy.Table(
    "documents",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("document_type", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("document_size", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("container", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("document_path", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("document_name", sqlalchemy.String, nullable=True),
    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column(
        "updated_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column("user_id", sqlalchemy.String, sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column(
        "document_type_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("document_types.id")
    ),
    sqlalchemy.Column("status", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean),
)

documents_type = sqlalchemy.Table(
    "document_types",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("document_name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("document_key", sqlalchemy.String(5)),
    sqlalchemy.Column("allowed_file_types", sqlalchemy.String),
    sqlalchemy.Column("max_file_count", sqlalchemy.Integer),
)
