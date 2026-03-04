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
