"""
Configuration module for Scenario.
"""

from typing import Optional
from pydantic import BaseModel

from scenario.testing_agent import TestingAgent

class ScenarioConfig(BaseModel):
    """
    Configuration class for the Scenario library.

    This allows users to set global configuration settings for the library,
    such as the LLM provider and model to use for the testing agent.
    """

    testing_agent: Optional[TestingAgent] = None
    max_turns: Optional[int] = 10
    verbose: Optional[bool] = True
    cache_key: Optional[str] = None

    def merge(self, other: "ScenarioConfig") -> "ScenarioConfig":
        return ScenarioConfig(
            testing_agent=other.testing_agent if other.testing_agent else self.testing_agent,
            max_turns=(other.max_turns if other.max_turns is not None else self.max_turns),
            verbose=(other.verbose if other.verbose is not None else self.verbose),
            cache_key=(
                other.cache_key if other.cache_key is not None else self.cache_key
            ),
        )
