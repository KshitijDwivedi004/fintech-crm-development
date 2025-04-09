from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, root_validator


class UserBase(BaseModel):
    full_name: Optional[str] = Field(None, example="Sumit Kashyap")
    country_code: Optional[str] = Field(None, example="91")
    email: Optional[EmailStr] = None
    phone_number: str = Field(..., example="8640014872")
    org_Name: Optional[str] = Field(None, example="Techdome")
    pan_number: Optional[str] = Field(None, example="KPMYK8956H")
    filling_status: Optional[str] = Field(None, example="Individual")
    service_selected: Optional[str] = Field(None, example="Live Tax Consultation")
    tax_payer_type: Optional[str] = Field(None, example="Salaried")
    tax_slab: Optional[str] = Field(None, example="2.5 to 5 Lakh")
    income_slab: Optional[str] = Field(None, example="2,50,001 - 5,00,000")
    regime_opted: Optional[str] = Field(None, example="Old")
    gst_number: Optional[str] = Field(None, example="07AABCT1234C1ZV")
    category: Optional[str] = Field(None, example="Consultation Initiated")
    status: Optional[str] = Field(None, example="Consultation Initiated")
    source: Optional[str] = None
    loan_amount: Optional[float] = None
    employment_type: Optional[str] = None
    document_name: Optional[str] = None  # Added this line
    company_name: Optional[str] = None
    monthly_income: Optional[float] = None
    loan_purpose: Optional[str] = None
    loan_tenure: Optional[int] = None
    raw_data: Optional[dict] = None
    cibil_score: Optional[int] = None
    subscription_status: Optional[str] = None
    location: Optional[str] = Field(None, example="New Delhi")

  

class UserCreate(BaseModel):
    full_name: Optional[str] = Field(None, example="Harsh")
    email: Optional[EmailStr] = None
    phone_number: str = Field(..., example="1234567890")


class UserCreateKafka(BaseModel):
    phone_number: str
    country_code: str
    status: str
    source: str


class UserUpdate(UserCreate):
    is_active: bool = Field(..., example=True)


class UserId(UserBase):
    id: str
    last_communicated: Optional[str] = None
    documents_count: Optional[int] = None
    created_on: datetime


class UserInDBBase(UserId):
    documents: list


class ResetPassword(BaseModel):
    token: str
    new_password: str
class ResetAuditorPassword(BaseModel):
    token: str
    current_password: str
    new_password: str
    confirm_password: str | Optional[str] = None
class ForgetPassword(BaseModel):
    current_email: Optional[str] = None


class OTPVerification(BaseModel):
    email: str
    otp: str


class NameOrder(str, Enum):
    A_Z = "A-Z"
    Z_A = "Z-A"


class TaxSlab(str, Enum):
    Upto_2_5_lakh = "Upto 2.5 Lakh"
    From_2_5_5_lakh = "2.5 to 5 Lakh"
    Fom_5_7_5_lakh = "5 to 7.5 Lakh"
    From_7_5_10_lakh = "7.5 to 10 Lakh"
    Above_10_lakh = "Above 10 Lakh"


class Category(str, Enum):
    Consultation_Initiated = "Consultation Initiated"
    Assignment_and_Progress = "Assignment and Progress"
    Workflow_Progress = "Workflow Progress"
    Information_and_Documents = "Information and Documents"


class TaxPayerType(str, Enum):
    Salaried = "Salaried"
    Business = "Business"


class UserUpdateDeatils(BaseModel):
    tax_payer_type: Optional[TaxPayerType] = Field(None, example="Salaried")
    tax_slab: Optional[TaxSlab] = Field(None, example="2.5 to 5 Lakh")
    category: Optional[Category] = Field(None, example="Consultation Initiated")


class ExternalSourceBase(BaseModel):
    source: str


class UnifiedLeadBase(BaseModel):
    # User Identification
    id: Optional[str] = None
    user_id: Optional[str] = None  # Added explicit user_id field
    document_name: Optional[str] = None  # Added this line

    # Customer Details
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    country_code: Optional[str] = None
    pan_number: Optional[str] = None

    # Financial Details
    loan_amount: Optional[float] = None
    employment_type: Optional[str] = None
    loan_type: Optional[str] = None
    cibil_score: Optional[float] = None

    # Tracking Details
    lead_source: Optional[str] = None
    last_communicated: Optional[datetime] = None
    created_at: Optional[datetime] = None
    documents_count: Optional[int] = None

    # Additional details
    company_name: Optional[str] = None
    monthly_income: Optional[float] = None
    loan_purpose: Optional[str] = None
    loan_tenure: Optional[int] = None
    raw_data: Optional[dict] = None
    subscription_status: Optional[str] = None
    tax_payer_type: Optional[str] = None
    tax_slab: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True


class InternalUserLead(UnifiedLeadBase):
    id: str
    documents_count: Optional[int] = None
    lead_source: str = "internal_crm"


class LoanApplication(UnifiedLeadBase):
    id: str
    documentId: Optional[str] = None
    lead_source: str = "strapi_loan"


class CibilUserLead(UnifiedLeadBase):
    documentId: str
    lead_source: str = "strapi_cibil"


