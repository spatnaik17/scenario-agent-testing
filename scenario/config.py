"""
Configuration module for Scenario.
"""

from typing import Optional, TypedDict
from dataclasses import dataclass, field


class TestingAgentConfig(TypedDict, total=False):
    """
    Configuration class for the TestingAgent.
    """

    model: str
    api_key: Optional[str]
    temperature: float
    max_tokens: Optional[int]


@dataclass
class ScenarioConfig:
    """
    Configuration class for the Scenario library.

    This allows users to set global configuration settings for the library,
    such as the LLM provider and model to use for the testing agent.
    """

    testing_agent: TestingAgentConfig = field(
        default_factory=lambda: TestingAgentConfig(
            temperature=0,
        )
    )
    verbose: bool = True
