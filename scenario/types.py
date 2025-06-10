from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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


@dataclass
class ScenarioResult:
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
    passed_criteria: List[str] = Field(default_factory=list)
    failed_criteria: List[str] = Field(default_factory=list)
    total_time: Optional[float] = None
    agent_time: Optional[float] = None
