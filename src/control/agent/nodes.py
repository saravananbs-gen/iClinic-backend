from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.config.settings import settings
from src.control.agent.prompts import (
    DETECT_INTEND_SYSTEM_PROMPT,
    SUGGEST_PROVIDERS_SYSTEM_PROMPT,
    CHOOSE_PROVIDER_SYSTEM_PROMPT,
    SUGGEST_SLOTS_SYSTEM_PROMPT,
    CHANGE_PROVIDER_CHECK_SYSTEM_PROMPT,
    CHOOSE_SLOT_AND_SUGGEST_TYPES_SYSTEM_PROMPT,
    CHOOSE_APPOINTMENT_TYPE_SYSTEM_PROMPT,
    CONFIRM_BOOKING_SYSTEM_PROMPT,
    COLLECT_CANCEL_REASON_SYSTEM_PROMPT,
    CHOOSE_APPOINTMENT_TO_CANCEL_SYSTEM_PROMPT,
    CONFIRM_CANCEL_SYSTEM_PROMPT,
)
from src.control.agent.schemas import (
    IntentResponse,
    SuggestProvidersResponse,
    ChooseProviderResponse,
    SuggestSlotsResponse,
    ChangeProviderCheckResponse,
    ChooseSlotAndSuggestTypesResponse,
    ChooseAppointmentTypeResponse,
    ConfirmBookingResponse,
    CollectCancelReasonResponse,
    ChooseAppointmentToCancelResponse,
    ConfirmCancelResponse,
    AgentState,
)
from src.control.agent.tools import (
    find_providers,
    get_provider_slots,
    get_appointment_types,
    create_appointment,
    list_active_appointments,
    cancel_appointment_by_id,
)


llm = ChatOpenAI(
    model=settings.LLM_DEPLOYMENT_NAME,
    api_key=settings.AZURE_FOUNDRY_KEY,
    base_url=settings.AZURE_FOUNDRY_ENDPOINT,
    temperature=0.2,
)

structured_llm = llm.with_structured_output(IntentResponse)
suggest_providers_llm = llm.with_structured_output(SuggestProvidersResponse)
choose_provider_llm = llm.with_structured_output(ChooseProviderResponse)
suggest_slots_llm = llm.with_structured_output(SuggestSlotsResponse)
change_provider_check_llm = llm.with_structured_output(ChangeProviderCheckResponse)
choose_slot_and_suggest_types_llm = llm.with_structured_output(
    ChooseSlotAndSuggestTypesResponse
)
choose_appointment_type_llm = llm.with_structured_output(ChooseAppointmentTypeResponse)
confirm_booking_llm = llm.with_structured_output(ConfirmBookingResponse)
collect_cancel_reason_llm = llm.with_structured_output(CollectCancelReasonResponse)
choose_appointment_to_cancel_llm = llm.with_structured_output(
    ChooseAppointmentToCancelResponse
)
confirm_cancel_llm = llm.with_structured_output(ConfirmCancelResponse)


def _format_appointments_for_cancel_message(appointments: list[dict]) -> str:
    appointment_lines = [
        (
            f"{index}. {appointment['provider_name']} "
            f"({appointment['specialization']}) - {appointment['date']} at {appointment['time']}"
        )
        for index, appointment in enumerate(appointments, start=1)
    ]
    return "\n".join(appointment_lines)


def detect_intent(state: AgentState):
    user_message = state["messages"][-1]
    system_prompt = DETECT_INTEND_SYSTEM_PROMPT
    result = structured_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message.content),
        ]
    )
    return {
        "intent": result.intent,
        "messages": state["messages"] + [AIMessage(content=result.message)],
    }


async def suggest_providers(state: AgentState, config):
    user_message = state["messages"][-1]
    providers_json = await find_providers.ainvoke({}, config)
    system_prompt = SUGGEST_PROVIDERS_SYSTEM_PROMPT.format(providers=providers_json)
    result = suggest_providers_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message.content),
        ]
    )
    return {
        "suggested_providers": result.suggested_providers,
        "messages": state["messages"] + [AIMessage(content=result.message)],
    }


