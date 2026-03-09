from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.Provider import Provider


async def create_provider(
    session: AsyncSession,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    specialization: str | None = None,
    notable_work: str | None = None,
    experience_years: int | None = None,
    qualification: str | None = None,
    consultation_fee: float | None = None,
    bio: str | None = None,
) -> Provider:
    provider = Provider(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        specialization=specialization,
        notable_work=notable_work,
        experience_years=experience_years,
        qualification=qualification,
        consultation_fee=consultation_fee,
        bio=bio,
    )
    session.add(provider)
    await session.flush()
    return provider


async def get_all(session: AsyncSession) -> Sequence[Provider]:
    result = await session.execute(
        select(Provider).order_by(Provider.created_at.desc())
    )
    return result.scalars().all()


async def get_by_id(session: AsyncSession, provider_id: str) -> Provider | None:
    return await session.get(Provider, provider_id)
