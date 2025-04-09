from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import List


class LeadSource(str, Enum):
    STRAPI = "strapi"
    BEEHIIV = "beehiiv"
    WHATSAPP = "whatsapp"

class EmploymentType(str, Enum):
    SALARIED = "salaried"
    SELF_EMPLOYED = "self_employed"
    BUSINESS = "business"
    OTHER = "other"

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    REJECTED = "rejected"

class LeadBase(BaseModel):
    full_name: Optional[str] = Field(None, example="John Doe")
    email: Optional[EmailStr] = Field(None, example="john@example.com")
    phone_number: Optional[str] = Field(None, example="1234567890")
    source: LeadSource
    loan_amount: Optional[float] = Field(None, example=50000.0)
    employment_type: Optional[EmploymentType] = None
    status: Optional[LeadStatus] = Field(default=LeadStatus.NEW)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class LeadCreate(LeadBase):
    source_id: Optional[str] = Field(None, description="Original ID from the source system")

class LeadUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    loan_amount: Optional[float] = None
    employment_type: Optional[EmploymentType] = None
    status: Optional[LeadStatus] = None
    metadata: Optional[Dict[str, Any]] = None
    last_contact: Optional[datetime] = None

class LeadInDB(LeadBase):
    id: str
    source_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_contact: Optional[datetime]
    is_active: bool

class LeadFilter(BaseModel):
    source: Optional[LeadSource] = None
    status: Optional[LeadStatus] = None
    employment_type: Optional[EmploymentType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_loan_amount: Optional[float] = None
    max_loan_amount: Optional[float] = None

class NameOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class LeadCombinedDataResponse(BaseModel):
    total_records: int = Field(..., description="Total number of lead records")
    leads: List[LeadInDB] = Field(..., description="List of leads with details")

    class Config:
        json_schema_extra = {
            "example": {
                "total_records": 100,
                "leads": [
                    {
                        "id": "56789",
                        "full_name": "Jane Smith",
                        "email": "jane@example.com",
                        "phone_number": "9876543210",
                        "source": "whatsapp",
                        "loan_amount": 75000,
                        "employment_type": "self_employed",
                        "status": "qualified",
                        "created_at": "2024-02-19T09:30:00",
                        "updated_at": "2024-02-19T10:00:00",
                        "last_contact": "2024-02-19T10:05:00",
                        "is_active": True
                    }
                ]
            }
        }
