from fastapi import APIRouter, Depends, HTTPException, Query
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_database as get_async_db
from app.api.api_v1.deps import get_current_user
from app.models.notes import notes
from app.schemas.notes import NoteCreate,NoteUpdate, NoteResponse, PaginatedNotesResponse
from typing import List
from app.models.notes import notes
from app.repository.notes_repo import NotesRepository

router = APIRouter()

@router.get("/notes", response_model=dict)
async def get_notes(
    leads_id: str = Query(..., description="Lead ID to fetch notes"),
    page: int = Query(1, ge=1),
    size: int = Query(10, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    """Fetch all notes related to a specific `leads_id`"""
    return await NotesRepository.get_notes_paginated(leads_id, page, size)

# #  Update Note
# @router.put("/note/{note_id}", response_model=NoteResponse)
# async def update_note(
#     note_id: int,
#     note_update: NoteUpdate,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: dict = Depends(get_current_user),
# ):
#     existing_note = await NotesRepository.get_note_by_id(db, note_id, current_user.full_name)
#     if not existing_note:
#         raise HTTPException(status_code=404, detail="Note not found or unauthorized")

#     update_data = note_update.dict(exclude_unset=True)
#     if not update_data:
#         return existing_note  # No update provided

#     updated_note = await NotesRepository.update_note(db, note_id, current_user.full_name, update_data)
#     return updated_note

# #  Delete Note
# @router.delete("/note/{note_id}")
# async def delete_note(
#     note_id: int,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: dict = Depends(get_current_user),
# ):
#     success = await NotesRepository.delete_note(db, note_id, current_user.full_name)
#     if not success:
#         raise HTTPException(status_code=404, detail="Note not found or unauthorized")
#     return {"message": "Note deleted successfully"}



# modified create_note function
@router.post("/note", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    leads_id: str = Query(..., description="Lead ID to create note"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    # new_note = await NotesRepository.create_note(db, current_user.full_name,current_user.id ,note_data.notes)
    new_note=await NotesRepository.create_note(leads_id, current_user.full_name, note_data.notes)

    if not new_note:
        raise HTTPException(status_code=500, detail="Failed to create note")
    return new_note
