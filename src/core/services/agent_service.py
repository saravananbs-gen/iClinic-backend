from langchain_core.messages import HumanMessage

from src.control.agents.create_agent import agent


class VoiceAgent:
    def __init__(self):
        self.agent = agent

    async def generate_response(
        self,
        call_sid: str,
        user_input: str,
        user_id: str,
        user_phone: str,
    ) -> str:

        result = await self.agent.ainvoke(
            {
                "messages": [HumanMessage(content=user_input)],
            },
            config={
                "configurable": {
                    "thread_id": call_sid,
                    "user_id": user_id,
                    "user_phone": user_phone,
                }
            },
        )

        return result["messages"][-1].content


voice_agent = VoiceAgent()
