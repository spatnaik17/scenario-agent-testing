"""
Configuration module for Scenario.
"""

from typing import TYPE_CHECKING, Any, Optional, Type, Union
from pydantic import BaseModel

if TYPE_CHECKING:
    from scenario.scenario_agent_adapter import ScenarioAgentAdapter

    ScenarioAgentType = ScenarioAgentAdapter
else:
    ScenarioAgentType = Any


class ScenarioConfig(BaseModel):
    """
    Configuration class for the Scenario library.

    This allows users to set global configuration settings for the library,
    such as the LLM provider and model to use for the testing agent.
    """

    testing_agent: Optional[Type[ScenarioAgentType]] = None
    max_turns: Optional[int] = 10
    verbose: Optional[Union[bool, int]] = True
    cache_key: Optional[str] = None
    debug: Optional[bool] = False

    def merge(self, other: "ScenarioConfig") -> "ScenarioConfig":
        return ScenarioConfig(
            **{
                **self.items(),
                **other.items(),
            }
        )

    def items(self):
        return {k: getattr(self, k) for k in self.model_dump(exclude_none=True).keys()}
