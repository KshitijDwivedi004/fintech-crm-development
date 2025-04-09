import uuid
import sqlalchemy
from sqlalchemy import Boolean, Column, String, ForeignKey, DateTime, Text, JSON, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime

from app.db.session import metadata
from app.enum.telecaller_status import TelecallerStatus

# Keep existing telecallers table
telecallers = metadata.tables.get("telecallers") or sqlalchemy.Table(
    "telecallers",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column(
        "user_id",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("auditor.id"),
        unique=True,
        nullable=False,
    ),
    sqlalchemy.Column(
        "status", sqlalchemy.Enum(TelecallerStatus), default=TelecallerStatus.OFFLINE
    ),
    sqlalchemy.Column("last_active_time", sqlalchemy.DateTime, default=datetime.utcnow),
    sqlalchemy.Column("break_start_time", sqlalchemy.DateTime, nullable=True),
    sqlalchemy.Column("total_break_time", sqlalchemy.Integer, default=0),
    sqlalchemy.Column("total_active_time", sqlalchemy.Integer, default=0),
)

# Add new tables for call functionality with corrected data types
call_log = metadata.tables.get("call_log") or sqlalchemy.Table(
    "call_log",
    metadata,
    Column("id", UUID, primary_key=True, default=uuid.uuid4),
    Column("user_id", String, ForeignKey("auditor.id"), nullable=False),
    Column(
        "lead_id", String, ForeignKey("leads.id"), nullable=False
    ),  # Changed from UUID to String
    Column("caller_number", String, nullable=False),
    Column("receiver_number", String, nullable=False),
    Column("did_number", String, nullable=True),
    Column("call_id", String, nullable=True),  # External call ID from Alohaa
    Column("reference_id", String, nullable=True),  # Reference ID from Alohaa
    Column("status", String, nullable=True),  # answered, not_answered, etc.
    Column("call_duration", Integer, default=0),  # Duration in seconds
    Column("recording_url", String, nullable=True),
    Column("call_start_time", DateTime, nullable=True),
    Column("call_end_time", DateTime, nullable=True),
    Column("created_at", DateTime, default=func.now()),
    Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
)

call_note = metadata.tables.get("call_note") or sqlalchemy.Table(
    "call_note",
    metadata,
    Column("id", UUID, primary_key=True, default=uuid.uuid4),
    Column("call_log_id", UUID, ForeignKey("call_log.id"), nullable=False),
    Column("user_id", String, ForeignKey("auditor.id"), nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime, default=func.now()),
    Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
)

call_disposition = metadata.tables.get("call_disposition") or sqlalchemy.Table(
    "call_disposition",
    metadata,
    Column("id", UUID, primary_key=True, default=uuid.uuid4),
    Column("call_log_id", UUID, ForeignKey("call_log.id"), nullable=False),
    Column("user_id", String, ForeignKey("auditor.id"), nullable=False),
    Column(
        "disposition_type", String, nullable=False
    ),  # Interested, Not Interested, Follow-up, etc.
    Column("follow_up_date", DateTime, nullable=True),
    Column("additional_details", JSON, nullable=True),
    Column("created_at", DateTime, default=func.now()),
    Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
)
