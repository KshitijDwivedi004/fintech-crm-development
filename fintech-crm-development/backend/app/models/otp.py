import sqlalchemy

from app.core.config import settings
from app.db.session import metadata

otps = sqlalchemy.Table(
    "otps",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("phone_number", sqlalchemy.String, nullable=False, index=True),
    sqlalchemy.Column("otp_code", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("status", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column(
        "updated_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column("otp_failed_count", sqlalchemy.Integer),
)

otp_blocks = sqlalchemy.Table(
    "otp_blocks",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("phone_number", sqlalchemy.String, nullable=False, index=True),
    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
)
