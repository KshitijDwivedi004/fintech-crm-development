from pydantic import BaseModel
from datetime import datetime
from typing import List
from typing import Optional

class NoteCreate(BaseModel):
    notes: str

class NoteResponse(BaseModel):
    id: str
    leads_id: str
    created_by_username: str
    notes: str
    time: datetime

    class Config:
        orm_mode = True

class NoteBase(BaseModel):
    notes: str

# class NoteCreate(NoteBase):
#     pass 

class NoteUpdate(BaseModel):
    notes: Optional[str] = None

class PaginatedNotesResponse(BaseModel):
    total: int
    page: int
    size: int
    notes: List[NoteResponse]
