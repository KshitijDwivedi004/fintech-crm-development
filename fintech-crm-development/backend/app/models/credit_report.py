import sqlalchemy as sa
from app.db.session import metadata

credit_reports = sa.Table(
    "credit_reports",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    # User identification
    sa.Column(
        "user_id", sa.String(100), index=True, nullable=True
    ),  # New field for user association
    sa.Column("pan_number", sa.String, index=True, nullable=False),
    sa.Column("phone_number", sa.String, index=True, nullable=False),
    sa.Column("first_name", sa.String, nullable=False),
    sa.Column("last_name", sa.String, nullable=False),
    sa.Column("dob", sa.String, nullable=False),  # Store as DD-MM-YYYY
    # Report metadata
    sa.Column("report_id", sa.String, index=True, unique=True),  # Equifax ReportOrderNO
    sa.Column(
        "lead_source", sa.String(50), nullable=True, server_default="Website"
    ),  # New field for tracking source
    sa.Column("created_at", sa.DateTime(timezone=True), default=sa.func.now()),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now()
    ),
    # Credit score
    sa.Column("credit_score", sa.Integer, nullable=True),
    sa.Column("credit_score_version", sa.String, nullable=True),
    # Full report data as JSON
    sa.Column("raw_data", sa.JSON, nullable=False),
    # Processed data for easier querying
    sa.Column("total_accounts", sa.Integer, nullable=True),
    sa.Column("active_accounts", sa.Integer, nullable=True),
    sa.Column("closed_accounts", sa.Integer, nullable=True),
    sa.Column("delinquent_accounts", sa.Integer, nullable=True),
    # Flags
    sa.Column("is_valid", sa.Boolean, default=True),
)
