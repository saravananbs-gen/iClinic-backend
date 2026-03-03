from sqlalchemy import String, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy.sql import func

from ...clients.postgres import Base
from ....utils.generate_uuidv7 import uuid7_str


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=uuid7_str
    )

    patient_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False
    )

    provider_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("providers.id"), nullable=False
    )

    slot_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("availability_slots.id"),
        unique=True,
        nullable=False,
    )

    appointment_type_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("appointment_types.id"), nullable=False
    )

    channel: Mapped[str | None] = mapped_column(String)
    status: Mapped[str | None] = mapped_column(String)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    patient = relationship("Patient", back_populates="appointments")
    provider = relationship("Provider", back_populates="appointments")
    slot = relationship("AvailabilitySlot", back_populates="appointment")
    appointment_type = relationship("AppointmentType", back_populates="appointments")
