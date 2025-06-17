from typing import List, Dict, Any, Optional, TYPE_CHECKING
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel

from scenario.config import ScenarioConfig

if TYPE_CHECKING:
    from .scenario_executor import ScenarioExecutor


class ScenarioState(BaseModel):
    description: str
    messages: List[ChatCompletionMessageParam]
    thread_id: str
    current_turn: int
    config: ScenarioConfig

    _executor: "ScenarioExecutor"

    def add_message(self, message: ChatCompletionMessageParam):
        self._executor.add_message(message)

    def last_message(self) -> ChatCompletionMessageParam:
        if len(self.messages) == 0:
            raise ValueError("No messages found")
        return self.messages[-1]

    def last_user_message(self) -> ChatCompletionUserMessageParam:
        user_messages = [m for m in self.messages if m["role"] == "user"]
        if not user_messages:
            raise ValueError("No user messages found")
        return user_messages[-1]

    def last_tool_call(
        self, tool_name: str
    ) -> Optional[ChatCompletionMessageToolCallParam]:
        for message in reversed(self.messages):
            if message["role"] == "assistant" and "tool_calls" in message:
                for tool_call in message["tool_calls"]:
                    if tool_call["function"]["name"] == tool_name:
                        return tool_call
        return None

    def has_tool_call(self, tool_name: str) -> bool:
        return self.last_tool_call(tool_name) is not None
