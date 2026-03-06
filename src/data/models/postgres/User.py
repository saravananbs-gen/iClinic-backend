from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime


from ...clients.postgres import Base
from ....utils.generate_uuidv7 import uuid7_str


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=uuid7_str
    )

    role_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("roles.id"), nullable=False
    )

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    last_login: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    updated_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False))

    role = relationship("Role", back_populates="users")
    provider = relationship(
        "Provider",
        back_populates="user",
        uselist=False,
        foreign_keys="[Provider.user_id]",
    )
    patient = relationship(
        "Patient",
        back_populates="user",
        uselist=False,
        foreign_keys="[Patient.user_id]",
    )
    sessions = relationship("Session", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
