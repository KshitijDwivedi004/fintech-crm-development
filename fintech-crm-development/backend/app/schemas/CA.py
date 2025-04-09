from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class CABase(BaseModel):
    full_name: str | None = Field(..., example="Sumit Kashyap")
    email: EmailStr | None = Field(..., example="user@gmail.com")
    phone_number: str | None = Field(..., example="8640014872")


class CACreate(CABase):
    password: str | None = Field(..., example="Admin@123")


class CAUpdate(CACreate):
    is_active: bool | None = Field(..., example=True)


class CAId(CABase):
    id: str | None


class CAInDBBase(CABase):
    id: str | None
    profilePicture: dict | None


class ProfilePictureCreate(BaseModel):
    filename: str = Field(..., example="Aadhar")
    filetype: str = Field(..., example="image/jpeg")
    filesize: int = Field(..., example=200)
    ca_id: str
    image_url: str
    ca_id: str
