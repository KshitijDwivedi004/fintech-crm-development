import logging
from collections import namedtuple

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

class MessageData:
    def __init__(self, text, number, message_id, message_type, timestamp, media_id=None, latitude=None, longitude=None):
        self.text = text
        self.number = number
        self.message_id = message_id
        self.message_type = message_type
        self.timestamp = timestamp
        self.media_id = media_id
        self.latitude = latitude
        self.longitude = longitude

async def extract_whatsapp_message(messages):
    """
    Extracts relevant data from a WhatsApp Webhook message.
    Supports text, interactive buttons, images, videos, documents, audio, and location messages.
    """
    text = ""
    media_id = None
    latitude = None
    longitude = None
    
    number = messages["from"]
    timestamp = messages["timestamp"]
    mess_id = messages["id"]
    typeMessage = messages["type"]

    # Handle Text Messages
    if typeMessage == "text":
        text = messages.get("text", {}).get("body", "")

    # Handle Interactive Messages (Button & List Reply)
    elif typeMessage == "interactive":
        interactiveObject = messages["interactive"]
        typeInteractive = interactiveObject["type"]
        if typeInteractive == "button_reply":
            text = interactiveObject["button_reply"]["title"]
        elif typeInteractive == "list_reply":
            text = interactiveObject["list_reply"]["title"]

    # Handle Media Messages (Images, Videos, Audio, Documents)
    elif typeMessage in ["image", "video", "audio", "document"]:
        media_id = messages.get(typeMessage, {}).get("id", None)
        logging.info(f"Received {typeMessage} with media_id: {media_id}")

    # Handle Location Messages
    elif typeMessage == "location":
        latitude = messages.get("location", {}).get("latitude", None)
        longitude = messages.get("location", {}).get("longitude", None)
        text = f"Location: {latitude}, {longitude}"
        logging.info(f"Received location: {latitude}, {longitude}")

    else:
        logging.warning(f"Unsupported message type: {typeMessage}")

    return MessageData(text, number, mess_id, typeMessage, timestamp, media_id, latitude, longitude)


