from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.User import User


async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_phone(session: AsyncSession, phone: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, user_id: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_id_with_profile(session: AsyncSession, user_id: str) -> Optional[User]:
    result = await session.execute(
        select(User)
        .options(selectinload(User.patient), selectinload(User.provider))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_by_email_or_phone(
    session: AsyncSession, email: str | None = None, phone: str | None = None
) -> Optional[User]:
    if email and phone:
        result = await session.execute(
            select(User).where((User.email == email) & (User.phone == phone))
        )
    elif email:
        result = await session.execute(select(User).where(User.email == email))
    elif phone:
        result = await session.execute(select(User).where(User.phone == phone))
    else:
        return None

    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    *,
    role_id: str,
    email: str,
    phone: str,
    password_hash: str,
) -> User:
    user = User(
        role_id=role_id,
        email=email,
        phone=phone,
        password_hash=password_hash,
    )
    session.add(user)
    await session.flush()
    return user
