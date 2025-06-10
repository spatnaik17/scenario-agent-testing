from abc import ABC, abstractmethod
from typing import ClassVar, Set

from openai.types.chat import ChatCompletionMessageParam

from .types import AgentInput, AgentReturnTypes, MessageTriggers


class ScenarioAgentAdapter(ABC):
    triggers: ClassVar[Set[MessageTriggers]] = {MessageTriggers.USER}

    def __init__(self, input: AgentInput):
        super().__init__()
        pass

    @abstractmethod
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        pass

    def add_message_to_history(self, message: ChatCompletionMessageParam) -> None:
        """
        Optional method to add message to agent's history.
        Override this method if you want to manually define how to manage memory for adding messages to an agent's history.
        """
        pass  # Default: do nothing