def choose_provider(state: AgentState):
    user_message = state["messages"][-1]
    suggested = state["suggested_providers"]
    providers_info = [
        {"id": p.id, "name": p.name, "specialization": p.specialization}
        for p in suggested
    ]
    system_prompt = CHOOSE_PROVIDER_SYSTEM_PROMPT.format(providers=providers_info)
    result = choose_provider_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message.content),
        ]
    )

    if result.action == "new_symptoms":
        return {
            "suggested_providers": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    return {
        "chosen_provider_id": result.chosen_provider_id,
        "messages": state["messages"] + [AIMessage(content=result.message)],
    }


async def suggest_slots(state: AgentState, config):
    user_message = state["messages"][-1]

    check_result = change_provider_check_llm.invoke(
        [
            SystemMessage(content=CHANGE_PROVIDER_CHECK_SYSTEM_PROMPT),
            HumanMessage(content=user_message.content),
        ]
    )

    if check_result.action == "change_provider":
        return {
            "suggested_providers": None,
            "chosen_provider_id": None,
            "suggested_slots": None,
            "chosen_slot_id": None,
            "suggested_appointment_types": None,
            "chosen_appointment_type": None,
            "messages": state["messages"] + [AIMessage(content=check_result.message)],
        }

    slots_json = await get_provider_slots.ainvoke(
        {
            "provider_id": state["chosen_provider_id"],
            "preferred_time": user_message.content,
        },
        config,
    )
    system_prompt = SUGGEST_SLOTS_SYSTEM_PROMPT.format(slots=slots_json)
    result = suggest_slots_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message.content),
        ]
    )
    return {
        "suggested_slots": result.suggested_slots,
        "messages": state["messages"] + [AIMessage(content=result.message)],
    }


