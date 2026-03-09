from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.Patient import Patient


async def create_patient(
    session: AsyncSession,
    *,
    user_id: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    dob=None,
    gender: str | None = None,
    blood_group: str | None = None,
    emergency_contact: str | None = None,
    medical_notes: str | None = None,
    is_walk_in: bool = False,
) -> Patient:
    patient = Patient(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        dob=dob,
        gender=gender,
        blood_group=blood_group,
        emergency_contact=emergency_contact,
        medical_notes=medical_notes,
        is_walk_in=is_walk_in,
    )
    session.add(patient)
    await session.flush()
    return patient


async def get_all(session: AsyncSession) -> Sequence[Patient]:
    result = await session.execute(select(Patient).order_by(Patient.created_at.desc()))
    return result.scalars().all()


async def get_by_id(session: AsyncSession, patient_id: str) -> Patient | None:
    return await session.get(Patient, patient_id)


async def get_by_phone(session: AsyncSession, phone: str) -> Patient | None:
    result = await session.execute(select(Patient).where(Patient.phone == phone))
    return result.scalar_one_or_none()
