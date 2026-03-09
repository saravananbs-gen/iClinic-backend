from langchain_core.tools import tool
import json
import uuid
from sqlalchemy import select
from langchain_core.runnables import RunnableConfig
from src.data.models.postgres.Provider import Provider
from src.data.models.postgres.Appointment import Appointment
from src.data.models.postgres.AvailabilitySlot import AvailabilitySlot
from src.data.models.postgres.AppointmentType import AppointmentType
from src.data.clients.postgres import AsyncSessionLocal
from src.utils.generate_uuidv7 import uuid7_str
from src.utils.db_utils import _resolve_patient_id
from src.core.services.notification import send_appointment_notification
from src.observability.logging import get_logger

logger = get_logger(__name__)


@tool
async def find_providers(config: RunnableConfig) -> str:
    """Find providers by specialization."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Provider))
            providers = result.scalars().all()

            data = [
                {
                    "id": p.id,
                    "name": f"{p.first_name} {p.last_name}",
                    "specialization": p.specialization,
                    "experience": p.experience_years,
                    "fee": str(p.consultation_fee),
                }
                for p in providers
            ]
            return json.dumps(data) if data else "No providers found."

    except Exception as e:
        return f"Error fetching providers: {str(e)}"


@tool
async def get_provider_slots(provider_id: str, config: RunnableConfig) -> str:
    """Get available slots for a provider.
    provider_id is a uuid which is given to each provider.
    Eg:
    {"id": "cccccccc-cccc-cccc-cccc-cccccccccccc", "name": "MeeraSharma", "specialization": "Dermatology", "experience": 8, "fee": "600.00"}
    here cccccccc-cccc-cccc-cccc-cccccccccccc is the provider_id"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AvailabilitySlot).where(
                    AvailabilitySlot.provider_id == provider_id,
                    AvailabilitySlot.is_booked == False,  # noqa: E712
                )
            )

            slots = result.scalars().all()

            data = [
                {
                    "slot_id": s.id,
                    "start": s.start_time.isoformat(),
                    "end": s.end_time.isoformat(),
                }
                for s in slots
            ]

            return json.dumps(data) if data else "No available slots."

    except Exception as e:
        return f"Error fetching slots: {str(e)}"


@tool
async def create_appointment(
    provider_id: str,
    slot_id: str,
    appointment_type_name: str,
    config: RunnableConfig,
) -> str:
    """Create appointment and mark slot booked."""

    user_id = config["configurable"].get("user_id")

    try:
        async with AsyncSessionLocal() as session:
            patient_id = await _resolve_patient_id(session, user_id)
            if not patient_id:
                return "Patient profile not found for the current user."

            normalized_name = appointment_type_name.strip().title()

            result = await session.execute(
                select(AppointmentType).where(AppointmentType.name == normalized_name)
            )
            appointment_type = result.scalar_one_or_none()

            if not appointment_type:
                return f"Appointment type '{normalized_name}' not found."

            appointment = Appointment(
                id=str(uuid.UUID(uuid7_str().strip('"'))),
                patient_id=patient_id,
                provider_id=str(uuid.UUID(provider_id.strip('"'))),
                slot_id=str(uuid.UUID(slot_id.strip('"'))),
                appointment_type_id=appointment_type.id,
                status="confirmed",
            )

            session.add(appointment)

            slot_result = await session.execute(
                select(AvailabilitySlot).where(
                    AvailabilitySlot.id == str(uuid.UUID(slot_id.strip('"')))
                )
            )
            slot = slot_result.scalar_one_or_none()

            if not slot:
                return "Selected slot not found."

            if slot.is_booked:
                return "This slot is already booked."

            slot.is_booked = True

            await session.commit()

            provider_result = await session.execute(
                select(Provider).where(Provider.id == provider_id)
            )
            provider = provider_result.scalar_one()

            slot_time = f"{slot.start_time} - {slot.end_time}"

            try:
                await send_appointment_notification(
                    action="booked",
                    patient_email=config["configurable"]["user_email"],
                    patient_phone=config["configurable"]["user_phone"],
                    provider_name=f"{provider.first_name} {provider.last_name}",
                    specialization=provider.specialization,
                    slot_time=slot_time,
                    appointment_type=normalized_name,
                )
            except Exception:
                logger.error(
                    "Booking notification failed",
                    exc_info=True,
                    extra={"extra_data": {"appointment_id": str(appointment.id)}},
                )

            return "Appointment successfully confirmed."

    except Exception as e:
        return f"Error creating appointment: {str(e)}"


