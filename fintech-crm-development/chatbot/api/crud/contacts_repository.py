from sqlalchemy import insert,select
from api.db_utils import database
from api.schemas.contacts_schema import ContactCreate
from api.db_utils import database, contacts
from api.db_utils import database, messages, templates
from api.schemas.message_schema import MessageBase
from sqlalchemy import select, func, and_, over, or_
from sqlalchemy.sql import text
from sqlalchemy import cast, TIMESTAMP, Numeric



async def create_contact(contact: ContactCreate):
    query = insert(contacts).values(
        phone_number=contact.phone_number,
        name=contact.name,
        email_id=contact.email_id,
    )
    await database.execute(query)



async def get_contacts(unnamed: bool = False, unread: bool = False):
    # Existing subqueries for latest_messages and unread_counts
    latest_messages = (
        select(
            messages.c.id,
            messages.c.phone_number,
            messages.c.message_text,
            messages.c.message_id,
            messages.c.message_type,
            messages.c.message_sender,
            messages.c.timestamp,
            messages.c.media_id,
            messages.c.latitude,
            messages.c.longitude,
            func.row_number().over(
                partition_by=messages.c.phone_number,
                order_by=messages.c.timestamp.desc()
            ).label("rn")
        )
    ).subquery()

    unread_counts = (
        select(
            messages.c.phone_number,
            func.count().label("unread_count")
        )
        .where(
            messages.c.message_sender == "user",
            messages.c.read == False
        )
        .group_by(messages.c.phone_number)
    ).subquery()
    
    query = (
        select(
            contacts.c.phone_number,
            contacts.c.name,
            contacts.c.email_id,
            contacts.c.created_at,
            latest_messages.c.id.label("message_id"),
            latest_messages.c.phone_number.label("message_phone_number"),
            latest_messages.c.message_text,
            latest_messages.c.message_id.label("message_message_id"),
            latest_messages.c.message_type,
            latest_messages.c.message_sender,
            latest_messages.c.timestamp,
            latest_messages.c.media_id,
            latest_messages.c.latitude,
            latest_messages.c.longitude,
            unread_counts.c.unread_count
        )
        .select_from(
            contacts.outerjoin(
                latest_messages,
                and_(
                    contacts.c.phone_number == latest_messages.c.phone_number,
                    latest_messages.c.rn == 1
                )
            ).outerjoin(
                unread_counts,
                contacts.c.phone_number == unread_counts.c.phone_number
            )
        )
    )
    
    conditions = []
    if unnamed:
        conditions.append(contacts.c.name.is_(None))
    if unread:
        conditions.append(func.coalesce(unread_counts.c.unread_count, 0) > 0)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(
    func.coalesce(
        func.to_timestamp(cast(latest_messages.c.timestamp, Numeric)),  
        cast(contacts.c.created_at, TIMESTAMP)                          
    ).desc(),
    contacts.c.created_at.desc()
)
    
    result = await database.fetch_all(query=query)
    
    contacts_response = []
    for row in result:
        has_message = row["message_id"] is not None
        unread_count = row["unread_count"] or 0
        
        message_data = {}
        if has_message:
            message_data = {
                "id": row["message_id"],
                "phone_number": row["message_phone_number"],
                "message_text": row["message_text"],
                "message_id": row["message_message_id"],
                "message_type": row["message_type"],
                "message_sender": row["message_sender"],
                "timestamp": row["timestamp"],
                "media_id": row["media_id"],
                "latitude": row["latitude"],
                "longitude": row["longitude"]
            }
        
        contact = {
            "phone_number": row["phone_number"],
            "name": row["name"],  
            "email_id": row["email_id"],
            "latest_message": message_data if has_message else None,
            "unread_user_messages_count": unread_count
        }
        contacts_response.append(contact)
    
    return contacts_response


async def search_contacts(keyword: str):
    # query = select(contacts).where(contacts.c.name.ilike(f"%{keyword}%"))  # Case-insensitive search
    query = select(contacts).where(
    or_(
        contacts.c.name.ilike(f"%{keyword}%"),
        contacts.c.phone_number.ilike(f"%{keyword}%"),
        contacts.c.email_id.ilike(f"%{keyword}%")
    )
    )
    
    return await database.fetch_all(query)

async def get_contact(phone_number: str):
    query = select(contacts).where(contacts.c.phone_number == phone_number)
    return await database.fetch_one(query)