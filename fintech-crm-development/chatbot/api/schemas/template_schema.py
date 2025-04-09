from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class TemplateBase(BaseModel):
    name: str
    wa_name: str
    category: str

class WhatsAppButton(BaseModel):
    type: str  # "URL" | "PHONE_NUMBER" | "QUICK_REPLY"
    text: str
    url: Optional[str] = None
    phone_number: Optional[str] = None

class WhatsAppTemplateComponent(BaseModel):
    type: str  # "HEADER" | "BODY" | "FOOTER" | "BUTTONS"
    format: Optional[str] = None  # "TEXT" | "IMAGE" | "DOCUMENT"
    text: Optional[str] = None
    example: Optional[dict] = None  # Optional example data
    buttons: Optional[List[WhatsAppButton]] = None

class WhatsappTemplate(BaseModel):
    name: str
    language: str
    category: str
    components: List[WhatsAppTemplateComponent]
class Template(TemplateBase):
    id: int
    created_at: datetime
    

    class Config:
        orm_mode = True