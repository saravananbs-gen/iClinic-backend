from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.Appointment import Appointment
from src.data.repositories import (
    patient_repository,
    provider_repository,
    appointment_repository,
    slot_repository,
    appointment_type_repository,
)
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
from src.core.services.notification import send_appointment_notification
from src.observability.logging import get_logger

logger = get_logger(__name__)


async def list_patients(session: AsyncSession) -> list[PatientResponse]:
    patients = await patient_repository.get_all(session)
    return [PatientResponse.model_validate(p) for p in patients]


async def create_patient(
    session: AsyncSession, payload: CreatePatientRequest
) -> PatientResponse:
    existing = await patient_repository.get_by_phone(session, payload.phone)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A patient with this phone number already exists.",
        )

    patient = await patient_repository.create_patient(
        session,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        email=payload.email,
        dob=payload.dob,
        gender=payload.gender,
        blood_group=payload.blood_group,
        emergency_contact=payload.emergency_contact,
        medical_notes=payload.medical_notes,
        is_walk_in=True,
    )
    await session.commit()
    return PatientResponse.model_validate(patient)


async def list_providers(session: AsyncSession) -> list[ProviderResponse]:
    providers = await provider_repository.get_all(session)
    return [
        ProviderResponse.model_validate(
            {
                **p.__dict__,
                "consultation_fee": float(p.consultation_fee)
                if p.consultation_fee is not None
                else None,
            }
        )
        for p in providers
    ]


async def create_provider(
    session: AsyncSession, payload: CreateProviderRequest
) -> ProviderResponse:
    provider = await provider_repository.create_provider(
        session,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        email=payload.email,
        specialization=payload.specialization,
        notable_work=payload.notable_work,
        experience_years=payload.experience_years,
        qualification=payload.qualification,
        consultation_fee=payload.consultation_fee,
        bio=payload.bio,
    )
    await session.commit()
    return ProviderResponse.model_validate(provider)


async def list_provider_slots(
    session: AsyncSession, provider_id: str
) -> list[SlotResponse]:
    provider = await provider_repository.get_by_id(session, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found."
        )

    slots = await slot_repository.get_by_provider(session, provider_id)
    return [SlotResponse.model_validate(s) for s in slots]


async def list_appointment_types(
    session: AsyncSession,
) -> list[AppointmentTypeResponse]:
    types = await appointment_type_repository.get_all(session)
    return [AppointmentTypeResponse.model_validate(t) for t in types]


async def book_appointment(
    session: AsyncSession, payload: CreateAppointmentRequest
) -> AppointmentResponse:
    patient = await patient_repository.get_by_id(session, payload.patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found."
        )

    provider = await provider_repository.get_by_id(session, payload.provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found."
        )

    slot = await slot_repository.get_by_id(session, payload.slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found."
        )
    if slot.is_booked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This slot is already booked.",
        )
    if slot.provider_id != payload.provider_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot does not belong to the specified provider.",
        )

    appt_type = await appointment_type_repository.get_by_id(
        session, payload.appointment_type_id
    )
    if not appt_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment type not found.",
        )

    appointment = Appointment(
        patient_id=payload.patient_id,
        provider_id=payload.provider_id,
        slot_id=payload.slot_id,
        appointment_type_id=payload.appointment_type_id,
        channel=payload.channel,
        notes=payload.notes,
        status="confirmed",
    )
    session.add(appointment)

    slot.is_booked = True

    await session.commit()
    await session.refresh(appointment)

    try:
        patient_email = patient.email or (patient.user.email if patient.user else None)
        patient_phone = patient.phone or (patient.user.phone if patient.user else None)
        slot_time = f"{slot.start_time} - {slot.end_time}"

        await send_appointment_notification(
            action="booked",
            patient_email=patient_email,
            patient_phone=patient_phone,
            provider_name=f"{provider.first_name} {provider.last_name}",
            specialization=provider.specialization,
            slot_time=slot_time,
            appointment_type=appt_type.name,
        )
    except Exception:
        logger.error(
            "Booking notification failed",
            exc_info=True,
            extra={"extra_data": {"appointment_id": appointment.id}},
        )

    return AppointmentResponse.model_validate(appointment)


def _build_detail(appointment: Appointment) -> AppointmentDetailResponse:
    provider = appointment.provider
    return AppointmentDetailResponse(
        id=appointment.id,
        status=appointment.status,
        channel=appointment.channel,
        notes=appointment.notes,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        patient=PatientResponse.model_validate(appointment.patient)
        if appointment.patient
        else None,
        provider=ProviderResponse.model_validate(
            {
                **provider.__dict__,
                "consultation_fee": float(provider.consultation_fee)
                if provider.consultation_fee is not None
                else None,
            }
        )
        if provider
        else None,
        slot=SlotResponse.model_validate(appointment.slot)
        if appointment.slot
        else None,
        appointment_type=AppointmentTypeResponse.model_validate(
            appointment.appointment_type
        )
        if appointment.appointment_type
        else None,
    )


async def list_appointments(
    session: AsyncSession,
) -> list[AppointmentDetailResponse]:
    appointments = await appointment_repository.get_all(session)
    return [_build_detail(a) for a in appointments]


async def list_patient_appointments(
    session: AsyncSession, patient_id: str
) -> list[AppointmentDetailResponse]:
    patient = await patient_repository.get_by_id(session, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found."
        )

    appointments = await appointment_repository.get_for_patient(session, patient_id)
    return [_build_detail(a) for a in appointments]


async def list_provider_appointments(
    session: AsyncSession, provider_id: str
) -> list[AppointmentDetailResponse]:
    provider = await provider_repository.get_by_id(session, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found."
        )

    appointments = await appointment_repository.get_for_provider(session, provider_id)
    return [_build_detail(a) for a in appointments]


async def cancel_appointment(
    session: AsyncSession, appointment_id: str
) -> AppointmentDetailResponse:
    appointment = await appointment_repository.get_by_id(session, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    if appointment.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Appointment is already cancelled.",
        )

    appointment.status = "cancelled"

    slot = await slot_repository.get_by_id(session, appointment.slot_id)
    if slot:
        slot.is_booked = False

    await session.commit()
    await session.refresh(appointment)

    try:
        patient = appointment.patient
        provider = appointment.provider
        patient_email = (
            (patient.email or (patient.user.email if patient.user else None))
            if patient
            else None
        )
        patient_phone = (
            (patient.phone or (patient.user.phone if patient.user else None))
            if patient
            else None
        )
        slot_time = f"{slot.start_time} - {slot.end_time}" if slot else "N/A"

        await send_appointment_notification(
            action="cancelled",
            patient_email=patient_email,
            patient_phone=patient_phone,
            provider_name=f"{provider.first_name} {provider.last_name}"
            if provider
            else "N/A",
            specialization=provider.specialization if provider else None,
            slot_time=slot_time,
            appointment_type="Appointment",
        )
    except Exception:
        logger.error(
            "Cancellation notification failed",
            exc_info=True,
            extra={"extra_data": {"appointment_id": appointment_id}},
        )

    return _build_detail(appointment)
