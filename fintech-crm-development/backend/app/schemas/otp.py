from pydantic import BaseModel, Field


class CreateOTP(BaseModel):
    phone_number: str


class VerifyOTP(CreateOTP):
    otp_code: int


class InfoOTP(VerifyOTP):
    otp_failed_count: int
    status: bool
