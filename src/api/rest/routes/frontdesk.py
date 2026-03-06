from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services import frontdesk_service
from src.data.clients.postgres import get_async_session
from src.schemas.frontdesk import (
    CreatePatientRequest,
    CreateProviderRequest,
    CreateAppointmentRequest,
    PatientResponse,
    ProviderResponse,
    SlotResponse,
    AppointmentTypeResponse,
    AppointmentResponse,
    AppointmentDetailResponse,
)

router = APIRouter()


@router.get("/patients", response_model=list[PatientResponse])
async def list_patients(
    session: AsyncSession = Depends(get_async_session),
):
    return await frontdesk_service.list_patients(session)


@router.post("/patient", response_model=PatientResponse, status_code=201)
async def create_patient(
    payload: CreatePatientRequest,
    session: AsyncSession = Depends(get_async_session),
):
    return await frontdesk_service.create_patient(session, payload)


@router.get("/providers", response_model=list[ProviderResponse])
async def list_providers(
    session: AsyncSession = Depends(get_async_session),
):
    return await frontdesk_service.list_providers(session)


@router.post("/provider", response_model=ProviderResponse, status_code=201)
async def create_provider(
    payload: CreateProviderRequest,
    session: AsyncSession = Depends(get_async_session),
):
    return await frontdesk_service.create_provider(session, payload)


@router.get("/providers/{provider_id}/slots", response_model=list[SlotResponse])
async def list_provider_slots(
    provider_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    return await frontdesk_service.list_provider_slots(session, provider_id)


@router.get("/appointment-types", response_model=list[AppointmentTypeResponse])
async def list_appointment_types(
    session: AsyncSession = Depends(get_async_session),
):
    return await frontdesk_service.list_appointment_types(session)


@router.post("/appointments", response_model=AppointmentResponse, status_code=201)
async def book_appointment(
    payload: CreateAppointmentRequest,
    session: AsyncSession = Depends(get_async_session),
):
    return await frontdesk_service.book_appointment(session, payload)


@router.get("/appointments", response_model=list[AppointmentDetailResponse])
async def list_appointments(
    session: AsyncSession = Depends(get_async_session),
):
    return await frontdesk_service.list_appointments(session)


@router.get(
    "/patient/{patient_id}/appointments",
    response_model=list[AppointmentDetailResponse],
)
async def list_patient_appointments(
    patient_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    return await frontdesk_service.list_patient_appointments(session, patient_id)


@router.get(
    "/provider/{provider_id}/appointments",
    response_model=list[AppointmentDetailResponse],
)
async def list_provider_appointments(
    provider_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    return await frontdesk_service.list_provider_appointments(session, provider_id)


@router.patch(
    "/appointments/{appointment_id}/cancel",
    response_model=AppointmentDetailResponse,
)
async def cancel_appointment(
    appointment_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    return await frontdesk_service.cancel_appointment(session, appointment_id)
