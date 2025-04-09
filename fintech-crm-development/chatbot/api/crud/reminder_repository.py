from sqlalchemy import select, update
from datetime import datetime
from api.db_utils import database, reminders
from api.schemas.reminder_schema import ReminderCreate,Reminder
from datetime import timezone

class ReminderRepository:
    async def create_reminder(self, reminder: ReminderCreate):
    # Convert reminder_time to UTC naive datetime if necessary
        if reminder.reminder_time.tzinfo:
            reminder_time_naive = reminder.reminder_time.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            reminder_time_naive = reminder.reminder_time

        # Include status="pending" in the insert
        query = reminders.insert().values(
            user_phone=reminder.user_phone,
            reminder_time=reminder_time_naive,
            message=reminder.message,
            status="pending"  # Explicitly set status here
        )
        reminder_id = await database.execute(query)
        
        # Fetch the inserted reminder to return full data
        query = select([reminders]).where(reminders.c.id == reminder_id)
        result = await database.fetch_one(query)
        return result

    async def get_pending_reminders(self):
        current_time = datetime.now()
        query = select([reminders]).where(
            (reminders.c.reminder_time <= current_time) &
            (reminders.c.status == "pending")
        )
        return await database.fetch_all(query)

    async def mark_reminder_completed(self, reminder_id: int):
        query = update(reminders).where(reminders.c.id == reminder_id).values(status="completed")
        await database.execute(query)

    async def get_reminders(self,phone_number:str):
        query=select([reminders]).where(
            reminders.c.user_phone == phone_number
        )
        return await database.fetch_all(query)

reminder_repo = ReminderRepository()