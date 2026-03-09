from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import require_patient
from src.data.clients.postgres import get_async_session
from src.core.services import dashboard_service
from src.schemas.auth import CurrentUserSchema
from src.schemas.dashboard import (
    DashboardAppointmentsResponse,
    DashboardProfileResponse,
)

router = APIRouter()


@router.get("/profile", response_model=DashboardProfileResponse)
async def get_dashboard_profile(
    current_user: CurrentUserSchema = Depends(require_patient),
    session: AsyncSession = Depends(get_async_session),
) -> DashboardProfileResponse:
    return await dashboard_service.get_profile(session, current_user.user_id)


@router.get("/appointments", response_model=DashboardAppointmentsResponse)
async def get_dashboard_appointments(
    current_user: CurrentUserSchema = Depends(require_patient),
    session: AsyncSession = Depends(get_async_session),
) -> DashboardAppointmentsResponse:
    return await dashboard_service.get_appointments(session, current_user.user_id)
