from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.config.settings import settings
from src.control.agent.prompts import (
    DETECT_INTEND_SYSTEM_PROMPT,
    SUGGEST_PROVIDERS_SYSTEM_PROMPT,
    CHOOSE_PROVIDER_SYSTEM_PROMPT,
    SUGGEST_SLOTS_SYSTEM_PROMPT,
    CHOOSE_SLOT_AND_SUGGEST_TYPES_SYSTEM_PROMPT,
    CHOOSE_APPOINTMENT_TYPE_SYSTEM_PROMPT,
    CONFIRM_BOOKING_SYSTEM_PROMPT,
)
from src.control.agent.schemas import (
    IntentResponse,
    SuggestProvidersResponse,
    ChooseProviderResponse,
    SuggestSlotsResponse,
    ChooseSlotAndSuggestTypesResponse,
    ChooseAppointmentTypeResponse,
    ConfirmBookingResponse,
    AgentState,
)
from src.control.agent.tools import (
    find_providers,
    get_provider_slots,
    get_appointment_types,
    create_appointment,
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
choose_slot_and_suggest_types_llm = llm.with_structured_output(
    ChooseSlotAndSuggestTypesResponse
)
choose_appointment_type_llm = llm.with_structured_output(ChooseAppointmentTypeResponse)
confirm_booking_llm = llm.with_structured_output(ConfirmBookingResponse)


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
    return {
        "chosen_provider_id": result.chosen_provider_id,
        "messages": state["messages"] + [AIMessage(content=result.message)],
    }


async def suggest_slots(state: AgentState, config):
    user_message = state["messages"][-1]
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

    else:
        return {
            "suggested_slots": None,
            "chosen_slot_id": None,
            "suggested_appointment_types": None,
            "chosen_appointment_type": None,
            "messages": state["messages"] + [AIMessage(content=result.message)],
        }
