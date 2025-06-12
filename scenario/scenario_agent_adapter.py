from abc import ABC, abstractmethod
from typing import ClassVar, Set

from .types import AgentInput, AgentReturnTypes, ScenarioAgentRole


class ScenarioAgentAdapter(ABC):
    roles: ClassVar[Set[ScenarioAgentRole]] = {ScenarioAgentRole.AGENT}

    def __init__(self, input: AgentInput):
        super().__init__()
        pass

    @abstractmethod
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        pass
