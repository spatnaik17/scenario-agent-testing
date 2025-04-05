"""
Scenario module: defines the core Scenario class for agent testing.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable

from scenario.config import ScenarioConfig, TestingAgentConfig
from scenario.scenario_executor import ScenarioExecutor

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
            if not hasattr(
                Scenario, "default_config"
            ) or not Scenario.default_config.testing_agent.get("model"):
                raise Exception(default_config_error_message)
            self.config = Scenario.default_config
        else:
            # Merge the default config with the user-provided config
            self.config = ScenarioConfig(
                testing_agent=Scenario.default_config.testing_agent
                | self.config.testing_agent
            )

    def run(self, context: Optional[Dict[str, Any]] = None) -> ScenarioResult:
        """
        Run the scenario against the agent under test.

        Args:
            context: Optional initial context for the agent

        Returns:
            ScenarioResult containing the test outcome
        """
        # Run the scenario using the testing agent
        return ScenarioExecutor(self).run(context)

    @classmethod
    def configure(
        cls,
        testing_agent: Optional[TestingAgentConfig] = None,
        verbose: Optional[bool] = None,
    ) -> None:
        existing_config = getattr(cls, "default_config", ScenarioConfig())

        # Merge the default config with the new provided config
        cls.default_config = ScenarioConfig(
            testing_agent=existing_config.testing_agent | (testing_agent or {}),
            verbose=verbose if verbose is not None else existing_config.verbose,
        )
