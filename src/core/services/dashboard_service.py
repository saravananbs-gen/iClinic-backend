from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.Appointment import Appointment
from src.data.models.postgres.Provider import Provider
from src.data.models.postgres.AvailabilitySlot import AvailabilitySlot
from src.data.models.postgres.AppointmentType import AppointmentType
from src.data.repositories import appointment_repository, user_repository
from src.schemas.dashboard import (
    AppointmentSummary,
    AvailabilitySlotInfo,
    DashboardAppointmentsResponse,
    DashboardProfileResponse,
    ProviderSummary,
    AppointmentTypeInfo,
)


def _compose_name(first: str | None, last: str | None) -> str | None:
    parts = [part for part in (first, last) if part]
    return " ".join(parts) if parts else None


def _map_provider(provider: Provider | None) -> ProviderSummary | None:
    if not provider:
        return None

    name = _compose_name(provider.first_name, provider.last_name)
    email = provider.user.email if provider.user else None
    phone = provider.user.phone if provider.user else None

    return ProviderSummary(
        id=provider.id,
        name=name,
        email=email,
        phone=phone,
        specialization=provider.specialization,
        qualification=provider.qualification,
        consultation_fee=float(provider.consultation_fee)
        if provider.consultation_fee is not None
        else None,
    )


def _map_slot(slot: AvailabilitySlot | None) -> AvailabilitySlotInfo | None:
    if not slot:
        return None

    return AvailabilitySlotInfo(
        id=slot.id,
        start_time=slot.start_time,
        end_time=slot.end_time,
        is_booked=slot.is_booked,
    )


def _map_appointment_type(
    appointment_type: AppointmentType | None,
) -> AppointmentTypeInfo | None:
    if not appointment_type:
        return None

    return AppointmentTypeInfo(
        id=appointment_type.id,
        name=appointment_type.name,
        description=appointment_type.description,
        duration_minutes=appointment_type.duration_minutes,
    )


def _map_appointment(appointment: Appointment, now_utc: datetime) -> AppointmentSummary:
    slot_info = _map_slot(appointment.slot)
    start_time = slot_info.start_time if slot_info else None
    if start_time:
        if start_time.tzinfo:
            comparable_start = start_time.astimezone(timezone.utc)
            comparable_now = now_utc
        else:
            comparable_start = start_time
            comparable_now = now_utc.replace(tzinfo=None)
        is_upcoming = comparable_start >= comparable_now
    else:
        is_upcoming = False

    return AppointmentSummary(
        id=appointment.id,
        status=appointment.status,
        channel=appointment.channel,
        notes=appointment.notes,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        is_upcoming=is_upcoming,
        provider=_map_provider(appointment.provider),
        slot=slot_info,
        appointment_type=_map_appointment_type(appointment.appointment_type),
    )


async def get_profile(session: AsyncSession, user_id: str) -> DashboardProfileResponse:
    user = await user_repository.get_by_id_with_profile(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    if user.patient:
        name = _compose_name(user.patient.first_name, user.patient.last_name)
    elif user.provider:
        name = _compose_name(user.provider.first_name, user.provider.last_name)
    else:
        name = None

    return DashboardProfileResponse(
        name=name or user.email,
        email=user.email,
        phone=user.phone,
    )


async def get_appointments(
    session: AsyncSession, user_id: str
) -> DashboardAppointmentsResponse:
    user = await user_repository.get_by_id_with_profile(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    if not user.patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found for user.",
        )

    appointments = await appointment_repository.get_for_patient(
        session, user.patient.id
    )
    now = datetime.now(timezone.utc)

    upcoming: list[AppointmentSummary] = []
    past: list[AppointmentSummary] = []

    for appointment in appointments:
        summary = _map_appointment(appointment, now)
        if summary.is_upcoming:
            upcoming.append(summary)
        else:
            past.append(summary)

    return DashboardAppointmentsResponse(upcoming=upcoming, past=past)
