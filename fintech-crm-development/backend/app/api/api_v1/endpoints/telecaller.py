from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query, status

from app.api.api_v1.deps import get_current_active_auditor
from app.repository.telecaller_repository import TelecallerRepository
from app.services.telecaller_service import TelecallerService
from app.schemas.telecaller_schemas import (
    TelecallerStatusUpdate,
    TelecallerStatusResponse,
    ClickToCallRequest,
    ClickToCallResponse,
    CallLog,
    CallLogCreate,
    CallNote,
    CallNoteCreate,
    CallDisposition,
    CallDispositionCreate,
    OutgoingCallWebhookPayload,
)
from app.core.config import settings
from app.core.websocket import websocket_manager
from app.enum.telecaller_status import TelecallerStatus

router = APIRouter()


def get_telecaller_repository():
    """Dependency to get the TelecallerRepository instance."""
    return TelecallerRepository()


@router.post("/status/{user_id}", response_model=TelecallerStatusResponse)
async def update_status(
    user_id: str,
    status_update: TelecallerStatusUpdate,
    repository: TelecallerRepository = Depends(get_telecaller_repository),
):
    """Update the status of a telecaller."""
    service = TelecallerService(repository)
    success = await service.update_status(user_id, status_update.status)

    telecaller = await repository.get_telecaller(user_id)
    if not telecaller:
        raise HTTPException(status_code=404, detail="Telecaller not found")

    return telecaller


@router.get("/status/{user_id}", response_model=TelecallerStatusResponse)
async def get_status(
    user_id: str,
    repository: TelecallerRepository = Depends(get_telecaller_repository),
):
    """Get the status of a telecaller."""
    telecaller = await repository.get_telecaller(user_id)
    if not telecaller:
        raise HTTPException(status_code=404, detail="Telecaller not found")

    return telecaller


@router.get("/status", response_model=List[TelecallerStatusResponse])
async def get_statuses(repository: TelecallerRepository = Depends(get_telecaller_repository)):
    """Get the statuses of all telecallers."""
    telecallers = await repository.get_telecallers()
    return telecallers


# New endpoints for call functionality
@router.post("/click-to-call", response_model=ClickToCallResponse)
async def click_to_call(
    call_req: ClickToCallRequest,
    current_user: Any = Depends(get_current_active_auditor),
    repository: TelecallerRepository = Depends(get_telecaller_repository),
):
    """
    Initiate a call to a lead using Alohaa's Click to Call API
    """
    service = TelecallerService(repository)

    # Set telecaller to BUSY status
    await service.update_status(current_user.id, TelecallerStatus.BUSY)

    result = await service.click_to_call(
        user_id=current_user.id, lead_id=call_req.lead_id, receiver_number=call_req.receiver_number
    )

    # Also notify via websocket that a call has been initiated
    if result.get("success"):
        await websocket_manager.broadcast(
            {
                "event": "call_initiated",
                "user_id": current_user.id,
                "lead_id": call_req.lead_id,
                "receiver_number": call_req.receiver_number,
                "reference_id": result.get("response", {}).get("reference_id"),
            }
        )

    return result


@router.get("/call-logs", response_model=List[CallLog])
async def read_call_logs(
    skip: int = 0,
    limit: int = 100,
    lead_id: Optional[str] = None,  # Changed from UUID to str
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Any = Depends(get_current_active_auditor),
    repository: TelecallerRepository = Depends(get_telecaller_repository),
):
    """
    Retrieve call logs for the current telecaller
    """
    return await repository.get_call_logs(
        skip=skip,
        limit=limit,
        user_id=current_user.id,
        lead_id=lead_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/call-logs/{call_log_id}", response_model=CallLog)
async def read_call_log(
    call_log_id: UUID = Path(...),
    current_user: Any = Depends(get_current_active_auditor),
    repository: TelecallerRepository = Depends(get_telecaller_repository),
):
    """
    Get a specific call log by ID
    """
    call_log = await repository.get_call_log(call_log_id)
    if not call_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call log not found")

    # Ensure the telecaller can only access their own call logs
    if call_log["user_id"] != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return call_log


@router.post("/call-notes", response_model=CallNote)
async def create_call_note(
    note_in: CallNoteCreate,
    current_user: Any = Depends(get_current_active_auditor),
    repository: TelecallerRepository = Depends(get_telecaller_repository),
):
    """
    Create a note for a call
    """
    service = TelecallerService(repository)

    # Verify the call log exists and belongs to the telecaller
    call_log = await repository.get_call_log(note_in.call_log_id)
    if not call_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call log not found")

    if call_log["user_id"] != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    # Ensure the user_id matches the current user
    note_data = note_in.dict()
    note_data["user_id"] = current_user.id

    note = await repository.create_call_note(note_data)

    # Notify via websocket
    await websocket_manager.broadcast(
        {
            "event": "call_note_created",
            "call_log_id": str(note_in.call_log_id),
            "note_id": str(note["id"]),
        }
    )

    return note


@router.get("/call-notes/call/{call_log_id}", response_model=List[CallNote])
async def read_call_notes_by_call(
    call_log_id: UUID = Path(...),
    current_user: Any = Depends(get_current_active_auditor),
    repository: TelecallerRepository = Depends(get_telecaller_repository),
):
    """
    Get all notes for a specific call
    """
    # Verify the call log exists and belongs to the telecaller
    call_log = await repository.get_call_log(call_log_id)
    if not call_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call log not found")

    if call_log["user_id"] != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return await repository.get_call_notes_by_call_log_id(call_log_id)


@router.post("/call-disposition", response_model=CallDisposition)
async def create_call_disposition(
    disposition_in: CallDispositionCreate,
    current_user: Any = Depends(get_current_active_auditor),
    repository: TelecallerRepository = Depends(get_telecaller_repository),
):
    """
    Create a disposition for a call
    """
    service = TelecallerService(repository)

    # Verify the call log exists and belongs to the telecaller
    call_log = await repository.get_call_log(disposition_in.call_log_id)
    if not call_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call log not found")

    if call_log["user_id"] != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    # Check if disposition already exists
    existing_disposition = await repository.get_call_disposition_by_call_log_id(
        disposition_in.call_log_id
    )
    if existing_disposition:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Call disposition already exists for this call",
        )

    # Ensure the user_id matches the current user
    disposition_data = disposition_in.dict()
    disposition_data["user_id"] = current_user.id

    # Change status back to ACTIVE
    await service.update_status(current_user.id, TelecallerStatus.ACTIVE)

    disposition = await repository.create_call_disposition(disposition_data)

    # Notify via websocket
    await websocket_manager.broadcast(
        {
            "event": "call_disposition_created",
            "call_log_id": str(disposition_in.call_log_id),
            "disposition_id": str(disposition["id"]),
            "disposition_type": disposition["disposition_type"],
        }
    )

    return disposition


@router.get("/call-disposition/call/{call_log_id}", response_model=CallDisposition)
async def read_call_disposition_by_call(
    call_log_id: UUID = Path(...),
    current_user: Any = Depends(get_current_active_auditor),
    repository: TelecallerRepository = Depends(get_telecaller_repository),
):
    """
    Get the disposition for a specific call
    """
    # Verify the call log exists and belongs to the telecaller
    call_log = await repository.get_call_log(call_log_id)
    if not call_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call log not found")

    if call_log["user_id"] != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    disposition = await repository.get_call_disposition_by_call_log_id(call_log_id)
    if not disposition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Call disposition not found"
        )

    return disposition


# Webhook endpoint for Alohaa callbacks
@router.post("/alohaa-webhook", status_code=status.HTTP_200_OK)
async def alohaa_webhook(
    payload: OutgoingCallWebhookPayload,
    repository: TelecallerRepository = Depends(get_telecaller_repository),
):
    """
    Webhook endpoint to receive call status updates from Alohaa
    """
    service = TelecallerService(repository)
    result = await service.process_webhook(payload.dict())

    # If successful, notify via websocket
    if result.get("success") and result.get("call_log_id"):
        # Get the call log to extract user_id
        call_log = await repository.get_call_log(UUID(result.get("call_log_id")))

        if call_log:
            # Update the telecaller status back to ACTIVE if call is completed
            await service.update_status(call_log["user_id"], TelecallerStatus.ACTIVE)

            await websocket_manager.broadcast(
                {
                    "event": "call_completed",
                    "call_log_id": result["call_log_id"],
                    "user_id": call_log["user_id"],
                    "call_status": payload.call_status,
                    "call_duration": payload.call_duration,
                }
            )

    return {"status": "processed"}


# Endpoint to get signed URL for call recording
@router.get("/call-recording/{document_id}", response_model=dict)
async def get_call_recording_url(
    document_id: str = Path(...),
    current_user: Any = Depends(get_current_active_auditor),
    repository: TelecallerRepository = Depends(get_telecaller_repository),
):
    """
    Get a signed URL for a call recording
    """
    service = TelecallerService(repository)
    result = await service.get_signed_url(document_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", {}).get("reason", "Recording not found"),
        )

    return result