@tool
async def get_appointment_types() -> str:
    """Fetch all available appointment types."""

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AppointmentType).order_by(AppointmentType.duration_minutes)
            )
            types = result.scalars().all()

            if not types:
                return "No appointment types available."

            data = [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "duration_minutes": t.duration_minutes,
                }
                for t in types
            ]

            return json.dumps(data)

    except Exception as e:
        return f"Error fetching appointment types: {str(e)}"


@tool
async def list_active_appointments(config: RunnableConfig) -> str:
    """
    Fetch all currently confirmed appointments for the calling user.
    Use this before cancelling to ensure we have the correct appointment ID.
    """
    patient_id = config["configurable"].get("user_id")

    try:
        async with AsyncSessionLocal() as session:
            resolved_patient_id = await _resolve_patient_id(session, patient_id)
            if not resolved_patient_id:
                return "Patient profile not found for the current user."

            stmt = (
                select(Appointment, Provider, AvailabilitySlot)
                .join(Provider, Appointment.provider_id == Provider.id)
                .join(AvailabilitySlot, Appointment.slot_id == AvailabilitySlot.id)
                .where(
                    Appointment.patient_id == resolved_patient_id,
                    Appointment.status == "confirmed",
                )
            )

            result = await session.execute(stmt)
            appointments = result.all()

            if not appointments:
                return "You don't have any active appointments at the moment."

            data = [
                {
                    "appointment_id": str(apt.Appointment.id),
                    "provider_name": f"Dr. {apt.Provider.first_name} {apt.Provider.last_name}",
                    "specialization": apt.Provider.specialization,
                    "date": apt.AvailabilitySlot.start_time.strftime("%B %d, %Y"),
                    "time": apt.AvailabilitySlot.start_time.strftime("%I:%M %p"),
                    "slot_id": str(apt.AvailabilitySlot.id),
                }
                for apt in appointments
            ]

            return json.dumps(data)

    except Exception as e:
        return f"Error retrieving appointments: {str(e)}"


@tool
async def cancel_appointment_by_id(appointment_id: str, config: RunnableConfig) -> str:
    """
    Permanently cancels a specific appointment and frees the associated slot.
    - appointment_id: The unique ID of the appointment to cancel.
    """
    patient_id = config["configurable"].get("user_id")

    try:
        async with AsyncSessionLocal() as session:
            resolved_patient_id = await _resolve_patient_id(session, patient_id)
            if not resolved_patient_id:
                return "Patient profile not found for the current user."

            stmt = select(Appointment).where(
                Appointment.id == str(uuid.UUID(appointment_id.strip('"'))),
                Appointment.patient_id == resolved_patient_id,
            )
            result = await session.execute(stmt)
            appointment = result.scalar_one_or_none()

            if not appointment:
                return "Authorization failed: Appointment not found or does not belong to you."

            if appointment.status == "cancelled":
                return "This appointment is already cancelled."

            appointment.status = "cancelled"

            slot_stmt = select(AvailabilitySlot).where(
                AvailabilitySlot.id == appointment.slot_id
            )
            slot_result = await session.execute(slot_stmt)
            slot = slot_result.scalar_one_or_none()

            if slot:
                slot.is_booked = False

            await session.commit()

            provider_result = await session.execute(
                select(Provider).where(Provider.id == appointment.provider_id)
            )
            provider = provider_result.scalar_one()

            slot_time = f"{slot.start_time} - {slot.end_time}"

            try:
                await send_appointment_notification(
                    action="cancelled",
                    patient_email=config["configurable"]["user_email"],
                    patient_phone=config["configurable"]["user_phone"],
                    provider_name=f"{provider.first_name} {provider.last_name}",
                    specialization=provider.specialization,
                    slot_time=slot_time,
                    appointment_type="Appointment",
                )
            except Exception:
                logger.error(
                    "Cancellation notification failed",
                    exc_info=True,
                    extra={"extra_data": {"appointment_id": appointment_id}},
                )

            return "Success: The appointment has been cancelled and the slot is now available."

    except Exception as e:
        return f"Critical error during cancellation: {str(e)}"
