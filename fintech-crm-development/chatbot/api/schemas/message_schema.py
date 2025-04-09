from pydantic import BaseModel
from typing import Optional, List

class MessageBase(BaseModel):
    phone_number: str
    message_text: str
    message_id: str
    message_type: str
    message_sender: str
    timestamp: str
    media_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    read: bool = False
    variables: Optional[List[str]] = None

class MessageReadUpdate(BaseModel):
    message_id: str
    read: bool

class MessageRequest(BaseModel):
    phone_number: str
    message: str
class SendTemplateRequest(BaseModel):
    phone_number: str
    template_name: str
    variables: List[str]