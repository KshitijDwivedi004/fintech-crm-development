import json
import logging
import re
import time
import uuid
from datetime import datetime, timedelta
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response, Query, UploadFile, File, Form, status, Path
from starlette.middleware.cors import CORSMiddleware
from api import deps
from api.calendly import send_put_request_with_token
from api.crud import message_repository
from api.crud.razorpay_repository import razorpay_repo
from api.db_utils import database
from api.kafka import kafka_producer
from api.logger import logger
from api.razor_pay import client, create_payment_link
from api.schemas.message_schema import MessageBase
from api.schemas.razorpay_schema import RazorPayCreate
from api.settings import settings
from api.utilis import convert_datetime_to_timezone
from bot.message_flow import message_process
from bot.message_handler import extract_whatsapp_message
from bot.whatsapp import obj_whatsapp
from api.services.whatsapp_service import get_whatsapp_media_url, download_whatsapp_media
from confluent_kafka import KafkaException
from api.crud import contacts_repository
from api.schemas.contacts_schema import ContactCreate
from api.services.whatsapp_service import send_template_message, create_whatsapp_upload_session, upload_whatsapp_media, fetch_whatsapp_templates, upload_template
from api.schemas.message_schema import MessageReadUpdate,MessageRequest, SendTemplateRequest
from api.services.whatsapp_service import upload_to_azure, download_azure_media
from api.crud.reminder_repository import reminder_repo
from api.schemas.reminder_schema import ReminderCreate, Reminder
import asyncio
from api.services.whatsapp_service import upload_to_azure,download_azure_media
from api.crud.user_repository import user_repository
from api.schemas.user import UserCreateManual
from fastapi import APIRouter, HTTPException, status, Body
from api.schemas.template_schema import TemplateBase, Template, WhatsappTemplate
from api.crud.template_repository import template_repository
from datetime import datetime
import logging
from typing import Optional, List


app = FastAPI(
    title=settings.PROJECT_NAME,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def check_reminders():
    """
    Background task to check for pending reminders and send them to Kafka.
    """
    while True:
        try:
            pending = await reminder_repo.get_pending_reminders()
            for reminder in pending:
                reminder_msg = {
                    "type": "reminder",
                    "data": {
                        "id": reminder["id"],
                        "user_phone": reminder["user_phone"],
                        "message": reminder["message"],
                        "timestamp": str(datetime.now())
                    }
                }
                
                # Send reminder to Kafka
                kafka_producer.produce(
                    "whatsapp-bot",
                    json.dumps(reminder_msg).encode("utf-8")
                )
                logger.info(f"Reminder sent to Kafka: {reminder_msg}")
                
                await reminder_repo.mark_reminder_completed(reminder["id"])
        
        except Exception as e:
            logger.error(f"Reminder check failed: {str(e)}")
        
        await asyncio.sleep(60)  


@app.on_event("startup")
async def startup():
    """
    Startup event to connect to the database and start the reminder checker.
    """
    try:
        await database.connect()
        logger.info("Database connected successfully.")
        
        # Start the reminder checker as a background task
        asyncio.create_task(check_reminders())
        logger.info("Reminder checker started.")
    
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """
    Shutdown event to disconnect from the database.
    """
    try:
        await database.disconnect()
        logger.info("Database disconnected successfully.")
    
    except Exception as e:
        logger.error(f"Shutdown failed: {str(e)}")
        raise

# WhatsApp Webhook Verification Endpoint
@app.get("/webhook")
async def verify_token(request: Request):
    """
    Verify the WhatsApp webhook by confirming the token.
    Accepts hub.challenge and hub.verify_token query parameters.
    
    Returns:
        str: The challenge parameter if valid, HTTP 400 otherwise.
    """
    try:
        challenge = request.query_params.get("hub.challenge")
        token = request.query_params.get("hub.verify_token")

        if challenge is not None and token is not None and token == settings.WATOKEN:
            return Response(content=challenge, media_type="text/plain")
        else:
            return Response(status_code=400)
    except Exception:
        logger.exception("Webhook Verification failed")

# WhatsApp Incoming Message Handler
@app.post("/webhook")
async def received_message(request: Request):
    """
    Receive message from WhatsApp webhook.
    Process the message, save it to the database, and send it to the Kafka queue.
    
    Returns:
        Response: Indicates the message has been received.
    """
    try:
        body = await request.json()
        messageObject = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])

        if not messageObject:
            return Response(content="EVENT_RECEIVED", media_type="text/plain")

        messages = messageObject[0]
        data = await extract_whatsapp_message(messages)
        message_data = {
            "phone_number": data.number[2:],
            "message_text": data.text,
            "message_id": data.message_id,
            "message_type": data.message_type,
            "message_sender": "user",
            "timestamp": data.timestamp,
            "media_id": data.media_id,
            "latitude": data.latitude,
            "longitude": data.longitude,
        }
        message_send={
            "type":"message",
            "data":message_data,
        }
        message = MessageBase(**message_data)

        # Check for duplicate message
        if await message_repository.get_message_id(message.message_id):
            return Response(content="Message Already exists", media_type="text/plain")

        # Send to Kafka and save to DB
        message_data_str = json.dumps(message_send)
        try:
            kafka_producer.poll()
            kafka_producer.produce("whatsapp-bot", message_data_str.encode("utf-8"))
        except KafkaException as e:
            logging.error(f"Kafka error: {e}")
            return Response(content="Temporary server issue", media_type="text/plain")
        await message_repository.create_message(message)

        return Response(content="EVENT_RECEIVED", media_type="text/plain")

    except Exception as e:
        logger.exception(f"Whatsapp Webhook Verification failed: {e}")

