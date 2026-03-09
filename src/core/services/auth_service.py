from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants.auth import ROLE_PATIENT, ROLE_FRONTDESK
from src.data.repositories import (
    patient_repository,
    role_repository,
    session_repository,
    user_repository,
)
from src.schemas.auth import LoginRequest, SignupRequest
from src.utils.auth import (
    _hash_password,
    _issue_tokens,
    _verify_password,
    _decode_refresh_token,
)
from src.observability.logging import get_logger

logger = get_logger(__name__)

ALLOWED_LOGIN_ROLES = {ROLE_PATIENT, ROLE_FRONTDESK}


async def signup(
    session: AsyncSession,
    payload: SignupRequest,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[str, str, str]:
    if await user_repository.get_by_email(session, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    if await user_repository.get_by_phone(session, payload.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone already registered.",
        )

    role = await role_repository.get_by_name(session, ROLE_PATIENT)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patient role not configured.",
        )

    password_hash = _hash_password(payload.password)

    user = await user_repository.create_user(
        session,
        role_id=role.id,
        email=payload.email,
        phone=payload.phone,
        password_hash=password_hash,
    )

    await patient_repository.create_patient(
        session,
        user_id=user.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        email=payload.email,
    )

    access_token, refresh_token = await _issue_tokens(
        session,
        user,
        ROLE_PATIENT,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await session.commit()
    logger.info(
        "User signed up",
        extra={"extra_data": {"user_id": str(user.id), "email": payload.email}},
    )
    return access_token, refresh_token, ROLE_PATIENT


async def login(
    session: AsyncSession,
    payload: LoginRequest,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[str, str, str]:
    try:
        payload.validate_identifier()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    user = await user_repository.get_by_email_or_phone(
        session, email=payload.email, phone=payload.phone
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    if not user.role or user.role.name not in ALLOWED_LOGIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account role is not permitted to log in.",
        )

    if not _verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    role_name: str = user.role.name

    access_token, refresh_token = await _issue_tokens(
        session,
        user,
        role_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await session.commit()
    logger.info(
        "User logged in",
        extra={"extra_data": {"user_id": str(user.id), "role": role_name}},
    )
    return access_token, refresh_token, role_name


async def refresh(
    session: AsyncSession,
    refresh_token: str,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[str, str, str]:
    payload = _decode_refresh_token(refresh_token)
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    db_session = await session_repository.get_active_by_jti(session, jti)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session.",
        )

    await session_repository.revoke_session(session, db_session)

    user = await user_repository.get_by_id(session, payload.get("user_id"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session.",
        )

    role_name = user.role.name if user.role else payload.get("role", "")

    access_token, new_refresh_token = await _issue_tokens(
        session,
        user,
        role_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await session.commit()
    return access_token, new_refresh_token, role_name


async def logout(session: AsyncSession, refresh_token: str) -> None:
    payload = _decode_refresh_token(refresh_token)
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    db_session = await session_repository.get_active_by_jti(session, jti)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    await session_repository.revoke_session(session, db_session)
    await session.commit()
