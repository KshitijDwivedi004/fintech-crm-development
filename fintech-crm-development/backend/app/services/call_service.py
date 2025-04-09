import json
import httpx
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from app.core.config import settings
from app.repository.call_repository import (
    telecaller_repository,
    call_log_repository,
    call_note_repository,
    call_disposition_repository,
)
from app.repository.user_repository import user_repository
from app.repository.lead_repository import lead_repository
from app.utils.cryptoUtil import get_password_hash, verify_password


class TelecallerService:
    async def create(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        # Hash the password
        hashed_password = get_password_hash(obj_in["password"])
        del obj_in["password"]
        obj_in["hashed_password"] = hashed_password
        obj_in["role"] = "Telecaller"

        return await telecaller_repository.create(obj_in)

    async def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        telecaller = await telecaller_repository.get_by_email(email)
        if not telecaller:
            return None
        if not verify_password(password, telecaller["hashed_password"]):
            return None
        return telecaller

    async def get(self, id: UUID) -> Optional[Dict[str, Any]]:
        return await telecaller_repository.get(id)

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await telecaller_repository.get_by_email(email)

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        return await telecaller_repository.get_multi(skip=skip, limit=limit)

    async def update(self, id: UUID, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        if "password" in obj_in:
            hashed_password = get_password_hash(obj_in["password"])
            del obj_in["password"]
            obj_in["hashed_password"] = hashed_password

        return await telecaller_repository.update(id, obj_in)

    async def delete(self, id: UUID) -> Dict[str, Any]:
        return await telecaller_repository.delete(id)

    async def is_active(self, telecaller: Dict[str, Any]) -> bool:
        return telecaller_repository.is_active(telecaller)


class AlohaaService:

    async def click_to_call(
        self, telecaller_id: UUID, lead_id: UUID, receiver_number: str
    ) -> Dict[str, Any]:
        """
        Initiate a click-to-call using Alohaa API
        """
        # Get telecaller details
        telecaller = await telecaller_repository.get(telecaller_id)
        if not telecaller:
            return {
                "success": False,
                "error": {"code": 1006, "reason": "Telecaller does not exist"},
            }

        # Get lead details
        lead = await lead_repository.get(lead_id)
        if not lead:
            return {"success": False, "error": {"code": 1007, "reason": "Lead does not exist"}}

        # Prepare the request payload
        payload = {
            "caller_number": telecaller["phone_number"],
            "receiver_number": receiver_number,
            "did_number": settings.ALOHAA_DID_NUMBER,
            "is_agent_required": True,
        }

        # Make the API call to Alohaa
        try:
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

                # Create a call log entry
                call_log_data = {
                    "telecaller_id": telecaller_id,
                    "lead_id": lead_id,
                    "caller_number": telecaller["phone_number"],
                    "receiver_number": receiver_number,
                    "did_number": settings.ALOHAA_DID_NUMBER,
                    "call_start_time": datetime.now(),
                }

                if response_data.get("success"):
                    call_log_data["reference_id"] = response_data["response"]["reference_id"]

                # Save the call log
                await call_log_repository.create(call_log_data)

                return response_data

        except Exception as e:
            return {"success": False, "error": {"code": 1000, "reason": f"Error: {str(e)}"}}

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
            call_log = await call_log_repository.get_by_call_id(payload.get("call_id"))

            if not call_log:
                # Try to find by reference_id if call_id is not found
                call_log = await call_log_repository.get_by_reference_id(
                    payload.get("reference_id", "")
                )

            if call_log:
                # Update the call log with details from the webhook
                update_data = {
                    "status": payload.get("call_status"),
                    "call_duration": payload.get("call_duration"),
                    "recording_url": payload.get("call_recording_url"),
                    "call_end_time": payload.get("ended_at") or datetime.now(),
                }

                updated_call_log = await call_log_repository.update(call_log["id"], update_data)
                return {"success": True, "call_log_id": str(updated_call_log["id"])}

        return {"success": False, "error": "Call log not found or webhook not supported"}


class CallLogService:
    async def create(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await call_log_repository.create(obj_in)

    async def get(self, id: UUID) -> Optional[Dict[str, Any]]:
        return await call_log_repository.get(id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        telecaller_id: Optional[UUID] = None,
        lead_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        return await call_log_repository.get_multi(
            skip=skip,
            limit=limit,
            telecaller_id=telecaller_id,
            lead_id=lead_id,
            start_date=start_date,
            end_date=end_date,
        )

    async def update(self, id: UUID, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await call_log_repository.update(id, obj_in)

    async def delete(self, id: UUID) -> Dict[str, Any]:
        return await call_log_repository.delete(id)


class CallNoteService:
    async def create(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await call_note_repository.create(obj_in)

    async def get(self, id: UUID) -> Optional[Dict[str, Any]]:
        return await call_note_repository.get(id)

    async def get_by_call_log_id(self, call_log_id: UUID) -> List[Dict[str, Any]]:
        return await call_note_repository.get_by_call_log_id(call_log_id)

    async def get_multi(
        self, skip: int = 0, limit: int = 100, telecaller_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        return await call_note_repository.get_multi(
            skip=skip, limit=limit, telecaller_id=telecaller_id
        )

    async def update(self, id: UUID, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await call_note_repository.update(id, obj_in)

    async def delete(self, id: UUID) -> Dict[str, Any]:
        return await call_note_repository.delete(id)


class CallDispositionService:
    async def create(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await call_disposition_repository.create(obj_in)

    async def get(self, id: UUID) -> Optional[Dict[str, Any]]:
        return await call_disposition_repository.get(id)

    async def get_by_call_log_id(self, call_log_id: UUID) -> Optional[Dict[str, Any]]:
        return await call_disposition_repository.get_by_call_log_id(call_log_id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        telecaller_id: Optional[UUID] = None,
        disposition_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return await call_disposition_repository.get_multi(
            skip=skip, limit=limit, telecaller_id=telecaller_id, disposition_type=disposition_type
        )

    async def update(self, id: UUID, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await call_disposition_repository.update(id, obj_in)

    async def delete(self, id: UUID) -> Dict[str, Any]:
        return await call_disposition_repository.delete(id)


telecaller_service = TelecallerService()
alohaa_service = AlohaaService()
call_log_service = CallLogService()
call_note_service = CallNoteService()
call_disposition_service = CallDispositionService()
