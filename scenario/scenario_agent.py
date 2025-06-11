from abc import ABC, abstractmethod
from typing import ClassVar, Set

from .types import AgentInput, AgentReturnTypes, MessageTriggers


class ScenarioAgentAdapter(ABC):
    triggers: ClassVar[Set[MessageTriggers]] = {MessageTriggers.USER}

    def __init__(self, input: AgentInput):
        super().__init__()
        pass

    @abstractmethod
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        pass
