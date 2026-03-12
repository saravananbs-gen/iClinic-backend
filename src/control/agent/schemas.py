from pydantic import BaseModel
from typing import Literal
from typing import TypedDict, List, Optional
from langchain_core.messages import BaseMessage


class SuggestedProvider(BaseModel):
    id: str
    name: str
    specialization: str
    experience: int
    fee: str


class SuggestedSlot(BaseModel):
    slot_id: str
    time: str
    start: str
    end: str


class AppointmentType(BaseModel):
    id: str
    name: str
    description: str
    duration_minutes: int


class AgentState(TypedDict):
    messages: List[BaseMessage]
    intent: str

    suggested_providers: Optional[List[SuggestedProvider]]
    chosen_provider_id: Optional[str]
    suggested_slots: Optional[List[SuggestedSlot]]
    chosen_slot_id: Optional[str]
    suggested_appointment_types: Optional[List[AppointmentType]]
    chosen_appointment_type: Optional[str]
    book_confirmed: Optional[bool]

    cancel_reason: Optional[str]
    active_appointments: Optional[List[dict]]
    chosen_appointment_id: Optional[str]
    cancel_confirmed: Optional[bool]


class IntentResponse(BaseModel):
    intent: Literal["book", "cancel", "unknown"]
    message: str


class SuggestProvidersResponse(BaseModel):
    suggested_providers: List[SuggestedProvider]
    message: str


class ChooseProviderResponse(BaseModel):
    action: Literal["choose", "new_symptoms"]
    chosen_provider_id: Optional[str]
    message: str


class SuggestSlotsResponse(BaseModel):
    suggested_slots: List[SuggestedSlot]
    message: str


class ChangeProviderCheckResponse(BaseModel):
    action: Literal["proceed", "change_provider"]
    message: str


class ChooseSlotAndSuggestTypesResponse(BaseModel):
    action: Literal["proceed", "change_provider", "change_slot"]
    chosen_slot_id: Optional[str]
    suggested_appointment_types: Optional[List[AppointmentType]]
    message: str


class ChooseAppointmentTypeResponse(BaseModel):
    action: Literal["proceed", "change_provider", "change_slot"]
    chosen_appointment_type: Optional[str]
    message: str


class ConfirmBookingResponse(BaseModel):
    action: Literal[
        "confirm", "change_provider", "change_slot", "change_appointment_type"
    ]
    message: str


class CollectCancelReasonResponse(BaseModel):
    action: Literal["proceed", "switch_to_book"]
    cancel_reason: Optional[str]
    message: str


class ChooseAppointmentToCancelResponse(BaseModel):
    action: Literal["choose", "switch_to_book"]
    chosen_appointment_id: Optional[str]
    message: str


class ConfirmCancelResponse(BaseModel):
    action: Literal["confirm", "abort", "switch_to_book"]
    message: str
