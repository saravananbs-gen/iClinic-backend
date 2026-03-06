from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class CreatePatientRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str | None = None
    dob: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    emergency_contact: str | None = None
    medical_notes: str | None = None


class PatientResponse(BaseModel):
    id: str
    user_id: str | None
    first_name: str | None
    last_name: str | None
    phone: str | None
    email: str | None
    dob: date | None
    gender: str | None
    blood_group: str | None
    emergency_contact: str | None
    medical_notes: str | None
    is_walk_in: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateProviderRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str | None = None
    email: str | None = None
    specialization: str | None = None
    notable_work: str | None = None
    experience_years: int | None = None
    qualification: str | None = None
    consultation_fee: float | None = None
    bio: str | None = None


class ProviderResponse(BaseModel):
    id: str
    user_id: str | None
    first_name: str | None
    last_name: str | None
    phone: str | None
    email: str | None
    specialization: str | None
    notable_work: str | None
    experience_years: int | None
    qualification: str | None
    consultation_fee: float | None
    bio: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SlotResponse(BaseModel):
    id: str
    provider_id: str
    start_time: datetime
    end_time: datetime
    is_booked: bool

    model_config = ConfigDict(from_attributes=True)


class AppointmentTypeResponse(BaseModel):
    id: str
    name: str
    description: str | None
    duration_minutes: int

    model_config = ConfigDict(from_attributes=True)


class CreateAppointmentRequest(BaseModel):
    patient_id: str
    provider_id: str
    slot_id: str
    appointment_type_id: str
    channel: str = "walk-in"
    notes: str | None = None


class AppointmentResponse(BaseModel):
    id: str
    patient_id: str
    provider_id: str
    slot_id: str
    appointment_type_id: str
    channel: str | None
    status: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentDetailResponse(BaseModel):
    id: str
    status: str | None
    channel: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    patient: PatientResponse | None
    provider: ProviderResponse | None
    slot: SlotResponse | None
    appointment_type: AppointmentTypeResponse | None

    model_config = ConfigDict(from_attributes=True)
