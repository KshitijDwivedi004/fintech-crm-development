import sqlalchemy

from app.core.config import settings
from app.db.session import metadata

auditor = sqlalchemy.Table(
    "auditor",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("full_name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String, index=True, nullable=False, unique=True),
    sqlalchemy.Column("phone_number", sqlalchemy.String, index=True, nullable=False, unique=True),
    sqlalchemy.Column("expertise", sqlalchemy.String, index=True, nullable=False),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean),
    sqlalchemy.Column("role", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("experience", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("qualification", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("task_read", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("task_write", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("task_create", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("task_delete", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("task_import", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("task_export", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("chat_read", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("chat_write", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("chat_create", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("chat_delete", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("chat_import", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("chat_export", sqlalchemy.Boolean, nullable=False),
    
    
    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column("created_by", sqlalchemy.String, sqlalchemy.ForeignKey("ca.id")),
)

auditor_profile = sqlalchemy.Table(
    "auditor_profile_picture",
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
    sqlalchemy.Column("auditor_id", sqlalchemy.String, sqlalchemy.ForeignKey("auditor.id")),
)

auditor_task = sqlalchemy.Table(
    "auditor_task",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("task_type", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("priority", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("task_name_1", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("task_name_2", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("task_name_3", sqlalchemy.String, nullable=True),
    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column(
        "updated_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column("created_by", sqlalchemy.String, sqlalchemy.ForeignKey("ca.id")),
    sqlalchemy.Column("created_for", sqlalchemy.String, sqlalchemy.ForeignKey("auditor.id")),
    sqlalchemy.Column("status", sqlalchemy.String),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean),
)
