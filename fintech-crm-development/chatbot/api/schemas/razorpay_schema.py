from pydantic import BaseModel


class RazorPayBase(BaseModel):
    event_id: str
    user_phone: str
    user_email: str | None
    order_id: str
    payment_id: str
    amount: str
    currency: str
    status: str
    method: str
    created_at: str


class RazorPayCreate(RazorPayBase):
    error_code: str | None
    error_source: str | None
    error_description: str | None
