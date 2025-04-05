"""
Scenario: A testing library for conversational agents.
"""

# First import non-dependent modules
from .result import ScenarioResult
from .config import ScenarioConfig

# Then import modules with dependencies
from .testing_agent import TestingAgent, DEFAULT_TESTING_AGENT
from .scenario import Scenario

# Import pytest plugin components
from .pytest_plugin import pytest_configure, scenario_reporter

__all__ = [
    "Scenario",
    "TestingAgent",
    "ScenarioResult",
    "ScenarioConfig",
    "DEFAULT_TESTING_AGENT",
    "pytest_configure",
    "scenario_reporter"
]
__version__ = "0.1.0"