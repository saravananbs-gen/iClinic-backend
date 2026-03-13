from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from src.control.agent.schemas import AgentState
from src.control.agent.nodes import (
    detect_intent,
    suggest_providers,
    choose_provider,
    suggest_slots,
    choose_slot_and_suggest_types,
    choose_appointment_type,
    confirm_booking,
    collect_cancel_reason,
    list_appointments_to_cancel,
    choose_appointment_to_cancel,
    confirm_cancel,
)
from src.data.clients.checkpointer import checkpointer


load_dotenv()

builder = StateGraph(AgentState)

builder.add_node("intent_detector", detect_intent)
builder.add_node("suggest_providers", suggest_providers)
builder.add_node("choose_provider", choose_provider)
builder.add_node("suggest_slots", suggest_slots)
builder.add_node("choose_slot_and_suggest_types", choose_slot_and_suggest_types)
builder.add_node("choose_appointment_type", choose_appointment_type)
builder.add_node("confirm_booking", confirm_booking)
builder.add_node("collect_cancel_reason", collect_cancel_reason)
builder.add_node("list_appointments_to_cancel", list_appointments_to_cancel)
builder.add_node("choose_appointment_to_cancel", choose_appointment_to_cancel)
builder.add_node("confirm_cancel", confirm_cancel)


def route_entry(state: AgentState):
    if state.get("intent") == "book":
        if not state.get("suggested_providers"):
            return "suggest_providers"
        if not state.get("chosen_provider_id"):
            return "choose_provider"
        if not state.get("suggested_slots"):
            return "suggest_slots"
        if not state.get("chosen_slot_id"):
            return "choose_slot_and_suggest_types"
        if not state.get("chosen_appointment_type"):
            return "choose_appointment_type"
        if not state.get("book_confirmed"):
            return "confirm_booking"

    if state.get("intent") == "cancel":
        if not state.get("cancel_reason"):
            return "collect_cancel_reason"
        if state.get("active_appointments") is None:
            return "list_appointments_to_cancel"
        if state.get("active_appointments") == []:
            return "intent_detector"
        if not state.get("chosen_appointment_id"):
            return "choose_appointment_to_cancel"
        if state.get("cancel_confirmed") is None:
            return "confirm_cancel"

    return "intent_detector"


builder.set_conditional_entry_point(route_entry)
builder.add_edge("intent_detector", END)
builder.add_edge("suggest_providers", END)
builder.add_edge("choose_provider", END)
builder.add_edge("suggest_slots", END)
builder.add_edge("choose_slot_and_suggest_types", END)
builder.add_edge("choose_appointment_type", END)
builder.add_edge("confirm_booking", END)
builder.add_edge("collect_cancel_reason", END)
builder.add_edge("list_appointments_to_cancel", END)
builder.add_edge("choose_appointment_to_cancel", END)
builder.add_edge("confirm_cancel", END)

graph = builder.compile(checkpointer=checkpointer)