async def choose_slot_and_suggest_types(state: AgentState, config):
    user_message = state["messages"][-1]
    slots_info = [
        {"slot_id": s.slot_id, "time": s.time} for s in state["suggested_slots"]
    ]
    appointment_types_json = await get_appointment_types.ainvoke({}, config)
    system_prompt = CHOOSE_SLOT_AND_SUGGEST_TYPES_SYSTEM_PROMPT.format(
        slots=slots_info,
        appointment_types=appointment_types_json,
    )
    result = choose_slot_and_suggest_types_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message.content),
        ]
    )

    if result.action == "change_provider":
        return {
            "suggested_providers": None,
            "chosen_provider_id": None,
            "suggested_slots": None,
            "chosen_slot_id": None,
            "suggested_appointment_types": None,
            "chosen_appointment_type": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    if result.action == "change_slot":
        return {
            "suggested_slots": None,
            "chosen_slot_id": None,
            "suggested_appointment_types": None,
            "chosen_appointment_type": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    return {
        "chosen_slot_id": result.chosen_slot_id,
        "suggested_appointment_types": result.suggested_appointment_types,
        "messages": state["messages"] + [AIMessage(content=result.message)],
    }


def choose_appointment_type(state: AgentState):

    user_message = state["messages"][-1]

    provider = state["suggested_providers"][0]
    chosen_provider_id = state["chosen_provider_id"]
    chosen_provider = next(
        (p for p in state["suggested_providers"] if p.id == chosen_provider_id),
        provider,
    )

    chosen_slot = next(
        (s for s in state["suggested_slots"] if s.slot_id == state["chosen_slot_id"]),
        state["suggested_slots"][0],
    )

    types_info = [
        {"name": t.name, "description": t.description}
        for t in state["suggested_appointment_types"]
    ]

    system_prompt = CHOOSE_APPOINTMENT_TYPE_SYSTEM_PROMPT.format(
        appointment_types=types_info,
        provider_name=chosen_provider.name,
        specialization=chosen_provider.specialization,
        slot_time=chosen_slot.time,
    )

    result = choose_appointment_type_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message.content),
        ]
    )

    if result.action == "change_provider":
        return {
            "suggested_providers": None,
            "chosen_provider_id": None,
            "suggested_slots": None,
            "chosen_slot_id": None,
            "suggested_appointment_types": None,
            "chosen_appointment_type": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    if result.action == "change_slot":
        return {
            "suggested_slots": None,
            "chosen_slot_id": None,
            "suggested_appointment_types": None,
            "chosen_appointment_type": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    return {
        "chosen_appointment_type": result.chosen_appointment_type,
        "messages": state["messages"] + [AIMessage(content=result.message)],
    }


async def confirm_booking(state: AgentState, config):

    user_message = state["messages"][-1]

    chosen_provider = next(
        (
            p
            for p in state["suggested_providers"]
            if p.id == state["chosen_provider_id"]
        ),
        state["suggested_providers"][0],
    )
    chosen_slot = next(
        (s for s in state["suggested_slots"] if s.slot_id == state["chosen_slot_id"]),
        state["suggested_slots"][0],
    )

    system_prompt = CONFIRM_BOOKING_SYSTEM_PROMPT.format(
        provider_name=chosen_provider.name,
        specialization=chosen_provider.specialization,
        slot_time=chosen_slot.time,
        appointment_type=state["chosen_appointment_type"],
    )

    result = confirm_booking_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message.content),
        ]
    )

    if result.action == "confirm":
        await create_appointment.ainvoke(
            {
                "provider_id": state["chosen_provider_id"],
                "slot_id": state["chosen_slot_id"],
                "appointment_type_name": state["chosen_appointment_type"],
            },
            config,
        )
        return {
            "book_confirmed": True,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    elif result.action == "change_provider":
        return {
            "suggested_providers": None,
            "chosen_provider_id": None,
            "suggested_slots": None,
            "chosen_slot_id": None,
            "suggested_appointment_types": None,
            "chosen_appointment_type": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    elif result.action == "change_slot":
        return {
            "suggested_slots": None,
            "chosen_slot_id": None,
            "suggested_appointment_types": None,
            "chosen_appointment_type": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    else:  # change_appointment_type
        return {
            "suggested_appointment_types": state["suggested_appointment_types"],
            "chosen_appointment_type": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }


async def collect_cancel_reason(state: AgentState, config):

    user_message = state["messages"][-1]

    result = collect_cancel_reason_llm.invoke(
        [
            SystemMessage(content=COLLECT_CANCEL_REASON_SYSTEM_PROMPT),
            HumanMessage(content=user_message.content),
        ]
    )

    if result.action == "switch_to_book":
        return {
            "intent": "book",
            "cancel_reason": None,
            "active_appointments": None,
            "chosen_appointment_id": None,
            "cancel_confirmed": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    appointments_json = await list_active_appointments.ainvoke({}, config)

    if appointments_json == "You don't have any active appointments at the moment.":
        return {
            "cancel_reason": result.cancel_reason,
            "active_appointments": [],
            "messages": state["messages"]
            + [
                AIMessage(
                    content=(
                        f"{result.message} You don't have any upcoming appointments to cancel."
                    )
                )
            ],
        }

    import json

    appointments = json.loads(appointments_json)
    appointments_list = _format_appointments_for_cancel_message(appointments)

    return {
        "cancel_reason": result.cancel_reason,
        "active_appointments": appointments,
        "messages": state["messages"]
        + [
            AIMessage(
                content=(
                    f"{result.message}\n\n"
                    f"Here are your upcoming appointments:\n\n"
                    f"{appointments_list}\n\n"
                    "Please tell me which appointment you'd like to cancel. "
                    "You can mention the doctor's name, date, or time."
                )
            )
        ],
    }


async def list_appointments_to_cancel(state: AgentState, config):

    appointments_json = await list_active_appointments.ainvoke({}, config)

    if appointments_json == "You don't have any active appointments at the moment.":
        return {
            "active_appointments": [],
            "messages": state["messages"]
            + [
                AIMessage(content="You don't have any upcoming appointments to cancel.")
            ],
        }

    import json

    appointments = json.loads(appointments_json)

    appointments_info = [
        {
            "appointment_id": a["appointment_id"],
            "provider_name": a["provider_name"],
            "specialization": a["specialization"],
            "date": a["date"],
            "time": a["time"],
        }
        for a in appointments
    ]

    system_prompt = CHOOSE_APPOINTMENT_TO_CANCEL_SYSTEM_PROMPT.format(
        appointments=appointments_info
    )

    result = choose_appointment_to_cancel_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content="Here are your upcoming appointments. Which one would you like to cancel?"
            ),
        ]
    )

    return {
        "active_appointments": appointments,
        "messages": state["messages"] + [AIMessage(content=result.message)],
    }


def choose_appointment_to_cancel(state: AgentState):

    user_message = state["messages"][-1]

    appointments_info = [
        {
            "appointment_id": a["appointment_id"],
            "provider_name": a["provider_name"],
            "specialization": a["specialization"],
            "date": a["date"],
            "time": a["time"],
        }
        for a in state["active_appointments"]
    ]

    system_prompt = CHOOSE_APPOINTMENT_TO_CANCEL_SYSTEM_PROMPT.format(
        appointments=appointments_info
    )

    result = choose_appointment_to_cancel_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message.content),
        ]
    )

    if result.action == "switch_to_book":
        return {
            "intent": "book",
            "cancel_reason": None,
            "active_appointments": None,
            "chosen_appointment_id": None,
            "cancel_confirmed": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    return {
        "chosen_appointment_id": result.chosen_appointment_id,
        "messages": state["messages"] + [AIMessage(content=result.message)],
    }


async def confirm_cancel(state: AgentState, config):

    user_message = state["messages"][-1]

    chosen = next(
        (
            a
            for a in state["active_appointments"]
            if a["appointment_id"] == state["chosen_appointment_id"]
        ),
        state["active_appointments"][0],
    )

    appointment_details = (
        f"Provider: {chosen['provider_name']} ({chosen['specialization']}), "
        f"Date: {chosen['date']} at {chosen['time']}"
    )

    result = confirm_cancel_llm.invoke(
        [
            SystemMessage(
                content=CONFIRM_CANCEL_SYSTEM_PROMPT.format(
                    appointment_details=appointment_details
                )
            ),
            HumanMessage(content=user_message.content),
        ]
    )

    if result.action == "confirm":
        await cancel_appointment_by_id.ainvoke(
            {"appointment_id": state["chosen_appointment_id"]},
            config,
        )
        return {
            "cancel_confirmed": True,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    elif result.action == "switch_to_book":
        return {
            "intent": "book",
            "cancel_reason": None,
            "active_appointments": None,
            "chosen_appointment_id": None,
            "cancel_confirmed": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }

    else:  # abort
        return {
            "cancel_confirmed": False,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }
