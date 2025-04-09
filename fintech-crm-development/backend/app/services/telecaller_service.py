import json
import httpx
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import sqlalchemy
import uuid


from app.repository.telecaller_repository import TelecallerRepository
from app.repository.user_repository import user_repository
from app.enum.telecaller_status import TelecallerStatus
from app.core.config import settings
from app.core.websocket import websocket_manager
from app.db.session import database
from app.models.telecallers import call_log


class TelecallerService:
    def __init__(self, repository: TelecallerRepository):
        self.repository = repository

    async def update_status(self, user_id: str, status: TelecallerStatus) -> bool:
        """Update the status of a telecaller."""
        return await self.repository.update_status(user_id, status)

    # Direct database insert for call log
    async def create_call_log_direct(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a call log with explicit datetime handling"""
        # Create a copy to avoid modifying the original data
        call_data = dict(data)

        # Set ID if not present
        if "id" not in call_data:
            call_data["id"] = UUID(str(uuid.uuid4()))

        # Handle datetime fields
        now = datetime.now()
        call_data["created_at"] = now
        call_data["updated_at"] = now

        # Ensure call_start_time is set
        if "call_start_time" not in call_data or call_data["call_start_time"] is None:
            call_data["call_start_time"] = now

        # Execute the insert directly
        query = call_log.insert().values(**call_data)
        result_id = await database.execute(query)

        # Return the created data
        return {"id": result_id, **call_data}

    # Call functionality
    async def click_to_call(
        self, user_id: str, lead_id: str, receiver_number: str
    ) -> Dict[str, Any]:
        """
        Initiate a click-to-call using Alohaa API
        """
        try:
            # Get telecaller details
            telecaller = await self.repository.get_telecaller(user_id)
            if not telecaller:
                return {"success": False, "error": {"code": 1006, "reason": "Telecaller not found"}}

            # Get lead details - Using user_repository instead of lead_repository
            lead = await user_repository.get_by_id(lead_id)
            if not lead:
                return {"success": False, "error": {"code": 1007, "reason": "Lead not found"}}

            # Get the actual phone number from the auditor table
            auditor_query = "SELECT phone_number FROM auditor WHERE id = :user_id"
            caller_record = await database.fetch_one(auditor_query, {"user_id": user_id})

            if not caller_record:
                return {
                    "success": False,
                    "error": {"code": 1008, "reason": "Caller phone number not found"},
                }

            caller_number = caller_record["phone_number"]

            # Prepare the request payload for Alohaa
            payload = {
                "caller_number": caller_number,
                "receiver_number": receiver_number,
                "did_number": settings.ALOHAA_DID_NUMBER,
                "is_agent_required": False,
            }

            # Make the API call to Alohaa
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://outgoing-call.alohaa.ai/v1/external/click-2-call",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "x-metro-api-key": settings.ALOHAA_API_KEY,
                    },
                )

                response_data = response.json()

                # Skip database logging if this is a test call
                if response_data.get("success"):
                    # Direct database insert to avoid serialization issues
                    call_record = {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "lead_id": lead_id,
                        "caller_number": caller_number,
                        "receiver_number": receiver_number,
                        "did_number": settings.ALOHAA_DID_NUMBER,
                        "reference_id": response_data["response"]["reference_id"],
                    }

                    # Use direct SQL query to insert
                    query = call_log.insert().values(
                        **call_record,
                        call_start_time=datetime.now(),
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    print(query)
                    await database.execute(query)

                return response_data

        except Exception as e:
            return {"success": False, "error": {"code": 1000, "reason": f"Error: {str(e)}"}}

    # Other methods remain the same
    async def get_signed_url(self, document_id: str) -> Dict[str, Any]:
        """
        Get a signed URL for call recording
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://outgoing-call.alohaa.ai/v1/external/get-signed-url",
                    json={"document_id": document_id},
                    headers={
                        "Content-Type": "application/json",
                        "x-metro-api-key": settings.ALOHAA_API_KEY,
                    },
                )

                return response.json()

        except Exception as e:
            return {"success": False, "error": {"code": 1000, "reason": f"Error: {str(e)}"}}

    async def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webhooks received from Alohaa
        """
        # Check if it's an outgoing call webhook
        if payload.get("call_type") == "outgoing":
            # Find the call log entry by call_id
            call_log = await self.repository.get_call_log_by_call_id(payload.get("call_id"))

            if not call_log:
                # Try to find by reference_id if call_id is not found
                call_log = await self.repository.get_call_log_by_reference_id(
                    payload.get("reference_id", "")
                )

            if call_log:
                # Update the call log with details from the webhook
                # Fix: Convert string to datetime if needed
                ended_at = payload.get("ended_at")
                if isinstance(ended_at, str):
                    try:
                        ended_at = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
                    except ValueError:
                        ended_at = datetime.now()

                update_data = {
                    "status": payload.get("call_status"),
                    "call_duration": payload.get("call_duration"),
                    "recording_url": payload.get("call_recording_url"),
                    "call_end_time": ended_at or datetime.now(),
                }

                updated_call_log = await self.repository.update_call_log(
                    call_log["id"], update_data
                )
                return {"success": True, "call_log_id": str(updated_call_log["id"])}

        return {"success": False, "error": "Call log not found or webhook not supported"}

    # Other methods remain the same...
