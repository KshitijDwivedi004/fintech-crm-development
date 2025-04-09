import re
import urllib.parse
import urllib.request

from app.core.config import settings


def extract_phone_number_and_country_code(input_string):
    """
    Extract phone number and country code from the given string
    """
    pattern = r"^(\d+)(\d{10})$"
    match = re.search(pattern, input_string)

    if match:
        country_code = match.group(1)
        phone_number = match.group(2)
        return phone_number, country_code
    else:
        return None, None


def send_OTP(numbers: str, otp: str):
    """
    Send OTP to the given phone number
    """
    message = f"""Welcome! 
Your one-time password is {otp}. Please do not share this with anyone.
Regards,
Zrokar
TECHDOME SOLUTIONS PRIVATE LIMITED"""
    data = urllib.parse.urlencode(
        {
            "apikey": settings.TEXTLOCAL_KEY,
            "numbers": f"91{numbers}",
            "message": message,
            "sender": settings.TEXTLOCAL_SENDER,
        }
    )
    data = data.encode("utf-8")

    request = urllib.request.Request(settings.TEXTLOCAL_URL + "?")
    f = urllib.request.urlopen(request, data)
    fr = f.read()
    return fr