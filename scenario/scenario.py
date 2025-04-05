"""
Scenario module: defines the core Scenario class for agent testing.
"""

from dataclasses import dataclass
from typing import Awaitable, List, Dict, Any, Optional, Callable, TypedDict, Union

from scenario.config import ScenarioConfig, TestingAgentConfig
from scenario.scenario_executor import ScenarioExecutor

from .result import ScenarioResult
from .testing_agent import DEFAULT_TESTING_AGENT, TestingAgent
from .error_messages import default_config_error_message
from openai.types.chat import ChatCompletionMessageParam


class AgentResult(TypedDict, total=False):
    message: str
    messages: List[ChatCompletionMessageParam]
    extra: Dict[str, Any]


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
    agent: Union[
        Callable[[str, Optional[Dict[str, Any]]], Dict[str, Any]],
        Callable[[str, Optional[Dict[str, Any]]], Awaitable[Dict[str, Any]]],
    ]
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
            self.config = self.config.merge(Scenario.default_config)

    async def run(self, context: Optional[Dict[str, Any]] = None) -> ScenarioResult:
        """
        Run the scenario against the agent under test.

        Args:
            context: Optional initial context for the agent

        Returns:
            ScenarioResult containing the test outcome
        """
        # Run the scenario using the testing agent
        return await ScenarioExecutor(self).run(context)

    @classmethod
    def configure(
        cls,
        testing_agent: Optional[TestingAgentConfig] = None,
        verbose: Optional[bool] = None,
        cache_key: Optional[str] = None,
    ) -> None:
        existing_config = getattr(cls, "default_config", ScenarioConfig())

        cls.default_config = existing_config.merge(
            ScenarioConfig(
                testing_agent=testing_agent or {},
                verbose=verbose,
                cache_key=cache_key,
            )
        )

    def copy(self) -> "Scenario":
        return Scenario(
            description=self.description,
            agent=self.agent,
            success_criteria=self.success_criteria,
            failure_criteria=self.failure_criteria,
            testing_agent=self.testing_agent,
            strategy=self.strategy,
            max_turns=self.max_turns,
            config=self.config,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the scenario to a dictionary representation."""
        return {
            "description": self.description,
            "success_criteria": self.success_criteria,
            "failure_criteria": self.failure_criteria,
            "strategy": self.strategy,
            "max_turns": self.max_turns,
            "config": self.config.model_dump(),
        }
