from fastapi import HTTPException, Request, status
from fastapi.responses import Response
from datetime import datetime, timedelta
from uuid import uuid4
import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.data.models.postgres.User import User
from src.data.repositories import session_repository
from src.constants.auth import (
    REFRESH_COOKIE_HTTPONLY,
    REFRESH_COOKIE_MAX_AGE_BUFFER_SECONDS,
    REFRESH_COOKIE_PATH,
)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age = max(
        (settings.REFRESH_TOKEN_EXPIRES_MINUTES * 60)
        - REFRESH_COOKIE_MAX_AGE_BUFFER_SECONDS,
        0,
    )
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        httponly=REFRESH_COOKIE_HTTPONLY,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=REFRESH_COOKIE_PATH,
    )


def _require_refresh_cookie(request: Request) -> str:
    token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token.",
        )
    return token


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_access_token(user: User, jti: str, role: str) -> str:
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MINUTES)
    payload = {
        "user_id": user.id,
        "user_phonenumber": user.phone,
        "user_email": user.email,
        "role": role,
        "token_type": "access",
        "jti": jti,
        "exp": datetime.now() + expires_delta,
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def _create_refresh_token(user: User, jti: str, role: str) -> str:
    expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRES_MINUTES)
    payload = {
        "user_id": user.id,
        "user_phonenumber": user.phone,
        "user_email": user.email,
        "role": role,
        "token_type": "refresh",
        "jti": jti,
        "exp": datetime.now() + expires_delta,
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def _decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        ) from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        ) from exc

    if payload.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )

    return payload


async def _issue_tokens(
    session: AsyncSession,
    user: User,
    role: str,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[str, str]:
    jti = str(uuid4())
    refresh_expires_at = datetime.now() + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRES_MINUTES
    )

    await session_repository.create_session(
        session,
        user_id=user.id,
        jti=jti,
        expires_at=refresh_expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    access_token = _create_access_token(user, jti, role)
    refresh_token = _create_refresh_token(user, jti, role)
    return access_token, refresh_token
