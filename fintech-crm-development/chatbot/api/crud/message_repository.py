import sqlalchemy
from sqlalchemy import select,text
from fastapi import HTTPException

from api.db_utils import database, messages, templates
from api.schemas.message_schema import MessageBase


from sqlalchemy import select, outerjoin, text
from api.db_utils import contacts


async def create_message(message: MessageBase):
    # Dynamically include only the fields that have values
    values_to_insert = {
        'phone_number': message.phone_number,
        'message_text': message.message_text,
        'message_id': message.message_id,
        'message_type': message.message_type,
        'message_sender': message.message_sender,
        'timestamp': message.timestamp,
        'read':message.read,
    }

    if message.media_id:
        values_to_insert['media_id'] = message.media_id
    if message.latitude:
        values_to_insert['latitude'] = message.latitude
    if message.longitude:
        values_to_insert['longitude'] = message.longitude
    if message.variables:
        values_to_insert['variables'] = message.variables

    query = messages.insert().values(values_to_insert)
    await database.execute(query)


async def get_message_id(message_id: str):
    query = messages.select().where(message_id == messages.c.message_id)
    return await database.fetch_one(query=query)


async def input_template(template: str, payload):
    query = templates.insert().values(template_name=template, template_json=payload)
    await database.execute(query)


async def get_template(template: str):
    query = templates.select().filter(templates.c.template_name == template)
    row = await database.fetch_one(query=query)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": f"Request asked for template: [{template}]"},
        )
    return row




async def get_message_list(phone_number: str, message_id: int = None, limit: int = 100):
    query = select(messages, contacts.c.name).select_from(
        outerjoin(messages, contacts, contacts.c.phone_number == messages.c.phone_number)
    ).where(messages.c.phone_number == phone_number)

    if message_id is not None:
        query = query.where(messages.c.id < message_id)

    query = query.limit(limit).order_by(messages.c.timestamp.desc())
    result = await database.fetch_all(query=query)

    # Map the results to include `name` or `null` when not found
    return [
        {
            "id": row.id,
            "phone_number": row.phone_number,
            "message_text": row.message_text,
            "message_id": row.message_id,
            "message_type": row.message_type,
            "message_sender": row.message_sender,
            "timestamp": row.timestamp,
            "media_id": row.media_id,
            "latitude": row.latitude,
            "variables": row.variables,
            "longitude": row.longitude,
            "read": row.read,  # Include read status
            "name": row.name if row.name is not None else None
        }
        for row in result
    ]




async def get_last_admin_message(phone_number: str):
    query = messages.select().where(
        phone_number == messages.c.phone_number, messages.c.message_sender == "Admin"
    )

    query = query.limit(1).order_by(messages.c.timestamp.desc())
    return await database.fetch_one(query=query)



async def search_messages(keyword: str, phone_number: str = None, limit: int = 100):
    query = select(messages, contacts.c.name).select_from(
        outerjoin(messages, contacts, contacts.c.phone_number == messages.c.phone_number)
    ).where(messages.c.message_text.ilike(f"%{keyword}%"))

    # Filter by phone_number if provided
    if phone_number:
        query = query.where(messages.c.phone_number == phone_number)

    query = query.order_by(messages.c.timestamp.desc()).limit(limit)

    result = await database.fetch_all(query=query)

    # Map the results to include `name` or `null` when not found
    return [
        {
            "id": row.id,
            "phone_number": row.phone_number,
            "message_text": row.message_text,
            "message_id": row.message_id,
            "message_type": row.message_type,
            "message_sender": row.message_sender,
            "timestamp": row.timestamp,
            "media_id": row.media_id,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "read": row.read,  # Include read status
            "name": row.name if row.name is not None else None
        }
        for row in result
    ]




async def filter_messages(
    phone_number: str,
    start_time: int = None,
    end_time: int = None,
    attachments: bool = None,
    limit: int = 100
):
    query = select(messages, contacts.c.name).select_from(
        outerjoin(messages, contacts, contacts.c.phone_number == messages.c.phone_number)
    ).where(messages.c.phone_number == phone_number)

    if start_time:
        query = query.where(text("CAST(timestamp AS INTEGER) >= :start_time").bindparams(start_time=start_time))

    if end_time:
        query = query.where(text("CAST(timestamp AS INTEGER) <= :end_time").bindparams(end_time=end_time))

    if attachments is not None:
        query = query.where(messages.c.media_id.isnot(None) if attachments else messages.c.media_id.is_(None))

    query = query.order_by(messages.c.timestamp.desc()).limit(limit)

    result = await database.fetch_all(query=query)

    return [
        {
            "id": row.id,
            "phone_number": row.phone_number,
            "message_text": row.message_text,
            "message_id": row.message_id,
            "message_type": row.message_type,
            "message_sender": row.message_sender,
            "timestamp": row.timestamp,
            "media_id": row.media_id,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "read": row.read,  
            "name": row.name if row.name is not None else None
        }
        for row in result
    ]

async def update_message_read_status(message_id: str, read_status: bool):
    query = messages.update().where(messages.c.message_id == message_id).values(read=read_status)
    await database.execute(query)