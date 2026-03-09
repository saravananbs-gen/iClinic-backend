from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from src.config.settings import settings
from src.constants.auth import REFRESH_COOKIE_PATH
from src.core.services import auth_service
from src.data.clients.postgres import get_async_session
from src.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from src.utils.auth import _require_refresh_cookie, _set_refresh_cookie

router = APIRouter(tags=["Auth"])


@router.post("/login/oauth")
async def login_oauth(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    """
    This endpoint is ONLY for Swagger OAuth2 compatibility.
    """
    payload = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )

    access_token, refresh_token, role = await auth_service.login(
        session,
        payload,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    _set_refresh_cookie(response, refresh_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role,
    }


@router.post("/signup", response_model=TokenResponse)
async def signup(
    payload: SignupRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    access_token, refresh_token, role = await auth_service.signup(
        session,
        payload,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token, role=role)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    access_token, refresh_token, role = await auth_service.login(
        session,
        payload,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token, role=role)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    refresh_token_value = _require_refresh_cookie(request)

    access_token, new_refresh_token, role = await auth_service.refresh(
        session,
        refresh_token_value,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _set_refresh_cookie(response, new_refresh_token)
    return TokenResponse(access_token=access_token, role=role)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    refresh_token_value = _require_refresh_cookie(request)
    await auth_service.logout(session, refresh_token_value)
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
    )
