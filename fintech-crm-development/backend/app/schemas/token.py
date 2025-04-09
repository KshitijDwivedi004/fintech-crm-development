from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    refresh_token: str | Optional[str]
    access_token: str
    token_type: str
    user_info: dict
class TokenRefresh(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
