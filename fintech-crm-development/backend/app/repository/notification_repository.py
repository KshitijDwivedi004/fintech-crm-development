from sqlalchemy import select, update
from app.db.session import database
from app.models import notifications

class NotificationRepository:
    async def create(self, notification_data):
        query = notifications.insert().values(
            type=notification_data["type"],
            formatted_data=notification_data,
            original_data=notification_data["original_data"],
            read_status=False
        )
        return await database.execute(query)

    async def get_unread(self):
        query = notifications.select().where(notifications.c.read_status == False)
        return await database.fetch_all(query)

    async def mark_all_as_read(self):
        query = (
            update(notifications)
            .values(read_status=True)
        )
        return await database.execute(query)

notification_repository = NotificationRepository()