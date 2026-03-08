from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.constants.auth import ROLE_PATIENT, ROLE_FRONTDESK
from src.data.clients.postgres import get_async_session
from src.data.repositories import session_repository
from src.schemas.auth import CurrentUserSchema


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/oauth")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> CurrentUserSchema:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("token_type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("user_id")
        user_phone = payload.get("user_phonenumber")
        user_email = payload.get("user_email")
        role = payload.get("role", "")
        jti = payload.get("jti")

        if not user_id or not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        active_session = await session_repository.get_active_by_jti(session, jti)
        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or revoked",
            )

        return CurrentUserSchema(
            user_id=user_id,
            user_phone=user_phone,
            user_email=user_email,
            role=role,
        )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def require_role(*allowed_roles: str):

    async def _check(
        current_user: CurrentUserSchema = Depends(get_current_user),
    ) -> CurrentUserSchema:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return current_user

    return _check


require_patient = require_role(ROLE_PATIENT)
require_frontdesk = require_role(ROLE_FRONTDESK)
