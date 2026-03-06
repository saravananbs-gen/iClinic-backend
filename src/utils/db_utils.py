import uuid
from sqlalchemy import select

from src.data.models.postgres.Patient import Patient


async def _resolve_patient_id(session, user_id: str) -> str | None:
    result = await session.execute(
        select(Patient.id).where(Patient.user_id == str(uuid.UUID(user_id.strip('"'))))
    )
    return result.scalar_one_or_none()
