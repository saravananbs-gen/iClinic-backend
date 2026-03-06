from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.AppointmentType import AppointmentType


async def get_all(session: AsyncSession) -> Sequence[AppointmentType]:
    result = await session.execute(
        select(AppointmentType).order_by(AppointmentType.name)
    )
    return result.scalars().all()


async def get_by_id(
    session: AsyncSession, appointment_type_id: str
) -> AppointmentType | None:
    return await session.get(AppointmentType, appointment_type_id)
