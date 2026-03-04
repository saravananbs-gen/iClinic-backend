from twilio.rest import Client

from src.config.settings import settings

ACCOUNT_SID = settings.TWILIO_ACCOUNT_SID
AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
TWILIO_PHONE = settings.TWILIO_PHONE_NUMBER

client = Client(ACCOUNT_SID, AUTH_TOKEN)


async def send_sms(to_phone: str, message: str):
    client.messages.create(body=message, from_=TWILIO_PHONE, to=to_phone)
