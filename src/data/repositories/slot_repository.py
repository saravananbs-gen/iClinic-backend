from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.AvailabilitySlot import AvailabilitySlot


async def get_by_provider(
    session: AsyncSession, provider_id: str
) -> Sequence[AvailabilitySlot]:
    result = await session.execute(
        select(AvailabilitySlot)
        .where(AvailabilitySlot.provider_id == provider_id)
        .order_by(AvailabilitySlot.start_time)
    )
    return result.scalars().all()


async def get_by_id(session: AsyncSession, slot_id: str) -> AvailabilitySlot | None:
    return await session.get(AvailabilitySlot, slot_id)
