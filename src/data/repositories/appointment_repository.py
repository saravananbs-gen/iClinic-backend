from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.Appointment import Appointment
from src.data.models.postgres.Provider import Provider
from src.data.models.postgres.AvailabilitySlot import AvailabilitySlot


async def get_for_patient(
    session: AsyncSession, patient_id: str
) -> Sequence[Appointment]:
    stmt = (
        select(Appointment)
        .join(Appointment.slot)
        .where(Appointment.patient_id == patient_id)
        .options(
            selectinload(Appointment.provider).selectinload(Provider.user),
            selectinload(Appointment.slot),
            selectinload(Appointment.appointment_type),
        )
        .order_by(AvailabilitySlot.start_time.desc())
    )

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_for_provider(
    session: AsyncSession, provider_id: str
) -> Sequence[Appointment]:
    stmt = (
        select(Appointment)
        .join(Appointment.slot)
        .where(Appointment.provider_id == provider_id)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.provider),
            selectinload(Appointment.slot),
            selectinload(Appointment.appointment_type),
        )
        .order_by(AvailabilitySlot.start_time.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_all(session: AsyncSession) -> Sequence[Appointment]:
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.provider),
            selectinload(Appointment.slot),
            selectinload(Appointment.appointment_type),
        )
        .order_by(Appointment.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_by_id(session: AsyncSession, appointment_id: str) -> Appointment | None:
    stmt = (
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.provider),
            selectinload(Appointment.slot),
            selectinload(Appointment.appointment_type),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
