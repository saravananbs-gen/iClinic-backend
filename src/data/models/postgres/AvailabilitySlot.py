from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from ...clients.postgres import Base
from ....utils.generate_uuidv7 import uuid7_str


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=uuid7_str
    )

    provider_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("providers.id"), nullable=False
    )

    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)

    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)

    provider = relationship("Provider", back_populates="availability_slots")
    appointment = relationship("Appointment", back_populates="slot", uselist=False)
