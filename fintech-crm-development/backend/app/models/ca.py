import sqlalchemy

from app.core.config import settings
from app.db.session import metadata

ca = sqlalchemy.Table(
    "ca",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("full_name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String, index=True, nullable=False, unique=True),
    sqlalchemy.Column("phone_number", sqlalchemy.String, index=True, nullable=False, unique=True),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean),
    sqlalchemy.Column("role", sqlalchemy.String, nullable=False),
    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
)

ca_profile = sqlalchemy.Table(
    "ca_profile_picture",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("filename", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("filetype", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("filesize", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("container", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("filepath", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("image_url", sqlalchemy.String, nullable=True),
    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column(
        "updated_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column("ca_id", sqlalchemy.String, sqlalchemy.ForeignKey("ca.id")),
)
