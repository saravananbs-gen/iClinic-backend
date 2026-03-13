from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from fastapi import APIRouter, Depends

from src.schemas.auth import CurrentUserSchema
from src.api.rest.dependencies import require_patient
from src.control.agent.graph import graph

router = APIRouter()


@router.post("/chat")
async def chat(
    message: str, thread_id: str, user: CurrentUserSchema = Depends(require_patient)
):

    state = {"messages": [HumanMessage(content=message)]}

    config: RunnableConfig = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user.user_id,
            "user_phone": user.user_phone,
            "user_email": user.user_email,
            "role": user.role,
        }
    }

    result = await graph.ainvoke(state, config=config)

    return result
