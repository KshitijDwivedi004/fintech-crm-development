import re
from datetime import datetime, timedelta
from typing import Any, Union

import jwt
from fastapi import HTTPException
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


async def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """
    Create access token for the given subject"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def create_refresh_token(subject: Union[str, Any], remember_me: bool = False) -> str:
    """Generate Refresh Token (longer if 'Remember Me' is checked)"""
    expire_time = timedelta(days=30) if remember_me else timedelta(days=7)  # 30 days if Remember Me,
    expire = datetime.utcnow() + expire_time
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=ALGORITHM)

async def decode_token(token: str, secret: str):
    """Decode JWT Token"""
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def password_regex(password: str):
    """
    Validate password with the given regex
    """
    if not re.match(r"^(?=.*[\d])(?=.*[A-Z])(?=.*[a-z])(?=.*[@#$])[\w\d@#$]{6,12}$", password):
        raise HTTPException(status_code=400, detail="Please Provide strong Password!")
    return password


def validate_phone_number(phone_number):
    """
    Validate phone number with the given regex
    """
    if not re.match(r"^\d{10}$", phone_number):
        raise HTTPException(status_code=400, detail="Please Provide valid Phonenumber")
    return phone_number
