from pydantic import BaseModel
from datetime import datetime

class NotificationBase(BaseModel):
    type: str
    data: dict
    read_status: bool = False

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True