import json
import logging
import re
import aiohttp


# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def headers(WA_TOKEN):
    return {"Content-Type": "application/json", "Authorization": f"Bearer {WA_TOKEN}"}


async def post_data(url, headers, data):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    response_text = await response.text()
                    return response_text
                else:
                    # Handle non-200 status codes
                    logging.error(f"Request failed with status code: {response.status}")
    except aiohttp.ClientError as e:
        # Handle aiohttp exceptions (e.g., connection errors, timeouts)
        logging.exception(f"Aiohttp error occurred: {e}")

async def message_text(
    url: str, token: str, phone_num: str, text: str, web_page_preview=True
):
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": phone_num,
            "recipient_type": "individual",
            "type": "text",
            "text": {"body": text, "preview_url": web_page_preview},
        }
    )
    headers_data = await headers(token)
    return await post_data(url, headers_data, payload)


async def message_template(url: str, token: str, phone_num: str, template_name: str):
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": phone_num,
            "recipient_type": "individual",
            "type": "template",
            "template": {"name": template_name, "language": {"code": "en_US"}},
        }
    )
    headers_data = await headers(token)
    return await post_data(url, headers_data, payload)


async def message_interactive(
    url: str,
    token: str,
    phone_num: str,
    text: str,
    markup_type: str = None,
    reply_markup: dict = None,
    header: str = None,
    header_type: str = "text",
    footer: str = None,
    web_page_preview=True,
):
    message_frame = {
        "messaging_product": "whatsapp",
        "to": phone_num,
        "recipient_type": "individual",
        "type": "interactive",
    }

    interactive_type = None
    interactive_action = None

    if markup_type == "buttons":
        buttons = reply_markup["buttons"]
        interactive_type = "button"
        interactive_action = {"buttons": []}
        for button in buttons:
            button_text = button["text"]
            reply_button = {
                "type": "reply",
                "reply": {
                    "id": f"option-{button_text}",
                    "title": button_text,
                },
            }
            interactive_action["buttons"].append(reply_button)
    elif markup_type == "lists":
        lists = reply_markup.get("lists", [])
        button_text = reply_markup.get("button_text", "")
        interactive_type = "list"
        interactive_action = {
            "button": button_text,
            "sections": [{"rows": []}]
        }
        for item in lists:
            list_text = item["text"]
            row = {
                "id": f"main-{list_text}",
                "title": list_text,
            }
            interactive_action["sections"][0]["rows"].append(row)

    if interactive_type and interactive_action:
        message_frame["interactive"] = {
            "type": interactive_type,
            "body": {"text": text},
            "action": interactive_action,
        }

    if header:
        if header_type == "text":
            message_frame["interactive"]["header"] = {
                "type": "text",
                "text": header,
            }
        elif header_type in ["image", "video", "document"]:
            if re.match(r"^((http[s]?://)|(www.))", header):
                header_type_object = {"link": header}
            else:
                header_type_object = {"id": header}
            message_frame["interactive"]["header"] = {
                "type": header_type,
                header_type: header_type_object,
            }

    if footer:
        message_frame["interactive"]["footer"] = {"text": footer}

    payload = json.dumps(message_frame)
    headers_data = await headers(token)
    return await post_data(url, headers_data, payload)


async def message_media(
    url: str,
    token: str,
    phone_num: str,
    media_path: str,
    caption: str = None,
    message_type: str = "image",
):
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": phone_num,
            "recipient_type": "individual",
            "type": message_type,
            message_type: {
                "link": media_path,
                "caption": caption,
            },
        }
    )
    headers_data = await headers(token)
    return await post_data(url, headers_data, payload)


async def message_location(
    url: str,
    token: str,
    phone_num: str,
    latitude: str,
    longitude: str,
    location_name: str,
    location_address: str,
):
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_num,
            "type": "location",
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "name": location_name,
                "address": location_address,
            },
        }
    )
    headers_data = await headers(token)
    return await post_data(url, headers_data, payload)
