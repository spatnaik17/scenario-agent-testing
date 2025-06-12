from enum import Enum
from pydantic import BaseModel, Field, SkipValidation
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Union,
)

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
    # Prevent pydantic from validating/parsing the messages and causing issues: https://github.com/pydantic/pydantic/issues/9541
    messages: Annotated[List[ChatCompletionMessageParam], SkipValidation]
    new_messages: Annotated[List[ChatCompletionMessageParam], SkipValidation]
    context: Dict[str, Any]
    requested_role: ScenarioAgentRole
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

    def __repr__(self) -> str:
        """Provide a concise representation for debugging."""
        status = "PASSED" if self.success else "FAILED"
        return f"ScenarioResult(success={self.success}, status={status}, reasoning='{self.reasoning or 'None'}')"


AgentReturnTypes = Union[
    str, ChatCompletionMessageParam, List[ChatCompletionMessageParam], ScenarioResult
]

# TODO: remove the optional ScenarioResult return type from here, use events instead
ScriptStep = Union[
    Callable[["ScenarioExecutor"], None],
    Callable[["ScenarioExecutor"], Optional[ScenarioResult]],
    # Async as well
    Callable[["ScenarioExecutor"], Awaitable[None]],
    Callable[["ScenarioExecutor"], Awaitable[Optional[ScenarioResult]]],
]
