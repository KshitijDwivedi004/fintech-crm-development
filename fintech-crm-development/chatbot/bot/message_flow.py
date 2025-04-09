import datetime
import json
import logging
import time
from api.schemas.message_schema import MessageBase
from bot.ChatBotAi.chatBot import get_AI_response
from bot.whatsapp import obj_whatsapp
from bot.fuzzy_matching import check_fuzzy_match
from api.crud import message_repository
from api.calendly import send_put_request_with_token

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

_template_data = {}


async def get_template_data(template_name: str):
    """
    Loads the template data from the database if it is not already loaded,
    caching it in the _template_data dictionary."""
    if template_name not in _template_data:
        template_data = await message_repository.get_template(template_name)
        template_data = json.loads(template_data.template_json)

        _template_data[template_name] = template_data
    return _template_data[template_name]


async def chat_flow(template_name: str, number: str, input_message: str):
    """
    This function performs the chat flow by retrieving a template from the database
    based on the template_name, matching the user input_message to a corresponding
    element in the template, and sending a message to the user based on the type of
    element found.

    :param template_name: the name of the template to retrieve from the database
    :param number: the phone number of the user to send the message to
    :param input_message: the message sent by the user

    :return: a tuple containing the message to be sent to the user and the type of message
    """
    data = await get_template_data(template_name)
    # Initialize variables for the message and message type
    message = None
    message_type = None
    matching_elements = []

    # Loop through all elements in the template
    for element in data["elements"]:
        if element["triggering_message"] == input_message:
            matching_elements.append(element)

        # If no matching elements were found and the input message was a fuzzy match,
        # send the first interactive element from the template
        # else no matching elements were found and the input message was not a fuzzy match,
        # get an AI response and send it to the user
    if not matching_elements:
        if check_fuzzy_match(input_message):
            matching_elements.append(data["elements"][0])
        else:
            message_type = "AI_response"
            message = await get_AI_response(input_message)
            await obj_whatsapp.send_message(phone_num=number, text=message)

    for element in matching_elements:
        if element["type"] == "interactive":
            reply_markup = element.get("reply_markup", {})
            if "buttons" in reply_markup:
                message_type = "interactive"
                message = element.get("text", None)
                await obj_whatsapp.send_message(
                    phone_num=number,
                    text=message,
                    markup_type="buttons",
                    reply_markup=reply_markup,
                    header=element.get("header", None),
                    header_type=element.get("header_type", None),
                    footer=element.get("footer", None),
                )
            if "lists" in reply_markup:
                message_type = "interactive"
                message = element.get("text", None)
                await obj_whatsapp.send_message(
                    phone_num=number,
                    text=message,
                    markup_type="lists",
                    reply_markup=reply_markup,
                    header=element.get("header", None),
                    header_type=element.get("header_type", None),
                    footer=element.get("footer", None),
                )

        elif element["type"] == "message":
            message = element.get("text", None)
            message_type = "text"
            await obj_whatsapp.send_message(phone_num=number, text=message)

        elif element["type"] == "action":
            if element["action"] == "send_media_message":
                message = element.get("media_link", None)
                caption = element.get("caption", None)
                message_type = element.get("message_type", None)
                await obj_whatsapp.send_media_message(
                    number, message, caption, message_type
                )
            elif element["action"] == "schedule_appointment":
                response = send_put_request_with_token()
                if response:
                    message = response["resource"]["booking_url"]
                    message_type = "link"
                    await obj_whatsapp.send_message(phone_num=number, text=message)

            elif element["action"] == "send_template_message":
                message = element.get("template_name", None)
                message_type = "template"
                await obj_whatsapp.send_template_message(number, message)

            elif element["action"] == "send_location_message":
                latitude = (element.get("latitude", None),)
                longitude = (element.get("longitude", None),)
                location_name = (element.get("location_name", None),)
                message = element.get("location_address", None)
                message_type = "location"
                await obj_whatsapp.send_location_message(
                    number, latitude, longitude, location_name, message
                )

    return message, message_type


async def message_process(text: str, number: str):
    message_text, message_type = await chat_flow(
        template_name="CMA", number=number, input_message=text
    )

    if message_text and message_type:
        message_info = {
            "phone_number": number,
            "message_text": message_text,
            "message_id": "bot",
            "message_type": message_type,
            "message_sender": "bot",
            "timestamp": str(int(time.time())),
        }
        mess = MessageBase(**message_info)
        await message_repository.create_message(mess)
        return message_info
