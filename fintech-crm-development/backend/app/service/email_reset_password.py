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


async def generate_account_reset_token(email: str) -> str:
    delta = timedelta(minutes=int(settings.EMAIL_RESET_TOKEN_EXPIRE_MINUTES))
    now = datetime.utcnow()
    expires = now + delta
    encoded_jwt = jwt.encode(
        {
            "exp": expires.timestamp(),
            "nbf": now.timestamp(),
            "sub": email,
            "type": "account_reset"
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    await insert_token(encoded_jwt, email, expires)
    return encoded_jwt

def verify_account_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if decoded_token["type"] != "account_reset":
            return None
        return decoded_token["sub"]
    except jwt.PyJWTError:
        return None
    
def send_reset_password_email(email_to: str,full_name: str,token: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Reset Password"

    # Find the Backend directory
    current_dir = Path(__file__).resolve().parent

    # Move up to `app`
    app_dir = current_dir.parent

    # Construct the email template path dynamically
    email_template_path = app_dir / "email-templates" / "reset_password.html"

    with open(email_template_path) as f:
        template_str = f.read()
    
    # Put deployed server link
    client_host = settings.CLIENT_HOST
    setup_link = f"{client_host}/reset-password/{token}"
    
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
            "username": full_name,
            "email": email_to,
            "link": setup_link,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_MINUTES // 60,
        },
        smtp=smtp_options,
    )
