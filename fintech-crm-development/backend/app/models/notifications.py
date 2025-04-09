import sqlalchemy
from app.db.session import metadata

notifications = sqlalchemy.Table(
    "notifications",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("type", sqlalchemy.String, index=True),
    sqlalchemy.Column("formatted_data", sqlalchemy.JSON),
    sqlalchemy.Column("original_data", sqlalchemy.JSON),
    sqlalchemy.Column("read_status", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column(
        "created_at", sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.func.now()
    ),
)
