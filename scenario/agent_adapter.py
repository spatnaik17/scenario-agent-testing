from abc import ABC, abstractmethod
from typing import ClassVar

from .types import AgentInput, AgentReturnTypes, AgentRole


class AgentAdapter(ABC):
    role: ClassVar[AgentRole] = AgentRole.AGENT

    @abstractmethod
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        pass
