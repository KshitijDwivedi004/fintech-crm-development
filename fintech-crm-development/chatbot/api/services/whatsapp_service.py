import requests
import logging
from api.settings import settings
from fastapi import UploadFile, HTTPException
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from datetime import datetime, timedelta
import uuid
import os
import mimetypes

TOKEN = settings.TOKEN
WHATSAPP_API_URL = "https://graph.facebook.com/v22.0/"
logger = logging.getLogger(__name__)





async def upload_to_azure(file_content: bytes, media_file: UploadFile) -> tuple[str, str]:
    try:
        blob_service_client = BlobServiceClient.from_connection_string(settings.CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER_NAME)

        if not container_client.exists():
            container_client.create_container()

        content_type = media_file.content_type or mimetypes.guess_type(media_file.filename)[0] or "application/octet-stream"

        file_extension = os.path.splitext(media_file.filename)[-1].lower() or ".bin"
        blob_name = f"{uuid.uuid4()}{file_extension}"

        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(
            file_content,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )

        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=settings.AZURE_CONTAINER_NAME,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )

        return blob_name, f"https://{blob_service_client.account_name}.blob.core.windows.net/{settings.AZURE_CONTAINER_NAME}/{blob_name}?{sas_token}"
    
    except Exception as e:
        logger.error(f"Azure upload failed: {e}")
        raise

async def download_azure_media(media_id: str) -> tuple[bytes, str]:
    try:
        blob_service_client = BlobServiceClient.from_connection_string(settings.CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(
            container=settings.AZURE_CONTAINER_NAME,
            blob=media_id
        )

        stream = blob_client.download_blob()
        content = stream.readall()  
        properties = blob_client.get_blob_properties()

        return content, properties.content_settings.content_type
    except Exception as e:
        logger.error(f"Azure download failed: {e}")
        raise


def get_whatsapp_media_url(media_id: str):
    try:
        url = f"{WHATSAPP_API_URL}{media_id}/"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.get(url, headers=headers)
        logger.info(f"API Response: {response.status_code}, {response.text}")
        response.raise_for_status()  
        return response.json().get("url")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch media URL: {e}")
        raise


def download_whatsapp_media(media_url: str):
    """
    Download media content from the given URL.
    """
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(media_url, headers=headers)
    if response.status_code == 200:
        return response.content, response.headers.get("Content-Type")
    else:
        raise Exception(f"Failed to download media: {response.text}")


async def send_template_message(phone_number: str, template_name: str, variables: list[str], media_url:str, type:str):
    try:
        url = f"{WHATSAPP_API_URL}{settings.NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "en"
                },
                "components":[]
            }
        }
        if type == "IMAGE":

            head_component = {
                "type": "header",
                "parameters": [{"type": "image", "image": { "link":media_url}}]
            }
            data["template"]["components"].append(head_component)
        
        if type == "DOCUMENT":

            head_component = {
                "type": "header",
                "parameters": [{"type": "document", "document": { "link":media_url}}]
            }
            data["template"]["components"].append(head_component)
        
        if variables:
            body_component = {
                "type": "body",
                "parameters": [{"type": "text", "text": var} for var in variables]
            }
            data["template"]["components"].append(body_component)
        print(data)
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to send template message: {e}")
        raise

async def create_whatsapp_upload_session(file_name: str, file_length: int, file_type: str):
    try:
        url = f"{WHATSAPP_API_URL}{settings.APP_ID}/uploads?file_name={file_name}&file_length={file_length}&file_type={file_type}&access_token={TOKEN}"
        response = requests.post(url)
        response.raise_for_status()
        return response.json().get("id")
    except requests.RequestException as e:
        logger.error(f"Failed to create WhatsApp upload session: {e}")
        raise

async def upload_whatsapp_media(session_id: str, file_content: bytes, file_type: str):
    try:
        url = f"{WHATSAPP_API_URL}{session_id}&file_offset=0"
        headers = {
            "Authorization": f"OAuth {TOKEN}",
            "Content-Type": file_type
        }

        response = requests.post(url, headers=headers, data=file_content)
        response.raise_for_status()
        return response.json().get("h")  # WhatsApp returns a media ID
    except requests.RequestException as e:
        logger.error(f"Failed to upload media to WhatsApp: {e}")
        raise

async def fetch_whatsapp_templates(wa_name):
    try:
        url = f"{WHATSAPP_API_URL}{settings.WHATSAPP_BUSINESS_ID}/message_templates?name={wa_name}"
        print(url)
        headers = {
            "Authorization": f"Bearer {TOKEN}"
        }

        response = requests.get(url, headers=headers)
        print(response.json())
        response.raise_for_status()
        data = response.json().get("data", [])
        return data[0] if data else {}
    
    except requests.RequestException as e:
        logger.error(f"Failed to fetch WhatsApp templates: {e}")
        return {"error": "Failed to fetch templates"}

async def upload_template(templatedata):
    try:
        url = f"{WHATSAPP_API_URL}{settings.WHATSAPP_BUSINESS_ID}/message_templates"
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"  # Required for JSON data
        }

        # Convert templatedata to JSON
        response = requests.post(url, headers=headers, json=templatedata)

        print("Response Status Code:", response.status_code)
        print("Response Text:", response.text)  # Debugging

        if response.status_code != 200:
            error_message = response.json().get("error", {}).get("error_user_msg", "Unknown error occurred")
            raise HTTPException(status_code=response.status_code, detail=f"Template upload failed: {error_message}")

        return response.json()  # Return response data if successful
    except requests.RequestException as e:
        logger.error(f"Failed to Create WhatsApp template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")