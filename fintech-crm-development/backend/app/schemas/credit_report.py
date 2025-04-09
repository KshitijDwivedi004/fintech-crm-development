from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class OTPGenerateRequest(BaseModel):
    """
    Request model for generating OTP for credit report
    """

    phone_number: str = Field(..., description="Phone number to receive OTP")
    orderid: str = Field("1", description="Order ID")


class OTPGenerateResponse(BaseModel):
    """
    Response model for OTP generation
    """

    code: str
    status: str
    mess: str
    data: str


class CreditReportRequest(BaseModel):
    """
    Request model for fetching credit report
    """

    fname: str = Field(..., description="First name")
    lname: str = Field(..., description="Last name")
    dob: str = Field(..., description="Date of birth in DD-MM-YYYY format")
    phone_number: str = Field(..., description="Phone number")
    pan_num: str = Field(..., description="PAN number")
    otp: str = Field(..., description="OTP received")
    orderid: str = Field("1", description="Order ID")
    user_id: Optional[str] = Field(None, description="Optional user ID for association")
    lead_source: Optional[str] = Field("Website", description="Source of the lead")


class CreditReportResponse(BaseModel):
    """
    Response model for credit report
    """

    code: str
    status: str
    mess: str
    data: Dict[str, Any]
    from_database: Optional[bool] = Field(
        None, description="Whether the report was retrieved from database"
    )


class CreditReportListItem(BaseModel):
    """
    Model for credit report list item
    """

    id: int
    user_id: Optional[str] = None
    pan_number: str
    phone_number: str
    first_name: str
    last_name: str
    dob: str
    credit_score: Optional[int] = None
    total_accounts: Optional[int] = None
    active_accounts: Optional[int] = None
    closed_accounts: Optional[int] = None
    delinquent_accounts: Optional[int] = None
    lead_source: Optional[str] = "Website"
    created_at: Any
    updated_at: Any
    raw_data: Optional[Dict[str, Any]] = None


class CreditReportListData(BaseModel):
    """
    Data model for credit report list response
    """

    reports: List[CreditReportListItem]
    total: int
    limit: int
    skip: int


class CreditReportListResponse(BaseModel):
    """
    Response model for credit report list
    """

    code: str
    status: str
    mess: str
    data: CreditReportListData


class APIErrorResponse(BaseModel):
    """
    Error response model
    """

    code: str
    status: str = "error"
    mess: str
    data: Optional[Dict[str, Any]] = None


class DeleteReportResponse(BaseModel):
    """
    Response model for delete operation
    """

    code: str
    status: str
    mess: str
    data: Optional[Dict[str, Any]] = None
