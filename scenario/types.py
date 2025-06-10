from enum import Enum
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from openai.types.chat import ChatCompletionMessageParam

# Prevent circular imports + Pydantic breaking
if TYPE_CHECKING:
    from scenario.scenario_executor import ScenarioExecutor

    ScenarioExecutorType = ScenarioExecutor
else:
    ScenarioExecutorType = Any


class MessageTriggers(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class AgentInput(BaseModel):
    thread_id: str
    messages: List[ChatCompletionMessageParam]
    context: Dict[str, Any]
    scenario_state: ScenarioExecutorType = Field(exclude=True)

    def last_user_message(self) -> ChatCompletionMessageParam:
        user_messages = [m for m in self.messages if m["role"] == "user"]
        if not user_messages:
            raise ValueError("No user messages found")
        return user_messages[-1]


class ScenarioResult(BaseModel):
    """
    Represents the results of a scenario test run.

    Attributes:
        success: Whether the scenario passed
        conversation: The conversation history
        reasoning: Reasoning for the result
        passed_criteria: List of criteria that were met
        failed_criteria: List of criteria that were not met
    """

    success: bool
    messages: List[ChatCompletionMessageParam]
    reasoning: Optional[str] = None
    passed_criteria: List[str] = []
    failed_criteria: List[str] = []
    total_time: Optional[float] = None
    agent_time: Optional[float] = None


AgentReturnTypes = Union[
    str, ChatCompletionMessageParam, List[ChatCompletionMessageParam], ScenarioResult
]