class NewsletterSubscriberLead(UnifiedLeadBase):
    lead_source: str = "beehiiv"
    subscription_status: Optional[str] = None


class CombinedDataResponse(BaseModel):
    total_records: int = Field(..., description="Total number of records across all sources")
    leads: List[UnifiedLeadBase] = Field(..., description="Combined list of leads from all sources")

    class Config:
        json_schema_extra = {
            "example": {
                "total_records": 150,
                "leads": [
                    {
                        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "full_name": "John Doe",
                        "email": "john@example.com",
                        "phone_number": "1234567890",
                        "country_code": "91",
                        "pan_number": "ABCDE1234F",
                        "loan_amount": 50000,
                        "employment_type": "Salaried",
                        "loan_type": "Personal",
                        "cibil_score": 750,
                        "lead_source": "internal_crm",
                        "last_communicated": "2024-02-18T10:00:00",
                        "created_at": "2024-02-18T10:00:00",
                        "documents_count": 3,
                        "tax_payer_type": "Salaried",
                        "tax_slab": "2.5 to 5 Lakh",
                        "category": "Consultation Initiated",
                    },
                    {
                        "id": "b2c3d4e5-f6g7-8901-hijk-lm2345678901",
                        "user_id": "b2c3d4e5-f6g7-8901-hijk-lm2345678901",
                        "email": "subscriber@example.com",
                        "lead_source": "beehiiv",
                        "created_at": "2024-02-10T08:30:00",
                        "subscription_status": "active",
                    },
                ],
            }
        }


class UserCreateManual(BaseModel):
    full_name: str = Field(..., example="John Doe")
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    country_code: Optional[str] = Field(None, example="91")
    status: Optional[str] = Field("New", example="New")
    is_active: Optional[bool] = Field(True, example=True)
    role: Optional[str] = Field("User", example="User")
    org_Name: Optional[str] = None
    pan_number: Optional[str] = None
    filling_status: Optional[str] = None
    service_selected: Optional[str] = None
    tax_payer_type: Optional[str] = None
    tax_slab: Optional[str] = None
    income_slab: Optional[str] = None
    regime_opted: Optional[str] = None
    gst_number: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = Field("whatsapp", example="whatsapp")
    loan_amount: Optional[float] = None
    employment_type: Optional[str] = None
    company_name: Optional[str] = None
    monthly_income: Optional[float] = None
    loan_purpose: Optional[str] = None
    loan_tenure: Optional[int] = None
    raw_data: Optional[dict] = None
    cibil_score: Optional[int] = None
    subscription_status: Optional[str] = None
    location: Optional[str] = Field(None, example="New Delhi")

    @root_validator(pre=True)
    def check_email_or_phone_present(cls, values):
        if "email" not in values and "phone_number" not in values:
            raise ValueError("Either email or phone number must be provided")
        return values


class UserFull(UserBase):
    id: str
    created_on: datetime
    updated_on: datetime
    last_communicated: Optional[str] = None
    phone_number: Optional[str] = None  # Make phone_number optional
    is_active: Optional[bool] = True
    role: Optional[str] = "User"
    source: Optional[str] = None
    loan_amount: Optional[float] = None
    employment_type: Optional[str] = None
    company_name: Optional[str] = None
    monthly_income: Optional[float] = None
    loan_purpose: Optional[str] = None
    loan_tenure: Optional[int] = None
    raw_data: Optional[dict] = None
    cibil_score: Optional[int] = None
    subscription_status: Optional[str] = None
    location: Optional[str] = Field(None, example="New Delhi")


class UserUpdateRequest(BaseModel):
    id: str
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    full_name: Optional[str] = None
    country_code: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    org_Name: Optional[str] = None
    pan_number: Optional[str] = None
    filling_status: Optional[str] = None
    service_selected: Optional[str] = None
    tax_payer_type: Optional[str] = None
    tax_slab: Optional[str] = None
    income_slab: Optional[str] = None
    regime_opted: Optional[str] = None
    gst_number: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    loan_amount: Optional[float] = None
    employment_type: Optional[str] = None
    company_name: Optional[str] = None
    monthly_income: Optional[float] = None
    loan_purpose: Optional[str] = None
    loan_tenure: Optional[int] = None
    raw_data: Optional[dict] = None
    cibil_score: Optional[int] = None
    subscription_status: Optional[str] = None
    location: Optional[str] = Field(None, example="New Delhi")

    class Config:
        # This allows partial updates
        extra = "ignore"
        # Make sure we use arbitrary_types_allowed to handle any custom types
        arbitrary_types_allowed = True


class UserBulkUpload(BaseModel):
    full_name: str
    phone_number: Optional[str]
    email: Optional[EmailStr]
    location: Optional[str]
    pan_number: Optional[str]
    cibil_score: Optional[int]
    source: Optional[str]
    employment_type: Optional[str]
    annual_income: Optional[float]
    loan_purpose: Optional[str]
    loan_amount_required: Optional[float]

    @root_validator(pre=True)
    def check_email_or_phone_present(cls, values):
        if not (values.get("email") or values.get("phone_number")):
            raise ValueError("Each row must have either email or phone number")
        return values


class BulkUploadResponse(BaseModel):
    detail: str
