from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    document_type: str = Field(..., example="image/jpeg")
    document_size: int = Field(..., example=200)
    status: str = Field(..., example="Pending")
    user_id: str
    document_type_id: int
    document_path: str
    document_name: Optional[str] = None


class DocumentId(BaseModel):
    id: int
    document_type: str = Field(..., example="image/jpeg")
    document_size: int = Field(..., example=200)
    status: str = Field(..., example="Pending")
    user_id: str
    document_type_id: int
    document_path: str


class DocumentUpdate(BaseModel):
    document_type: Optional[str] = None
    document_size: Optional[int] = None
    document_name: Optional[str] = None
    status: Optional[str] = None

class DocumentName(str, Enum):
    aadharFornt = "aadhar_front"
    aadharBack = "aadhar_back"
    pancard = "pancard"
    form16 = "form16"


class DocumentStatus(str, Enum):
    pending = "pending"
    reviewed = "reviewed"
    rejected = "rejected"


class DocumentType(str, Enum):
    jpeg = "image/jpeg"
    jpg = "image/jpg"
    png = "image/png"
    pdf = "application/pdf"
    csv = "text/csv"
    xml = "application/xml"
    xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    doc = "application/msword"
    docx = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" 
    xls = "application/vnd.ms-excel"


class DocumentBase(BaseModel):
    id: int
    document_type: str
    document_size: int
    container: str
    document_path: str
    created_on: datetime
    updated_on: datetime
    user_id: str
    document_type_id: int
    status: str
    document_name: Optional[str] = None  # Added field

class DocumentCreate(BaseModel):
    document_name: str | Optional[str] = None
    document_type: str
    document_size: int
    status: str
    user_id: str
    document_type_id: int
    document_path: str

class DocumentList(DocumentBase):
    id: int
    document_path: str
    container: str
    created_on: datetime
    updated_on: datetime
    user_id: str
    document_type_id: int
    status: str
    is_active: bool
    document_name: str|None 
    document_file_name: str|None 
    