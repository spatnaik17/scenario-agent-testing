"""
Configuration module for Scenario.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class ScenarioConfig:
    """
    Configuration class for the Scenario library.

    This allows users to set global configuration settings for the library,
    such as the LLM provider and model to use for the testing agent.
    """

    testing_agent_model: str = "openai/gpt-4o-mini"
    api_key: Optional[str] = None
    temperature: float = 0
    max_tokens: int = 1000
    verbose: bool = True
    timeout: int = 60
