from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class AuditorBase(BaseModel):
    full_name: str | None = Field(..., example="Sumit Kashyap")
    email: EmailStr | None = Field(..., example="user@gmail.com")
    phone_number: str | None = Field(..., example="8640014872")
    expertise: str | None = Field(..., example="Tax Auditor")


"""
    currently I will set created_by option in auditor pydantic schema to none as we haven't implemented the
    admin functionality yet, after implementing the admin functionality we can secure this 
    endpoint and set created_by option to the current user.  
"""


class AuditorCreate(BaseModel):
    full_name: str = Field(..., example="John Doe")
    email: EmailStr = Field(..., example="johndoe@example.com")
    phone_number: str | None = Field(None, example="9876543210")
    expertise: str | None = Field(None, example="Tax Auditor")
    experience: int | None = None
    qualification: str | None = None
    created_by: str | None = None
    password: str | None = None
    task_read: bool = True
    task_write: bool = True
    task_create: bool = True
    task_delete: bool = True
    task_import: bool = True
    task_export: bool = True
    chat_read: bool = True
    chat_write: bool = True
    chat_create: bool = True
    chat_delete: bool = True
    chat_import: bool = True
    chat_export: bool = True


class AuditorCreateId(AuditorCreate):
    created_by: str | None


class AuditorUpdate(AuditorCreate):
    is_active: bool | None = Field(..., example=True)


class AuditorId(AuditorBase):
    id: str | None
    experience: int | None
    qualification: str | None
    task_read: bool | None = Field(..., example=True)
    task_write: bool | None = Field(..., example=True)
    task_create: bool | None = Field(..., example=True)
    task_delete: bool | None = Field(..., example=True)
    task_import: bool | None = Field(..., example=True)
    task_export: bool | None = Field(..., example=True)
    chat_read: bool | None = Field(..., example=True)
    chat_write: bool | None = Field(..., example=True)
    chat_create: bool | None = Field(..., example=True)
    chat_delete: bool | None = Field(..., example=True)
    chat_import: bool | None = Field(..., example=True)
    chat_export: bool | None = Field(..., example=True)


class AuditorInDBBase(AuditorId):
    profilePicture: dict | None


class ProfilePictureCreate(BaseModel):
    filename: str = Field(..., example="Aadhar")
    filetype: str = Field(..., example="image/jpeg")
    filesize: int = Field(..., example=200)
    auditor_id: str
    image_url: str | None
    auditor_id: str


class AuditorTaskBase(BaseModel):
    task_type: str | None = Field(..., example="Tax Compliance")
    priority: str | None = Field(..., example="medium")
    task_name_1: str | None = Field(..., example="String")
    task_name_2: str | None = Field(..., example="String")
    task_name_3: str | None = Field(..., example="String")
    status: str | None = Field(..., example="Pending")


class AuditorTaskCreate(AuditorTaskBase):
    created_by: str
    created_for: str


class AuditorTaskDateTime(AuditorTaskCreate):
    id: str
    created_on: datetime
    updated_on: datetime
