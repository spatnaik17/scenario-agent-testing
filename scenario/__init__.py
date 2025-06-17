"""
Scenario: A testing library for conversational agents.
"""

# First import non-dependent modules
from .types import ScenarioResult, AgentInput, AgentRole, AgentReturnTypes
from .config import ScenarioConfig

# Then import modules with dependencies
from .scenario_executor import ScenarioExecutor
from .scenario_state import ScenarioState
from .agent_adapter import AgentAdapter
from .judge_agent import JudgeAgent
from .user_simulator_agent import UserSimulatorAgent
from .cache import scenario_cache
from .script import message, user, agent, judge, proceed, succeed, fail

# Import pytest plugin components
from .pytest_plugin import pytest_configure, scenario_reporter

run = ScenarioExecutor.run
configure = ScenarioConfig.configure
default_config = ScenarioConfig.default_config
cache = scenario_cache

__all__ = [
    # Functions
    "run",
    "configure",
    "default_config",
    "cache",

    # Script
    "message",
    "proceed",
    "succeed",
    "fail",
    "judge",
    "agent",
    "user",

    # Types
    "ScenarioResult",
    "AgentInput",
    "AgentRole",
    "ScenarioConfig",
    "AgentReturnTypes",

    # Classes
    "ScenarioExecutor",
    "ScenarioState",
    "AgentAdapter",
    "UserSimulatorAgent",
    "JudgeAgent",

    # Plugins
    "pytest_configure",
    "scenario_reporter",
    "scenario_cache",
]
__version__ = "0.1.0"