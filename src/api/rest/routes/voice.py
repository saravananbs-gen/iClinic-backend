from fastapi import APIRouter, Request, Depends

from src.schemas.auth import CurrentUserSchema
from src.api.rest.dependencies import require_patient
from src.core.services.voice_service import (
    twilio_entrypoint,
    handle_speech,
    initiate_call,
)

router = APIRouter()


@router.get("/make-call")
async def make_call(
    to_number: str, user: CurrentUserSchema = Depends(require_patient)
):
    return await initiate_call(to_number=to_number, user=user)


@router.post("/voice")
async def voice_entrypoint():
    return await twilio_entrypoint()


@router.post("/handle-speech")
async def handle(request: Request):
    return await handle_speech(request)
