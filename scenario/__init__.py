"""
Scenario: A testing library for conversational agents.
"""

# First import non-dependent modules
from .types import ScenarioResult, AgentInput, ScenarioAgentRole, AgentReturnTypes
from .config import ScenarioConfig

# Then import modules with dependencies
from .scenario_agent_adapter import ScenarioAgentAdapter
from .testing_agent import TestingAgent
from .scenario import Scenario
from .cache import scenario_cache

# Import pytest plugin components
from .pytest_plugin import pytest_configure, scenario_reporter

__all__ = [
    # Types
    "ScenarioResult",
    "AgentInput",
    "ScenarioAgentRole",
    "ScenarioConfig",
    "AgentReturnTypes",

    # Classes
    "Scenario",
    "ScenarioAgentAdapter",
    "TestingAgent",

    # Plugins
    "pytest_configure",
    "scenario_reporter",
    "scenario_cache",
]
__version__ = "0.1.0"