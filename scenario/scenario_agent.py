from abc import ABC, abstractmethod
from typing import Any, ClassVar, List, Set, Union

from openai.types.chat import ChatCompletionMessageParam

from scenario.error_messages import message_return_error_message
from scenario.types import ScenarioResult

from .types import AgentInput, AgentReturnTypes, MessageTriggers


class ScenarioAgent(ABC):
    triggers: ClassVar[Set[MessageTriggers]]

    def __init__(self, input: AgentInput):
        super().__init__()
        pass

    async def _call_wrapped(self, input: AgentInput) -> AgentReturnTypes:
        return_value = await self.call(input)
        self._check_valid_return_type(return_value)
        return return_value

    def _check_valid_return_type(self, return_value: Any) -> None:
        def _is_valid_openai_message(message: Any) -> bool:
            return (isinstance(message, dict) and "role" in message) or hasattr(
                message, "role"
            )

        if (
            isinstance(return_value, str)
            or _is_valid_openai_message(return_value)
            or (
                isinstance(return_value, list)
                and all(_is_valid_openai_message(message) for message in return_value)
            )
            or isinstance(return_value, ScenarioResult)
        ):
            return

        raise ValueError(
            message_return_error_message(
                got=return_value, class_name=self.__class__.__name__
            )
        )

    @abstractmethod
    async def call(
        self, input: AgentInput
    ) -> AgentReturnTypes:
        pass

    def add_message_to_history(self, message: ChatCompletionMessageParam) -> None:
        """
        Optional method to add message to agent's history.
        Override this method if you want to manually define how to manage memory for adding messages to an agent's history.
        """
        pass  # Default: do nothing
