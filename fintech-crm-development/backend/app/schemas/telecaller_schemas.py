from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from app.enum.telecaller_status import TelecallerStatus


# Keep existing schemas
class TelecallerStatusUpdate(BaseModel):
    status: TelecallerStatus


class TelecallerStatusResponse(BaseModel):
    user_id: str
    status: TelecallerStatus
    last_active_time: Optional[datetime] = None
    total_active_time: Optional[int] = None
    total_break_time: Optional[int] = None


# Add new schemas for calling functionality
class ClickToCallRequest(BaseModel):
    lead_id: str  # Changed from UUID to str to match the model
    receiver_number: str


class ClickToCallResponse(BaseModel):
    success: bool
    reference_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None


# Call Log Schemas
class CallLogBase(BaseModel):
    user_id: str
    lead_id: str  # Changed from UUID to str
    caller_number: str
    receiver_number: str
    did_number: Optional[str] = None
    call_id: Optional[str] = None
    reference_id: Optional[str] = None
    status: Optional[str] = None
    call_duration: Optional[int] = 0
    recording_url: Optional[str] = None
    call_start_time: Optional[datetime] = None
    call_end_time: Optional[datetime] = None


class CallLogCreate(CallLogBase):
    pass


class CallLogUpdate(BaseModel):
    status: Optional[str] = None
    call_duration: Optional[int] = None
    recording_url: Optional[str] = None
    call_end_time: Optional[datetime] = None


class CallLogInDB(CallLogBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class CallLog(CallLogInDB):
    pass


# Call Note Schemas
class CallNoteBase(BaseModel):
    call_log_id: UUID
    user_id: str
    content: str


class CallNoteCreate(CallNoteBase):
    pass


class CallNoteUpdate(BaseModel):
    content: Optional[str] = None


class CallNoteInDB(CallNoteBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class CallNote(CallNoteInDB):
    pass


# Call Disposition Schemas
class CallDispositionBase(BaseModel):
    call_log_id: UUID
    user_id: str
    disposition_type: str
    follow_up_date: Optional[datetime] = None
    additional_details: Optional[Dict[str, Any]] = None


class CallDispositionCreate(CallDispositionBase):
    pass


class CallDispositionUpdate(BaseModel):
    disposition_type: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    additional_details: Optional[Dict[str, Any]] = None


class CallDispositionInDB(CallDispositionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class CallDisposition(CallDispositionInDB):
    pass


# Webhook Payload Schemas
class OutgoingCallWebhookPayload(BaseModel):
    organisation_id: str
    call_type: str
    caller_number: str
    receiver_number: str
    did_number: str
    received_at: datetime
    ended_at: Optional[datetime] = None
    call_id: str
    call_status: Optional[str] = None
    call_duration: Optional[int] = None
    call_recording_url: Optional[str] = None
    agent_name: Optional[str] = None
    initiator_ring_duration: Optional[int] = None
    receiver_ring_duration: Optional[int] = None
    total_ring_duration: Optional[int] = None
    hangup_cause: Optional[str] = None
