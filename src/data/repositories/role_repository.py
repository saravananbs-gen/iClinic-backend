from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.Role import Role


async def get_by_name(session: AsyncSession, name: str) -> Optional[Role]:
    result = await session.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()
