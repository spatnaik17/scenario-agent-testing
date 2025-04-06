"""
Scenario module: defines the core Scenario class for agent testing.
"""

from typing import Awaitable, List, Dict, Any, Optional, Callable, TypedDict, Union

from scenario.config import ScenarioConfig
from scenario.scenario_executor import ScenarioExecutor

from .result import ScenarioResult
from .testing_agent import TestingAgent

from openai.types.chat import ChatCompletionMessageParam

class AgentResult(TypedDict, total=False):
    message: str
    messages: List[ChatCompletionMessageParam]
    extra: Dict[str, Any]


class Scenario(ScenarioConfig):
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
    failure_criteria: List[str] = []
    strategy: Optional[str] = None

    def __init__(self, description: str, **kwargs):
        """Validate scenario configuration after initialization."""
        if not description:
            raise ValueError("Scenario description cannot be empty")
        kwargs["description"] = description

        if not kwargs.get("success_criteria"):
            raise ValueError("Scenario must have at least one success criterion")

        if kwargs.get("max_turns", 0) < 1:
            raise ValueError("max_turns must be a positive integer")

        # Ensure agent is callable
        if not callable(kwargs.get("agent")):
            raise ValueError("Agent must be a callable function")

        default_config = getattr(Scenario, "default_config", None)
        if default_config:
            kwargs = {**default_config.model_dump(), **kwargs}

        super().__init__(**kwargs)


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
        testing_agent: Optional[TestingAgent] = None,
        max_turns: Optional[int] = None,
        verbose: Optional[bool] = None,
        cache_key: Optional[str] = None,
    ) -> None:
        existing_config = getattr(cls, "default_config", ScenarioConfig())

        cls.default_config = existing_config.merge(
            ScenarioConfig(
                testing_agent=testing_agent,
                max_turns=max_turns,
                verbose=verbose,
                cache_key=cache_key,
            )
        )
