from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, DECIMAL, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime


from ...clients.postgres import Base
from ....utils.generate_uuidv7 import uuid7_str


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=uuid7_str
    )

    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=True
    )

    first_name: Mapped[str | None] = mapped_column(String)
    last_name: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    specialization: Mapped[str | None] = mapped_column(String)
    notable_work: Mapped[str | None] = mapped_column(String)
    experience_years: Mapped[int | None] = mapped_column(Integer)
    qualification: Mapped[str | None] = mapped_column(String)
    consultation_fee: Mapped[float | None] = mapped_column(DECIMAL)

    bio: Mapped[str | None] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    updated_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False))

    user = relationship("User", back_populates="provider")
    availability_slots = relationship("AvailabilitySlot", back_populates="provider")
    appointments = relationship("Appointment", back_populates="provider")
