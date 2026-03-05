import time
from langchain_core.messages import HumanMessage

from src.control.agents.create_agent import agent
from src.observability.logging import get_logger

logger = get_logger(__name__)


class VoiceAgent:
    def __init__(self):
        self.agent = agent

    async def generate_response(
        self,
        call_sid: str,
        user_input: str,
        user_id: str,
        user_phone: str,
        user_email: str,
        to_phone: str,
    ) -> str:
        logger.info(
            "Agent invocation started",
            extra={
                "extra_data": {
                    "call_sid": call_sid,
                    "user_id": user_id,
                    "input_length": len(user_input),
                }
            },
        )

        start = time.perf_counter()
        try:
            result = await self.agent.ainvoke(
                {
                    "messages": [HumanMessage(content=user_input)],
                },
                config={
                    "configurable": {
                        "thread_id": call_sid,
                        "user_id": user_id,
                        "user_phone": user_phone,
                        "user_email": user_email,
                        "to_phone": to_phone,
                    }
                },
            )

            response_text = result["messages"][-1].content
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            logger.info(
                "Agent invocation completed",
                extra={
                    "extra_data": {
                        "call_sid": call_sid,
                        "duration_ms": duration_ms,
                        "response_length": len(response_text),
                    }
                },
            )

            return response_text

        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "Agent invocation failed",
                exc_info=True,
                extra={
                    "extra_data": {
                        "call_sid": call_sid,
                        "duration_ms": duration_ms,
                    }
                },
            )
            raise


voice_agent = VoiceAgent()
