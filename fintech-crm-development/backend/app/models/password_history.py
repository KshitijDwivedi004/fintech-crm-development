import sqlalchemy
from app.db.session import metadata
from sqlalchemy.sql import func
from uuid import uuid4

password_history = sqlalchemy.Table(
    "password_history",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, index=True, default=lambda: str(uuid4())),
    sqlalchemy.Column("user_id", sqlalchemy.String, sqlalchemy.ForeignKey("auditor.id", ondelete="CASCADE"), nullable=False, index=True),
    sqlalchemy.Column("password_hash", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime(timezone=True), server_default=func.now(), nullable=False),
)