import sqlalchemy
from sqlalchemy.dialects.postgresql import JSONB
from app.db.session import metadata

tokens = sqlalchemy.Table(
    "tokens",
    metadata,
    sqlalchemy.Column("token", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("user_email", sqlalchemy.String, index=True),
    sqlalchemy.Column("used", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("expires_at", sqlalchemy.DateTime(timezone=True)),    
)