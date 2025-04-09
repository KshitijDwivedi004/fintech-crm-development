from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.db.session import database
from app.models.call import telecaller, call_log, call_note, call_disposition
from app.repository.base_repository import base_repository


class TelecallerRepository:
    async def create(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await base_repository.create(telecaller, obj_in)

    async def get(self, id: UUID) -> Optional[Dict[str, Any]]:
        return await base_repository.get(telecaller, id=id)

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        query = telecaller.select().where(telecaller.c.email == email)
        return await database.fetch_one(query)

    async def get_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        query = telecaller.select().where(telecaller.c.phone_number == phone_number)
        return await database.fetch_one(query)

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        return await base_repository.get_multi(telecaller, skip=skip, limit=limit)

    async def update(self, id: UUID, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await base_repository.update(telecaller, id, obj_in)

    async def delete(self, id: UUID) -> Dict[str, Any]:
        return await base_repository.delete(telecaller, id)

    async def is_active(self, telecaller_obj: Dict[str, Any]) -> bool:
        return telecaller_obj.get("is_active", False)


class CallLogRepository:
    async def create(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await base_repository.create(call_log, obj_in)

    async def get(self, id: UUID) -> Optional[Dict[str, Any]]:
        return await base_repository.get(call_log, id=id)

    async def get_by_reference_id(self, reference_id: str) -> Optional[Dict[str, Any]]:
        query = call_log.select().where(call_log.c.reference_id == reference_id)
        return await database.fetch_one(query)

    async def get_by_call_id(self, call_id: str) -> Optional[Dict[str, Any]]:
        query = call_log.select().where(call_log.c.call_id == call_id)
        return await database.fetch_one(query)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        telecaller_id: Optional[UUID] = None,
        lead_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        query = call_log.select()

        if telecaller_id:
            query = query.where(call_log.c.telecaller_id == telecaller_id)

        if lead_id:
            query = query.where(call_log.c.lead_id == lead_id)

        if start_date:
            query = query.where(call_log.c.created_at >= start_date)

        if end_date:
            query = query.where(call_log.c.created_at <= end_date)

        query = query.order_by(call_log.c.created_at.desc()).offset(skip).limit(limit)
        return await database.fetch_all(query)

    async def update(self, id: UUID, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await base_repository.update(call_log, id, obj_in)

    async def delete(self, id: UUID) -> Dict[str, Any]:
        return await base_repository.delete(call_log, id)


class CallNoteRepository:
    async def create(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await base_repository.create(call_note, obj_in)

    async def get(self, id: UUID) -> Optional[Dict[str, Any]]:
        return await base_repository.get(call_note, id=id)

    async def get_by_call_log_id(self, call_log_id: UUID) -> List[Dict[str, Any]]:
        query = call_note.select().where(call_note.c.call_log_id == call_log_id)
        return await database.fetch_all(query)

    async def get_multi(
        self, skip: int = 0, limit: int = 100, telecaller_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        query = call_note.select()

        if telecaller_id:
            query = query.where(call_note.c.telecaller_id == telecaller_id)

        query = query.order_by(call_note.c.created_at.desc()).offset(skip).limit(limit)
        return await database.fetch_all(query)

    async def update(self, id: UUID, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await base_repository.update(call_note, id, obj_in)

    async def delete(self, id: UUID) -> Dict[str, Any]:
        return await base_repository.delete(call_note, id)


class CallDispositionRepository:
    async def create(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await base_repository.create(call_disposition, obj_in)

    async def get(self, id: UUID) -> Optional[Dict[str, Any]]:
        return await base_repository.get(call_disposition, id=id)

    async def get_by_call_log_id(self, call_log_id: UUID) -> Optional[Dict[str, Any]]:
        query = call_disposition.select().where(call_disposition.c.call_log_id == call_log_id)
        return await database.fetch_one(query)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        telecaller_id: Optional[UUID] = None,
        disposition_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = call_disposition.select()

        if telecaller_id:
            query = query.where(call_disposition.c.telecaller_id == telecaller_id)

        if disposition_type:
            query = query.where(call_disposition.c.disposition_type == disposition_type)

        query = query.order_by(call_disposition.c.created_at.desc()).offset(skip).limit(limit)
        return await database.fetch_all(query)

    async def update(self, id: UUID, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        return await base_repository.update(call_disposition, id, obj_in)

    async def delete(self, id: UUID) -> Dict[str, Any]:
        return await base_repository.delete(call_disposition, id)


telecaller_repository = TelecallerRepository()
call_log_repository = CallLogRepository()
call_note_repository = CallNoteRepository()
call_disposition_repository = CallDispositionRepository()
