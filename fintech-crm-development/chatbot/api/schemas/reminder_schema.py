from pydantic import BaseModel
from datetime import datetime

class ReminderCreate(BaseModel):
    user_phone: str
    reminder_time: datetime
    message: str

class Reminder(BaseModel):
    id: int
    user_phone: str
    reminder_time: datetime
    message: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True