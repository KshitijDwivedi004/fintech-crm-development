import logging

import razorpay
import requests

from api.settings import settings

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
client.set_app_details({"title": "ZEROKAR", "version": "1.0.0"})


def create_payment_link(name: str, email: str, contact: str, amount: int):
    try:
        payment_data = {
            "amount": amount,
            "currency": "INR",
            "description": "ZeroKar Payment Link",
            "customer": {
                "name": name,
                "email": email,
                "contact": f"+{contact}",
            },
            "notify": {
                "sms": True,
                "email": True,
            },
            "reminder_enable": True,
        }

        response = requests.post(
            settings.RAZORPAY_PAYMENT_LINK,
            json=payment_data,
            auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET),
            timeout=5,
        )

        if response.status_code == 200:
            return response.json()

    except Exception as e:
        logging.exception(f"Razorpay error occurred: {e}")
        return None
