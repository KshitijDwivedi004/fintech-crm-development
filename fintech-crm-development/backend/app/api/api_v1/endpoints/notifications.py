from fastapi import APIRouter
from app.repository.notification_repository import notification_repository

router = APIRouter()

@router.get("/notifications/unread")
async def get_unread_notifications():
    return await notification_repository.get_unread()

@router.post("/notifications/mark-all-as-read")
async def mark_all_as_read():
    await notification_repository.mark_all_as_read()
    return {"message": "All notifications marked as read"}