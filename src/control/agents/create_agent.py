from langchain.agents import create_agent
from langchain_groq import ChatGroq

from src.data.clients.checkpointer import checkpointer
from src.control.agents.prompts.chat import SYSTEM_PROMPT
from src.control.agents.tools.tools import (
    find_providers,
    get_provider_slots,
    create_appointment,
    get_appointment_types,
    list_active_appointments,
    cancel_appointment_by_id,
)
from src.config.settings import settings
from src.observability.logging.agent import AgentLoggingCallback
from src.observability.logging import get_logger

logger = get_logger(__name__)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.4,
    api_key=settings.GROQ_API_KEY,
    callbacks=[AgentLoggingCallback()],
)

agent = create_agent(
    model=llm,
    tools=[
        find_providers,
        get_provider_slots,
        create_appointment,
        get_appointment_types,
        list_active_appointments,
        cancel_appointment_by_id,
    ],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

logger.info(
    "LangGraph agent created",
    extra={"extra_data": {"model": "llama-3.3-70b-versatile", "tools_count": 6}},
)
