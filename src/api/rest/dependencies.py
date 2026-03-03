from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from src.config.settings import settings
from src.schemas.auth import CurrentUserSchema


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/oauth")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUserSchema:
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

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return CurrentUserSchema(
            user_id=user_id,
            user_phone=user_phone,
            user_email=user_email,
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