# Media Download Endpoint
@app.get("/api/get-media/{media_id}")
async def get_media(media_id: str):
    """
    Fetch media from WhatsApp using the provided media ID.
    Media content and type are returned directly.
    
    Parameters:
        media_id (str): The ID of the media to fetch.
    
    Returns:
        Response: The media content with appropriate content-type, or an error message.
    """
    try:
        media_url = get_whatsapp_media_url(media_id)
        media_content, content_type = download_whatsapp_media(media_url)
        return Response(content=media_content, media_type=content_type)
    except Exception as e:
        return Response(content=str(e), status_code=500)

# Template Input Endpoint
@app.post(f"{settings.API_V1_STR}/input-template")
async def input_template(template_name: str, flow: dict):
    """
    Input a WhatsApp message template.
    
    Parameters:
        template_name (str): The name of the template.
        flow (dict): The template flow data.
    
    Returns:
        dict: A success message upon processing the template.
    """
    await message_repository.input_template(template_name, json.dumps(flow))
    return {"detail": "Templated processed successfully!"}

# Message List Retrieval Endpoint
@app.get(f"{settings.API_V1_STR}/get-list-messages")
async def get_list_mess(phone_number: str, message_id: int = None, limit: int = 100):
    """
    Retrieve a list of messages for a specific phone number.
    
    Parameters:
        phone_number (str): The phone number to query.
        message_id (int): Optional starting message ID for pagination.
        limit (int): The maximum number of messages to retrieve (default 100).
    
    Returns:
        list: A list of messages matching the query.
    """
    return await message_repository.get_message_list(phone_number, message_id, limit)

# Message Filtering Endpoint
@app.get("/messages/filter-messages")
async def get_filtered_messages(phone_number: str, start_time: int = Query(None), end_time: int = Query(None), attachments: bool = Query(None), limit: int = Query(100)):
    """
    Filter messages based on specified criteria.
    
    Parameters:
        phone_number (str): The phone number to filter.
        start_time (int): Start time in epoch seconds (optional).
        end_time (int): End time in epoch seconds (optional).
        attachments (bool): Whether to include messages with attachments (optional).
        limit (int): Maximum number of messages to return (optional).
    
    Returns:
        list: Filtered messages list.
    """
    return await message_repository.filter_messages(phone_number, start_time, end_time, attachments, limit)

# Message Search Endpoint
@app.get(f"{settings.API_V1_STR}/search_messages")
async def search_messages(keyword: str, phone_number: str = None, limit: int = 100):
    """
    Search messages containing a specific keyword.
    
    Parameters:
        keyword (str): The keyword to search in messages.
        phone_number (str, optional): Filter by phone number.
        limit (int, optional): Number of messages to retrieve. Default is 100.
    
    Returns:
        List of matching messages.
    """
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty.")
    messages = await message_repository.search_messages(keyword, phone_number, limit)
    return messages if messages else {"detail": "No messages found."}

@app.post(f"{settings.API_V1_STR}/add-contacts")
async def add_contact(contact: UserCreateManual):
    """
    Add a new contact to the users table.
    
    Parameters:
        contact (UserCreateManual): Contact data including phone number, name, and email.
    
    Returns:
        dict: The user data whether newly created or existing.
    """
    try:
        user = await user_repository.create_manual(contact)
        return user
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/get-all-contacts")
async def get_users_endpoint(unnamed: bool = False, unread: bool = False):
    """
    Retrieve all users with optional filters for unnamed and unread messages.
    
    Parameters:
        unnamed (bool): If True, filter users with no name.
        unread (bool): If True, filter users with unread messages.
        
    Returns:
        dict: A dictionary containing filtered users.
    """
    return {"users": await user_repository.get_users_with_messages(unnamed=unnamed, unread=unread)}


@app.post("/messages/set-read-status")
async def set_message_read_status(
    message_update: MessageReadUpdate
):
    await message_repository.update_message_read_status(
        message_update.message_id,
        message_update.read
    )
    return {"status": "success"}


