from fastapi import APIRouter, Request

from src.core.services.voice_service import (
    twilio_entrypoint,
    handle_speech,
    initiate_call,
)

router = APIRouter()


@router.get("/make-call")
async def make_call(to_number: str, user_id: str):
    return await initiate_call(to_number, user_id)


@router.post("/voice")
async def voice_entrypoint():
    return await twilio_entrypoint()


@router.post("/handle-speech")
async def handle(request: Request):
    return await handle_speech(request)
