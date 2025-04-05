"""
Configuration module for Scenario.
"""

import os
from pathlib import Path
from typing import Optional, TypedDict
from joblib import Memory
from pydantic import BaseModel


class TestingAgentConfig(TypedDict, total=False):
    """
    Configuration class for the TestingAgent.
    """

    model: str
    api_key: Optional[str]
    temperature: float
    max_tokens: Optional[int]


class ScenarioConfig(BaseModel):
    """
    Configuration class for the Scenario library.

    This allows users to set global configuration settings for the library,
    such as the LLM provider and model to use for the testing agent.
    """

    testing_agent: TestingAgentConfig = TestingAgentConfig(
        temperature=0,
    )
    verbose: Optional[bool] = True
    cache_key: Optional[str] = None

    def merge(self, other: "ScenarioConfig") -> "ScenarioConfig":
        return ScenarioConfig(
            testing_agent=self.testing_agent | (other.testing_agent or {}),
            verbose=(other.verbose if other.verbose is not None else self.verbose),
            cache_key=(
                other.cache_key if other.cache_key is not None else self.cache_key
            ),
        )


def get_cache() -> Memory:
    """Get a cross-platform cache directory for scenario."""
    home_dir = str(Path.home())
    cache_dir = os.path.join(home_dir, ".scenario", "cache")

    return Memory(location=os.environ.get("SCENARIO_CACHE_DIR", cache_dir), verbose=0)