@app.get("/search-contacts/{keyword}", summary="Search By User Name, Phone Number or Email ID")
async def search_users(
    keyword: str = Path(..., title="Search Keyword", description="Search by Name, Email, or Phone Number")
):
    """
    Search for users by User Name, Phone Number or Email ID containing the keyword.
    
    Parameters:
        keyword (str): The keyword to search for in user names.
    
    Returns:
        dict: A list of users matching the keyword.
    """
    return {"users": await user_repository.search_users(keyword)}

@app.post("/send-template-message")
async def send_template_message_endpoint(
    phone_number: str = Form(...),
    template_name: str = Form(...),
    variables: Optional[str] = Form(None),
    handle: Optional[str] = Form(None),
    type: str = Form(...) 
):
    """
    Send a template message to a specified phone number.
    
    Parameters:
        phone_number (str): The phone number to send the message to.
        template_name (str): The name of the template to send.
    
    Returns:
        dict: Details of the sent template message and API response.
    """
    try:
        variables_list = []
        if variables:
            variables_list = json.loads(variables)
        media_url = handle if handle else None  # Use file string if provided

        response = await send_template_message(
            "91" + phone_number, template_name, variables_list, media_url,type
        )
        message_id = response.get("messages", [{}])[0].get("id", "")
        print(f"Extracted message ID: {message_id}")

        message_data = {
            "phone_number": phone_number,
            "message_text": f"{template_name} template sent",
            "message_id": message_id,
            "message_type": "Template",
            "message_sender": "Admin",
            "timestamp": str(int(time.time())),
            "variables":variables_list
        }
        print(f"Message Data: {message_data}")

        # Send message data to Kafka
        message_send = {
            "type": "message",
            "data": message_data,
        }
        message_data_str = json.dumps(message_send)
        print(f"Kafka Message Data: {message_data_str}")

        try:
            kafka_producer.poll()
            kafka_producer.produce("whatsapp-bot", message_data_str.encode("utf-8"))
            print("Message sent to Kafka successfully")
        except KafkaException as e:
            logging.error(f"Kafka error: {e}")
            print(f"Kafka error: {e}")

        await message_repository.create_message(MessageBase(**message_data))
        print("Message saved to database")

        return {"detail": "Template message sent successfully!", "response": response}

    except Exception as e:
        logger.error(f"Failed to send template message: {e}")
        print(f"Exception occurred: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post(f"{settings.API_V1_STR}/send_message")
async def send_message(request: MessageRequest, background_tasks: BackgroundTasks):
    """
    Send a text message to a specified phone number.
    
    Parameters:
        phone_number (str): The phone number to send the message to.
        message (str): The text content of the message.
        background_tasks (BackgroundTasks): Handles asynchronous sending of the message.
    
    Returns:
        dict: Details of the sent message.
    """
    try:
        phone_number = request.phone_number
        message = request.message
        if not re.match(r"^\d{1,15}$", phone_number):
            raise HTTPException(status_code=400, detail="Invalid phone number!")
        background_tasks.add_task(obj_whatsapp.send_message, phone_num="91"+phone_number, text=message)
        
        message_data = {
            "phone_number": phone_number,
            "message_text": message,
            "message_id": str(uuid.uuid4()),
            "message_type": "text",
            "message_sender": "Admin",
            "timestamp": str(int(time.time())),
        }

        # Send message data to Kafka
        message_send = {
            "type": "message",
            "data": message_data,
        }
        message_data_str = json.dumps(message_send)

        try:
            kafka_producer.poll()
            kafka_producer.produce("whatsapp-bot", message_data_str.encode("utf-8"))
        except KafkaException as e:
            logging.error(f"Kafka error: {e}")
            
        await message_repository.create_message(MessageBase(**message_data))
        return message_data
    except Exception as e:
        logger.error(f"Send message failed" + str(e))
        raise HTTPException(status_code=400, detail="Message sent failed!")
    

@app.post(f"{settings.API_V1_STR}/send-media-message",
          status_code=status.HTTP_201_CREATED)
async def send_media_message(
    background_tasks: BackgroundTasks,
    phone_number: str = Form(...),
    media_file: UploadFile = File(...),
    caption: str = Form(None),
    message_type: str = Form("image"),
):
    try:
        if message_type not in ["image", "document", "audio", "video", "sticker"]:
            raise HTTPException(status_code=400, detail="Invalid media type")

        content = await media_file.read()
        blob_name, media_url = await upload_to_azure(content, media_file)
        print(media_url)
        background_tasks.add_task(
            obj_whatsapp.send_media_message,
            phone_num="91"+phone_number,
            media_path=media_url,
            caption=caption,
            message_type=message_type
        )

        message_data = {
            "phone_number": phone_number,
            "message_text": caption or "",
            "message_id": str(uuid.uuid4()),  # Temporary ID, will be updated
            "message_type": message_type,
            "message_sender": "Admin",
            "timestamp": str(int(time.time())),
            "media_id": blob_name,
        }

        message_send = {
            "type": "message",
            "data": message_data,
        }
        message_data_str = json.dumps(message_send)

        kafka_producer.produce("whatsapp-bot", message_data_str.encode("utf-8"))
        await message_repository.create_message(MessageBase(**message_data))
        return {"status": "success", "media_id": blob_name}

    except Exception as e:
        logger.error(f"Media message failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sent-media/{media_id}")
async def get_sent_media(media_id: str):
    try:
        content, content_type = await download_azure_media(media_id)
        return Response(content=content, media_type=content_type)
    except Exception as e:
        logger.error(f"Media retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail="Media not found or expired"
        )

@app.post("/set-reminder", response_model=Reminder)
async def set_reminder(reminder: ReminderCreate):
    """
    Create a new reminder for a user.
    
    Parameters:
        reminder (ReminderCreate): JSON body containing user_phone, reminder_time, and message.
    
    Returns:
        Reminder: The created reminder with all details.
    """
    created_reminder = await reminder_repo.create_reminder(reminder)
    return created_reminder

@app.get("/get-reminders")
async def get_reminder(phone_number:str):

    reminders=await reminder_repo.get_reminders(phone_number)
    return reminders


@app.post("/add-template", status_code=status.HTTP_201_CREATED)
async def add_template(template_data:WhatsappTemplate):
    """Add a new message template"""

    def remove_null_values(obj):
        if isinstance(obj, dict):
            return {k: remove_null_values(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [remove_null_values(v) for v in obj]
        return obj
    try:
        wa_name = str(uuid.uuid4())
        wa_name = wa_name.replace("-", "_")
        template_dict = {
            "name": template_data.name,
            "wa_name": wa_name,  # Generate unique WA name
            "category": template_data.category,
            "status": "DRAFT"  # Default value
        }
        await template_repository.create_template(TemplateBase(**template_dict))
        template_data.name = wa_name
        template_data.category = "MARKETING"
        cleaned_template = remove_null_values(template_data.dict())
        print(cleaned_template)
        return await upload_template(cleaned_template)

    except Exception as e:
        logger.error(f"Template creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Template creation failed")


@app.get("/get-all-templates")
async def get_all_templates():
    templates = await template_repository.get_all_templates()
    result = []

    async def fetch_and_update(template):
        if template.status in ["DRAFT", "PENDING"]:
            wa_response = await fetch_whatsapp_templates(template.wa_name)
            if wa_response:
                updated_status = wa_response.get("status", template.status)
                updated_structure = wa_response
                await template_repository.update_template_status_and_structure(
                    template.wa_name, updated_status, updated_structure
                )
                template.status = updated_status
                template.structure = updated_structure
        return template

    # Execute all fetches in parallel
    updated_templates = await asyncio.gather(*[fetch_and_update(template) for template in templates])

    return updated_templates


@app.put("/update-template-status/{template_id}", response_model=Template)
async def update_template_status(
    template_id: int, 
    status_data: dict = Body(..., example={"status": "active"})
):
    """Update template status"""
    try:
        new_status = status_data.get('status')
        if not new_status:
            raise HTTPException(status_code=400, detail="Status field required")
            
        return await template_repository.update_template_status(template_id, new_status)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Status update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Status update failed")

# Lead Information Retrieval Endpoint
# @app.get("/get-lead-info")
# async def get_lead_info(phone_number: str) -> dict:
#     """
#     Fetch lead information from contacts and users tables.
    
#     Parameters:
#         phone_number (str): The phone number associated with the lead.
    
#     Returns:
#         dict: User data if found, or a message indicating the lead isn't added.
#     """
#     contact = await contacts_repository.get_contact(phone_number)
#     if not contact:
#         raise HTTPException(status_code=404, detail="Contact not found")
#     user = await users_repository.get_user_by_phone_number(phone_number)
#     return user if user else {"message": "Lead not added yet"}

@app.post("/upload-template-media-to-whatsapp")
async def upload_template_media(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        session_id = await create_whatsapp_upload_session(file.filename, len(file_content), file.content_type)

        # Call WhatsApp media upload function
        media_handle = await upload_whatsapp_media(
            session_id,  # Replace with actual session logic if needed
            file_content,
            file_type=file.content_type  # Extract content type
        )
        return {"media_handle": media_handle}
    except Exception as e:
        return {"error": str(e)}
@app.post("/upload-template-media-to-azure")
async def upload_template_media_to_azure(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        blob_name, media_url = await upload_to_azure(file_content, file)
        return {"media_handle": media_url}
    except Exception as e:
        return {"error": str(e)}