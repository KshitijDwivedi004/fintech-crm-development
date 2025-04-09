import sqlalchemy
from fastapi import HTTPException

from api.db_utils import database, razorpay
from api.schemas.razorpay_schema import RazorPayCreate


class RazorPayRepository:
    async def create(self, obj_in: RazorPayCreate):
        query = razorpay.insert().values(
            event_id=obj_in.event_id,
            user_phone=obj_in.user_phone,
            user_email=obj_in.user_email,
            order_id=obj_in.order_id,
            payment_id=obj_in.payment_id,
            amount=obj_in.amount,
            currency=obj_in.currency,
            status=obj_in.status,
            method=obj_in.method,
            error_code=obj_in.error_code,
            error_source=obj_in.error_source,
            error_description=obj_in.error_description,
            created_at=obj_in.created_at,
        )
        await database.execute(query)

    async def get_event_id(self, event_id: str):
        query = razorpay.select().where(event_id == razorpay.c.event_id)
        return await database.fetch_one(query=query)


razorpay_repo = RazorPayRepository()
