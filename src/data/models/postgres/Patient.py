from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime


from ...clients.postgres import Base
from ....utils.generate_uuidv7 import uuid7_str


class Patient(Base):
    __tablename__ = "patients"

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
    dob: Mapped[Date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String)
    blood_group: Mapped[str | None] = mapped_column(String)
    emergency_contact: Mapped[str | None] = mapped_column(String)
    medical_notes: Mapped[str | None] = mapped_column(Text)
    is_walk_in: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    updated_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False))

    user = relationship("User", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")
