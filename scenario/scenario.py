"""
Scenario module: defines the core Scenario class for agent testing.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable

import termcolor

from scenario.config import ScenarioConfig

from .result import ScenarioResult
from .testing_agent import DEFAULT_TESTING_AGENT, TestingAgent
from .error_messages import default_config_error_message


@dataclass
class Scenario:
    """
    A scenario represents a specific testing case for an agent.

    It includes:
    - A description of the scenario
    - Success criteria to determine if the agent behaved correctly
    - Failure criteria to determine if the agent failed
    - An optional strategy that guides the testing agent
    - Optional additional parameters
    """

    description: str
    agent: Callable[[str, Optional[Dict[str, Any]]], Dict[str, Any]]
    success_criteria: List[str]
    failure_criteria: List[str]
    testing_agent: TestingAgent = DEFAULT_TESTING_AGENT
    strategy: Optional[str] = None
    max_turns: int = 10
    config: ScenarioConfig = None  # type: ignore

    def __post_init__(self) -> None:
        """Validate scenario configuration after initialization."""
        if not self.description:
            raise ValueError("Scenario description cannot be empty")

        if not self.success_criteria:
            raise ValueError("Scenario must have at least one success criterion")

        if self.max_turns < 1:
            raise ValueError("max_turns must be a positive integer")

        if not self.failure_criteria:
            self.failure_criteria = []

        # Ensure agent is callable
        if not callable(self.agent):
            raise ValueError("Agent must be a callable function")

        if self.config is None:
            if not hasattr(Scenario, "default_config"):
                raise Exception(default_config_error_message)
            self.config = Scenario.default_config

    def run(self, context: Optional[Dict[str, Any]] = None) -> ScenarioResult:
        """
        Run the scenario against the agent under test.

        Args:
            context: Optional initial context for the agent

        Returns:
            ScenarioResult containing the test outcome
        """
        # Run the scenario using the testing agent
        return self.testing_agent.run_scenario(self.agent, self, context)

    @classmethod
    def configure(
        cls,
        testing_agent_model: str,
        api_key: Optional[str] = None,
        temperature: float = 0,
        max_tokens: int = 1000,
        verbose: bool = True,
        timeout: int = 60,
    ) -> None:
        cls.default_config = ScenarioConfig(
            testing_agent_model=testing_agent_model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            verbose=verbose,
            timeout=timeout,
        )
