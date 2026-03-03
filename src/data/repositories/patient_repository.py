from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.Patient import Patient


async def create_patient(
    session: AsyncSession,
    *,
    user_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
) -> Patient:
    patient = Patient(id=user_id, first_name=first_name, last_name=last_name)
    session.add(patient)
    await session.flush()
    return patient
