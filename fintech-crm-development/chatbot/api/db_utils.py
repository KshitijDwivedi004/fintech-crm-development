import os
from functools import lru_cache

import databases
import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import ARRAY


from api.settings import settings

load_dotenv()


# @lru_cache()
# def setting():
#     return Settings()


database = databases.Database(settings.DATABASE_URL)

metadata = sqlalchemy.MetaData()
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
    sqlalchemy.Column("variables", ARRAY(sqlalchemy.String), nullable=True),
)

templates = sqlalchemy.Table(
    "templates",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column("wa_name", sqlalchemy.String(100), nullable=False),
    sqlalchemy.Column("category", sqlalchemy.String(100), nullable=False),
    sqlalchemy.Column("status", sqlalchemy.String(50), nullable=False, server_default="DRAFT"),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now()),
    sqlalchemy.Column("structure", JSONB, nullable=True)
)
razorpay = sqlalchemy.Table(
    "razorpay",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("event_id", sqlalchemy.String),
    sqlalchemy.Column("user_phone", sqlalchemy.String),
    sqlalchemy.Column("user_email", sqlalchemy.String),
    sqlalchemy.Column("order_id", sqlalchemy.String),
    sqlalchemy.Column("payment_id", sqlalchemy.String),
    sqlalchemy.Column("amount", sqlalchemy.String),
    sqlalchemy.Column("currency", sqlalchemy.String),
    sqlalchemy.Column("status", sqlalchemy.String),
    sqlalchemy.Column("method", sqlalchemy.String),
    sqlalchemy.Column("error_code", sqlalchemy.String),
    sqlalchemy.Column("error_source", sqlalchemy.String),
    sqlalchemy.Column("error_description", sqlalchemy.String),
    sqlalchemy.Column("created_at", sqlalchemy.String),
)


contacts = sqlalchemy.Table(
    "contacts",
    metadata,
    sqlalchemy.Column("phone_number", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("email_id", sqlalchemy.String),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=func.now()),  
)

reminders = sqlalchemy.Table(
    "reminders",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("user_phone", sqlalchemy.String, sqlalchemy.ForeignKey("users.phone_number", ondelete="CASCADE")),
    sqlalchemy.Column("reminder_time", sqlalchemy.DateTime),
    sqlalchemy.Column("message", sqlalchemy.String),
    sqlalchemy.Column("status", sqlalchemy.String, default="pending"),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=func.now()),
)

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, index=True),
    sqlalchemy.Column("full_name", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("phone_number", sqlalchemy.String, index=True, nullable=False, unique=True),
    sqlalchemy.Column("country_code", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("email", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("org_Name", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("pan_number", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("filling_status", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("service_selected", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("tax_payer_type", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("tax_slab", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("income_slab", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("regime_opted", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("gst_number", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("category", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("status", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean),
    sqlalchemy.Column("role", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("last_communicated", sqlalchemy.String),
    sqlalchemy.Column("source", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("loan_amount", sqlalchemy.Float, nullable=True),
    sqlalchemy.Column("employment_type", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("company_name", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("monthly_income", sqlalchemy.Float, nullable=True),
    sqlalchemy.Column("loan_purpose", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("loan_tenure", sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column("raw_data", sqlalchemy.JSON, nullable=True),
    sqlalchemy.Column("cibil_score", sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column("subscription_status", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("location", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("auditor_id", sqlalchemy.String, nullable=True), 


    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column(
        "updated_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
)

# Define the documents table
documents = sqlalchemy.Table(
    "documents",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("document_type", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("document_size", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("container", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("document_path", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("document_name", sqlalchemy.String, nullable=True),
    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column(
        "updated_on", sqlalchemy.DateTime(timezone=True), default=sqlalchemy.func.now()
    ),
    sqlalchemy.Column("user_id", sqlalchemy.String, sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column(
        "document_type_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("document_types.id")
    ),
    sqlalchemy.Column("status", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean),
)

documents_type = sqlalchemy.Table(
    "document_types",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("document_name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("document_key", sqlalchemy.String(5)),
    sqlalchemy.Column("allowed_file_types", sqlalchemy.String),
    sqlalchemy.Column("max_file_count", sqlalchemy.Integer),
)

engine = sqlalchemy.create_engine(settings.DATABASE_URL)
metadata.create_all(engine)
