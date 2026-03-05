from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class DashboardProfileResponse(BaseModel):
    name: str
    email: EmailStr
    phone: str | None

    model_config = ConfigDict(from_attributes=True)


class ProviderSummary(BaseModel):
    id: str
    name: str | None
    email: EmailStr | None
    phone: str | None
    specialization: str | None
    qualification: str | None
    consultation_fee: float | None

    model_config = ConfigDict(from_attributes=True)


class AvailabilitySlotInfo(BaseModel):
    id: str
    start_time: datetime
    end_time: datetime
    is_booked: bool

    model_config = ConfigDict(from_attributes=True)


class AppointmentTypeInfo(BaseModel):
    id: str
    name: str
    description: str | None
    duration_minutes: int

    model_config = ConfigDict(from_attributes=True)


class AppointmentSummary(BaseModel):
    id: str
    status: str | None
    channel: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    is_upcoming: bool
    provider: ProviderSummary | None
    slot: AvailabilitySlotInfo | None
    appointment_type: AppointmentTypeInfo | None

    model_config = ConfigDict(from_attributes=True)


class DashboardAppointmentsResponse(BaseModel):
    upcoming: list[AppointmentSummary]
    past: list[AppointmentSummary]

    model_config = ConfigDict(from_attributes=True)
