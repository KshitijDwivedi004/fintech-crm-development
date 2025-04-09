import sqlalchemy

from app.core.config import settings
from app.db.session import metadata
from app.models.user import users

messages = sqlalchemy.Table(
"messages",
metadata,
sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
sqlalchemy.Column("phone_number", sqlalchemy.String, sqlalchemy.ForeignKey("users.phone_number", ondelete="CASCADE")),
sqlalchemy.Column("message_text", sqlalchemy.String),
sqlalchemy.Column("message_id", sqlalchemy.String),
sqlalchemy.Column("message_type", sqlalchemy.String),
sqlalchemy.Column("message_sender", sqlalchemy.String),
sqlalchemy.Column("timestamp", sqlalchemy.String),
sqlalchemy.Column("media_id", sqlalchemy.String, nullable=True),
sqlalchemy.Column("latitude", sqlalchemy.Float, nullable=True),
sqlalchemy.Column("longitude", sqlalchemy.Float, nullable=True),
sqlalchemy.Column("read", sqlalchemy.Boolean, default=False),
)