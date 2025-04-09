import sqlalchemy
from app.db.session import metadata
from datetime import datetime

failed_login_attempts = sqlalchemy.Table(
    "failed_login_attempts",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("user_id", sqlalchemy.String, sqlalchemy.ForeignKey("auditor.id")),
    sqlalchemy.Column("username", sqlalchemy.String, index=True),
    sqlalchemy.Column("attempt_time", sqlalchemy.DateTime, default=datetime.utcnow),
)