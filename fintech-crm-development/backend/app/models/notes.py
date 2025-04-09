import sqlalchemy
from app.db.session import metadata

notes = sqlalchemy.Table(
    "notes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("created_by_username", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("notes", sqlalchemy.String, nullable=False),
    sqlalchemy.Column(
        "time", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column("leads_id", sqlalchemy.String, sqlalchemy.ForeignKey("users.id")),
)
