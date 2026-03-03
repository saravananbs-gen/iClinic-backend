from fastapi import Request
from fastapi.responses import Response
from twilio.twiml.voice_response import Gather, VoiceResponse, Dial
import json
from dotenv import load_dotenv

from src.data.clients.redis import redis_client
from src.core.services.twilio_service import twilio_service
from src.core.services.agent_service import voice_agent
from src.constants.url import BASE_URL
from src.schemas.auth import CurrentUserSchema


load_dotenv()


async def initiate_call(to_number: str, user: CurrentUserSchema):
    call = twilio_service.make_call(
        to_number=to_number, callback_url=f"{BASE_URL}/voice/voice"
    )
    await redis_client.set(
        call.sid,
        json.dumps(
            {
                "user_id": user.user_id,
                "user_phone": user.user_phone,
                "user_email": user.user_email,
                "to_phone": to_number,
            }
        ),
        ex=3600,
    )
    return {"status": "Call initiated", "call_sid": call.sid}


async def twilio_entrypoint():
    response = VoiceResponse()

    response.say(
        "Hello! This is your desk assistant from Sarathy's clinic. "
        "How can I help you today?",
        voice="Polly.Joanna",
        language="en-US",
    )

    gather = Gather(
        input="speech",
        action="/voice/handle-speech",
        method="POST",
        timeout=5,
        speech_timeout="auto",
        speech_model="phone_call",
    )
    response.append(gather)

    response.say("Goodbye.")
    response.hangup()

    return Response(content=str(response), media_type="application/xml")


async def handle_speech(request: Request):
    form = await request.form()

    speech_result = form.get("SpeechResult", "").strip()
    call_sid = form.get("CallSid")

    response = VoiceResponse()

    if not speech_result:
        response.say("Thank you and have a great day!")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    user_data_raw = await redis_client.get(call_sid)

    if not user_data_raw:
        response.say("Session expired. Please call again.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    user_data = json.loads(user_data_raw)
    user_id = user_data["user_id"]
    user_phone = user_data["user_phone"]
    user_email = user_data["user_email"]
    to_phone = user_data["to_phone"]

    ai_text_reply = await voice_agent.generate_response(
        call_sid=call_sid,
        user_input=speech_result,
        user_id=user_id,
        user_phone=user_phone,
        user_email=user_email,
        to_phone=to_phone,
    )

    if ai_text_reply.lower() == "<TRANSFER_TO_HUMAN>".lower():
        response.say(
            "One moment, transferring you to a human assistant for immediate help."
        )
        dial = Dial()
        dial.number("+919629035281")
        response.append(dial)
    else:
        response.say(
            ai_text_reply,
            voice="Polly.Joanna",
            language="en-US",
        )

        gather = Gather(
            input="speech",
            action="/voice/handle-speech",
            method="POST",
            timeout=5,
            speech_timeout="auto",
            speech_model="phone_call",
        )
        response.append(gather)

        response.say("Thank you and have a great day!")
        response.hangup()

    return Response(content=str(response), media_type="application/xml")
