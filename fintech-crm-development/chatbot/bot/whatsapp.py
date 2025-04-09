from bot.message import (
    message_text,
    message_template,
    message_interactive,
    message_media,
    message_location,
)
from dotenv import load_dotenv
import os

load_dotenv()


class Whatsapp:
    version_number = 22.0

    def __init__(self, number_id: int, token: str) -> None:
        """This is the main Whatsapp class. Use it to initialize your bot
        Args:
            id: Your phone number id provided by WhatsApp cloud
            token : Your token provided by WhatsApp cloud"""
        self.id = number_id
        self.token = token
        self.base_url = (
            f"https://graph.facebook.com/v{str(self.version_number)}/{str(self.id)}"
        )
        self.msg_url = self.base_url + "/messages"
        self.media_url = self.base_url + "/media"

    async def send_message(
        self,
        phone_num: str,
        text: str,
        markup_type: str = None,
        reply_markup: dict = None,
        header: str = None,
        header_type: str = "text",
        footer: str = None,
        web_page_preview=True,
    ):
        """Sends text message
        Args:
            phone_num:(int) Recipeint's phone number
            text:(str) The text to be sent
            web_page_preview:(bool),optional. Turn web page preview of links on/off
        """
        if reply_markup:
            return await message_interactive(
                self.msg_url,
                self.token,
                phone_num,
                text,
                markup_type=markup_type,
                reply_markup=reply_markup,
                header=header,
                header_type=header_type,
                footer=footer,
                web_page_preview=web_page_preview,
            )
        else:
            return await message_text(
                self.msg_url,
                self.token,
                phone_num,
                text,
                web_page_preview=web_page_preview,
            )

    async def send_template_message(self, phone_num: str, template_name: str):
        """Sends preregistered template message"""
        return await message_template(self.msg_url, self.token, phone_num, template_name)

    async def send_media_message(
        self,
        phone_num: str,
        media_path: str,
        caption: str = None,
        message_type: str = "image",
    ):
        """Sends media message which may include audio, document, image, sticker, or video
        paths starting with http(s):// or www. will be treated as link"""
        return await message_media(
            self.msg_url, self.token, phone_num, media_path, caption, message_type
        )

    async def send_location_message(
        self,
        phone_num: str,
        latitude: str,
        longitude: str,
        location_name: str,
        location_address: str,
    ):
        """Send location based on args provided"""
        return await message_location(
            self.msg_url,
            self.token,
            phone_num,
            latitude,
            longitude,
            location_name,
            location_address,
        )


NUMBER_ID = os.getenv("NUMBER_ID")
TOKEN = os.getenv("TOKEN")

obj_whatsapp = Whatsapp(number_id=NUMBER_ID, token=TOKEN)