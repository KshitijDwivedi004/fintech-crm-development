from sqlalchemy import select, func
from sqlalchemy import insert, update, delete
import sqlalchemy
from app.models.notes import notes
import uuid
from typing import Dict, Any
from app.db.session import database

class NotesRepository:
    
    @staticmethod
    async def get_notes_paginated(leads_id: str, page: int, size: int) -> Dict[str, Any]:
        """Get paginated notes for a given `leads_id`"""
        query = (
            select(
                notes.c.id, 
                notes.c.leads_id, 
                notes.c.created_by_username, 
                notes.c.notes, 
                notes.c.time
            )
            .where(notes.c.leads_id == leads_id)
            .order_by(notes.c.time.desc())
            .limit(size)
            .offset((page - 1) * size)
        )

        lead_notes = await database.fetch_all(query)

        total_count_query = select(func.count()).where(notes.c.leads_id == leads_id)
        total_count = await database.fetch_val(total_count_query) 

        return {
            "total": total_count,
            "page": page,
            "size": size,
            "notes": [dict(row) for row in lead_notes], 
        }

    @staticmethod
    async def get_note_by_id(note_id: str, user_full_name: str) -> Dict[str, Any]:
        """Fetch a note by ID (ensuring user has permission)"""
        query = select(notes).where(
            notes.c.id == note_id, 
            notes.c.created_by_username == user_full_name
        )
        return await database.fetch_one(query)

    @staticmethod
    async def update_note(note_id: str, user_full_name: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a note (only if the logged-in user created it)"""
        query = (
            update(notes)
            .where(
                notes.c.id == note_id, 
                notes.c.created_by_username == user_full_name
            )
            .values(**update_data)
            .returning(notes)
        )
        return await database.fetch_one(query)

    @staticmethod
    async def delete_note(note_id: str, user_full_name: str) -> bool:
        """Delete a note (only if the logged-in user created it)"""
        # Check if note exists and user has permission
        note = await NotesRepository.get_note_by_id(note_id, user_full_name)
        if not note:
            return False
        
        query = delete(notes).where(notes.c.id == note_id)
        await database.execute(query)
        return True
    
    @staticmethod
    async def create_note(leads_id: str, user_full_name: str, note_text: str) -> Dict[str, Any]:
        """Create a new note for the logged-in user"""
        note_id = str(uuid.uuid4())
        query = (
            insert(notes)
            .values(
                id=note_id,
                leads_id=leads_id,
                created_by_username=user_full_name,
                notes=note_text,
            )
            .returning(
                notes.c.id, 
                notes.c.leads_id, 
                notes.c.created_by_username, 
                notes.c.notes, 
                notes.c.time
            )
        )
        result = await database.fetch_one(query)
        return dict(result) if result else None