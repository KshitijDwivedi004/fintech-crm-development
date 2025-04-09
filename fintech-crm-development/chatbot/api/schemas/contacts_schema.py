from pydantic import BaseModel
from typing import Optional

class ContactBase(BaseModel):
    phone_number: str
    name: Optional[str] = None
    email_id: str

class ContactCreate(ContactBase):
    pass

class ContactInDB(ContactBase):
    pass
