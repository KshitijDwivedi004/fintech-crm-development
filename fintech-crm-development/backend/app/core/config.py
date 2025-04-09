import os
from typing import Any, Dict, Optional
from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, validator, EmailStr


class Settings(BaseSettings):
    """
    Settings class for the application
    """

    DATABASE_USER: str
    DATABASE_PASSWORD: str
    STRAPI_API_URL: str
    DATABASE_HOST: str
    DATABASE_PORT: int | str
    DATABASE_NAME: str
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    STRAPI_API_TOKEN: str
    BEEHIIV_PUBLICATION_ID: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    ACCESS_TOKEN_EXPIRE_DAYS: int = 60 * 60 * 24 * 365
    SERVER_HOST: str
    PROJECT_NAME: str = "Saral"
    DATABASE_URI: PostgresDsn | None
    BEEHIIV_API_KEY: str
    CONNECTION_STRING: str
    CONTAINER_NAME: str
    PROFILEPICTURECONTAINER_NAME: str
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_GROUP_ID: str
    KAFKA_WEBSOCKET_GROUP_ID: str
    TEXTLOCAL_KEY: str
    LEAD_SYNC_INTERVAL: int = 3600  # Sync interval in seconds, default 1 hour
    TEXTLOCAL_SENDER: str
    TEXTLOCAL_URL: str
    AZURE_APPINSIGHTS_INSTRUMENTATIONKEY: str

    # Credit Report API Credentials
    CREDIT_REPORT_API_ID: str = ""
    CREDIT_REPORT_API_TOKEN: str = ""

    # Alohaa API Integration Settings
    ALOHAA_API_KEY: str = ""
    ALOHAA_DID_NUMBER: str = ""  # DID number with country code (e.g., "918069131110")
    ALOHAA_WEBHOOK_URL: str = ""  # Webhook URL for receiving Alohaa notifications

    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: str | None, values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("DATABASE_USER"),
            password=values.get("DATABASE_PASSWORD"),
            host=values.get("DATABASE_HOST"),
            port=str(values.get("DATABASE_PORT")),
            path=f"/{values.get('DATABASE_NAME') or ''}",
        )

    SMTP_TLS: bool = True
    SMTP_PORT: int | None
    SMTP_HOST: str | None
    SMTP_USER: str | None
    SMTP_PASSWORD: str | None
    EMAILS_FROM_EMAIL: str | None
    EMAILS_FROM_NAME: str | None
    SERVER_HOST: AnyHttpUrl
    CLIENT_HOST: AnyHttpUrl
    AZURE_STORAGE_PUBLIC_URL: str | None
    EMAILS_ENABLED: bool = True
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = "smtp.sendgrid.net"
    SMTP_USER: Optional[str] = "apikey"
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    EMAIL_RESET_TOKEN_EXPIRE_MINUTES: int
    EMAIL_TEMPLATES_DIR: str = "/app/email-templates"

    @validator("EMAILS_FROM_NAME")
    def get_project_name(cls, v: str | None, values: Dict[str, Any]) -> str:
        if not v:
            return values["PROJECT_NAME"]
        return v

    EMAILS_ENABLED: bool = False

    @validator("EMAILS_ENABLED", pre=True)
    def get_emails_enabled(cls, v: bool, values: Dict[str, Any]) -> bool:
        return bool(
            values.get("SMTP_HOST") and values.get("SMTP_PORT") and values.get("EMAILS_FROM_EMAIL")
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
