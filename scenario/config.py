"""
Configuration module for Scenario.
"""

from typing import Optional, Union
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
    verbose: Optional[Union[bool, int]] = True
    cache_key: Optional[str] = None
    debug: Optional[bool] = False

    def merge(self, other: "ScenarioConfig") -> "ScenarioConfig":
        return ScenarioConfig(**{
            **self.model_dump(),
            **other.model_dump(exclude_none=True),
        })
