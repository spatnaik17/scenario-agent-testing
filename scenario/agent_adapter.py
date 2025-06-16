from abc import ABC, abstractmethod
from typing import ClassVar, Set

from .types import AgentInput, AgentReturnTypes, AgentRole


class AgentAdapter(ABC):
    roles: ClassVar[Set[AgentRole]] = {AgentRole.AGENT}

    @abstractmethod
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        pass
