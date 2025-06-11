from enum import Enum
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam

# Prevent circular imports + Pydantic breaking
if TYPE_CHECKING:
    from scenario.scenario_executor import ScenarioExecutor

    ScenarioExecutorType = ScenarioExecutor
else:
    ScenarioExecutorType = Any


class ScenarioAgentRole(Enum):
    USER = "User"
    AGENT = "Agent"
    JUDGE = "Judge"


class AgentInput(BaseModel):
    thread_id: str
    messages: List[ChatCompletionMessageParam]
    new_messages: List[ChatCompletionMessageParam]
    context: Dict[str, Any]
    scenario_state: ScenarioExecutorType = Field(exclude=True)

    def last_new_user_message(self) -> ChatCompletionUserMessageParam:
        user_messages = [m for m in self.new_messages if m["role"] == "user"]
        if not user_messages:
            raise ValueError(
                "No new user messages found, did you mean to call the assistant twice? Perhaps change your adapter to use the full messages list instead."
            )
        return user_messages[-1]

    def last_new_user_message_str(self) -> str:
        content = self.last_new_user_message()["content"]
        if type(content) != str:
            raise ValueError(
                f"Last user message is not a string: {content.__repr__()}. Please use the full messages list instead."
            )
        return content


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
