from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.db.session import database
from app.models.telecallers import telecallers, call_log, call_note, call_disposition
from app.repository.base_repository import base_repository
from app.enum.telecaller_status import TelecallerStatus


class TelecallerRepository:
    async def get_telecaller(self, user_id: str):
        """Get telecaller status by user_id."""
        query = telecallers.select().where(telecallers.c.user_id == user_id)
        return await database.fetch_one(query)

    async def get_telecallers(self):
        """Get statuses of all telecallers."""
        query = telecallers.select()
        return await database.fetch_all(query)

    async def update_status(self, user_id: str, status: TelecallerStatus) -> bool:
        """Update the status of a telecaller."""
        # Get the current telecaller record
        query = telecallers.select().where(telecallers.c.user_id == user_id)
        telecaller = await database.fetch_one(query)

        now = datetime.utcnow()

        # If telecaller doesn't exist, create a new record
        if not telecaller:
            query = telecallers.insert().values(
                user_id=user_id,
                status=status,
                last_active_time=now if status == TelecallerStatus.ACTIVE else None,
            )
            await database.execute(query)
            return True

        update_values = {"status": status}

        # Handle status transitions
        if telecaller["status"] == TelecallerStatus.ACTIVE and status != TelecallerStatus.ACTIVE:
            # Calculate active time
            if telecaller["last_active_time"]:
                active_duration = int((now - telecaller["last_active_time"]).total_seconds())
                update_values["total_active_time"] = (
                    telecaller["total_active_time"] + active_duration
                )

            if status == TelecallerStatus.BREAK:
                update_values["break_start_time"] = now

        elif telecaller["status"] == TelecallerStatus.BREAK and status != TelecallerStatus.BREAK:
            # Calculate break time
            if telecaller["break_start_time"]:
                break_duration = int((now - telecaller["break_start_time"]).total_seconds())
                update_values["total_break_time"] = telecaller["total_break_time"] + break_duration
                update_values["break_start_time"] = None

        if status == TelecallerStatus.ACTIVE:
            update_values["last_active_time"] = now

        # Update the telecaller record
        query = telecallers.update().where(telecallers.c.user_id == user_id).values(**update_values)
        await database.execute(query)
        return True

    # Call log methods
    async def create_call_log(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        """Create a call log entry."""
        # Ensure call_start_time is a datetime object
        if "call_start_time" in obj_in and isinstance(obj_in["call_start_time"], str):
            obj_in["call_start_time"] = datetime.fromisoformat(
                obj_in["call_start_time"].replace("Z", "+00:00")
            )

        # Also process call_end_time if present
        if "call_end_time" in obj_in and isinstance(obj_in["call_end_time"], str):
            obj_in["call_end_time"] = datetime.fromisoformat(
                obj_in["call_end_time"].replace("Z", "+00:00")
            )

        return await base_repository.create(call_log, obj_in)

    async def get_call_log(self, id: UUID) -> Optional[Dict[str, Any]]:
        return await base_repository.get(call_log, id=id)

    async def get_call_log_by_reference_id(self, reference_id: str) -> Optional[Dict[str, Any]]:
        query = call_log.select().where(call_log.c.reference_id == reference_id)
        return await database.fetch_one(query)

    async def get_call_log_by_call_id(self, call_id: str) -> Optional[Dict[str, Any]]:
        query = call_log.select().where(call_log.c.call_id == call_id)
        return await database.fetch_one(query)

    async def get_call_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
        lead_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        query = call_log.select()

        if user_id:
            query = query.where(call_log.c.user_id == user_id)

        if lead_id:
            query = query.where(call_log.c.lead_id == lead_id)

        if start_date:
            query = query.where(call_log.c.created_at >= start_date)

        if end_date:
            query = query.where(call_log.c.created_at <= end_date)

        query = query.order_by(call_log.c.created_at.desc()).offset(skip).limit(limit)
        return await database.fetch_all(query)

    async def update_call_log(self, id: UUID, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure call_end_time is a datetime object
        if "call_end_time" in obj_in and isinstance(obj_in["call_end_time"], str):
            obj_in["call_end_time"] = datetime.fromisoformat(
                obj_in["call_end_time"].replace("Z", "+00:00")
            )

        return await base_repository.update(call_log, id, obj_in)

    async def delete_call_log(self, id: UUID) -> Dict[str, Any]:
        return await base_repository.delete(call_log, id)

    # Call Note methods
    async def create_call_note(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await base_repository.create(call_note, obj_in)

    async def get_call_note(self, id: UUID) -> Optional[Dict[str, Any]]:
        return await base_repository.get(call_note, id=id)

    async def get_call_notes_by_call_log_id(self, call_log_id: UUID) -> List[Dict[str, Any]]:
        query = call_note.select().where(call_note.c.call_log_id == call_log_id)
        return await database.fetch_all(query)

    async def get_call_notes(
        self, skip: int = 0, limit: int = 100, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = call_note.select()

        if user_id:
            query = query.where(call_note.c.user_id == user_id)

        query = query.order_by(call_note.c.created_at.desc()).offset(skip).limit(limit)
        return await database.fetch_all(query)

    async def update_call_note(self, id: UUID, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await base_repository.update(call_note, id, obj_in)

    async def delete_call_note(self, id: UUID) -> Dict[str, Any]:
        return await base_repository.delete(call_note, id)

    # Call Disposition methods
    async def create_call_disposition(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        # Handle follow_up_date if present
        if "follow_up_date" in obj_in and isinstance(obj_in["follow_up_date"], str):
            obj_in["follow_up_date"] = datetime.fromisoformat(
                obj_in["follow_up_date"].replace("Z", "+00:00")
            )

        return await base_repository.create(call_disposition, obj_in)

    async def get_call_disposition(self, id: UUID) -> Optional[Dict[str, Any]]:
        return await base_repository.get(call_disposition, id=id)

    async def get_call_disposition_by_call_log_id(
        self, call_log_id: UUID
    ) -> Optional[Dict[str, Any]]:
        query = call_disposition.select().where(call_disposition.c.call_log_id == call_log_id)
        return await database.fetch_one(query)

    async def get_call_dispositions(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
        disposition_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = call_disposition.select()

        if user_id:
            query = query.where(call_disposition.c.user_id == user_id)

        if disposition_type:
            query = query.where(call_disposition.c.disposition_type == disposition_type)

        query = query.order_by(call_disposition.c.created_at.desc()).offset(skip).limit(limit)
        return await database.fetch_all(query)

    async def update_call_disposition(self, id: UUID, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        # Handle follow_up_date if present
        if "follow_up_date" in obj_in and isinstance(obj_in["follow_up_date"], str):
            obj_in["follow_up_date"] = datetime.fromisoformat(
                obj_in["follow_up_date"].replace("Z", "+00:00")
            )

        return await base_repository.update(call_disposition, id, obj_in)

    async def delete_call_disposition(self, id: UUID) -> Dict[str, Any]:
        return await base_repository.delete(call_disposition, id)
