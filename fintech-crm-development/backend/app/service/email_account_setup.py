import jwt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import emails
from emails.template import JinjaTemplate
from app.core.config import settings
import os
from pathlib import Path
from app.repository.token_repository import insert_token


def send_account_setup_email(email_to: str, full_name: str, token: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Account Setup"

    current_dir = Path(__file__).resolve().parent

    # Move up to `app`
    app_dir = current_dir.parent

    # Construct the email template path dynamically
    email_template_path = app_dir / "email-templates" / "account_setup.html"

    with open(email_template_path) as f:
        template_str = f.read()
    
    # Put deployed server link
    client_host = settings.CLIENT_HOST
    setup_link = f"{client_host}/create-account/{token}"
    
    message = emails.Message(
        subject=subject,
        html=JinjaTemplate(template_str),
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    
    smtp_options = {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "tls": settings.SMTP_TLS,
        "user": settings.SMTP_USER,
        "password": settings.SMTP_PASSWORD,
    }
    email_sent=message.send(
        to=email_to,
        render={
            "project_name": settings.PROJECT_NAME,
            "full_name": full_name,
            "setup_link": setup_link,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_MINUTES // 60,
        },
        smtp=smtp_options,
    )

async def generate_account_setup_token(email: str) -> str:
    delta = timedelta(minutes=int(settings.EMAIL_RESET_TOKEN_EXPIRE_MINUTES))  # Convert to int
    now = datetime.utcnow()
    expires = now + delta
    encoded_jwt = jwt.encode(
        {
            "exp": expires.timestamp(),
            "nbf": now.timestamp(),
            "sub": email,
            "type": "account_setup"
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    await insert_token(encoded_jwt, email, expires)
    return encoded_jwt

def verify_account_setup_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if decoded_token["type"] != "account_setup":
            return None
        return decoded_token["sub"]
    except jwt.PyJWTError:
        return None
    
