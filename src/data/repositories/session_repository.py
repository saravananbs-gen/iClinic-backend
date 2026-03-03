from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.Session import Session


async def create_session(
    session: AsyncSession,
    *,
    user_id: str,
    jti: str,
    expires_at: datetime,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Session:
    db_session = Session(
        user_id=user_id,
        jti=jti,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(db_session)
    await session.flush()
    return db_session


async def get_active_by_jti(session: AsyncSession, jti: str) -> Optional[Session]:
    now = datetime.now()
    result = await session.execute(
        select(Session).where(
            Session.jti == jti, Session.is_revoked.is_(False), Session.expires_at > now
        )
    )
    return result.scalar_one_or_none()


async def revoke_session(session: AsyncSession, db_session: Session) -> None:
    db_session.is_revoked = True
    await session.flush()
