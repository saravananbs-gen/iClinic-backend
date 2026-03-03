from twilio.rest import Client

from src.config.settings import settings


class TwilioService:
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )

    def make_call(self, to_number: str, callback_url: str):
        return self.client.calls.create(
            to=to_number,
            from_=settings.TWILIO_PHONE_NUMBER,
            url=callback_url
        )

twilio_service = TwilioService()