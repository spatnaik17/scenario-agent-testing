"""
Scenario module: defines the core Scenario class for agent testing.
"""

from typing import Awaitable, List, Dict, Any, Optional, Callable, TypedDict, Union
import asyncio
import concurrent.futures
from functools import partial

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
    - Criteria to determine if the agent behaved correctly
    - Optional additional parameters
    """

    name: str
    description: str
    agent: Union[
        Callable[[str, Optional[Dict[str, Any]]], Dict[str, Any]],
        Callable[[str, Optional[Dict[str, Any]]], Awaitable[Dict[str, Any]]],
    ]
    criteria: List[str]

    def __init__(self, name: str, description: str, **kwargs):
        """Validate scenario configuration after initialization."""

        default_config = getattr(Scenario, "default_config", None)
        if default_config:
            kwargs = {**default_config.model_dump(), **kwargs}

        if not name:
            raise ValueError("Scenario name cannot be empty")
        kwargs["name"] = name

        if not description:
            raise ValueError("Scenario description cannot be empty")
        kwargs["description"] = description

        # TODO: allow not having any criteria, for scripted scenarios
        if not kwargs.get("criteria"):
            raise ValueError("Scenario must have at least one criteria")

        if kwargs.get("max_turns", 0) < 1:
            raise ValueError("max_turns must be a positive integer")

        # Ensure agent is callable
        if not callable(kwargs.get("agent")):
            raise ValueError("Agent must be a callable function")

        super().__init__(**kwargs)

    async def run(self, context: Optional[Dict[str, Any]] = None) -> ScenarioResult:
        """
        Run the scenario against the agent under test.

        Args:
            context: Optional initial context for the agent

        Returns:
            ScenarioResult containing the test outcome
        """

        # We'll use a thread pool to run the execution logic, we
        # require a separate thread because even though asyncio is
        # being used throughout, any user code on the callback can
        # be blocking, preventing them from running scenarios in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:

            def run_in_thread():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    return loop.run_until_complete(ScenarioExecutor(self).run(context))
                finally:
                    loop.close()

            # Run the function in the thread pool and await its result
            # This converts the thread's execution into a Future that the current
            # event loop can await without blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, run_in_thread)
            return result

    @classmethod
    def configure(
        cls,
        testing_agent: Optional[TestingAgent] = None,
        max_turns: Optional[int] = None,
        verbose: Optional[Union[bool, int]] = None,
        cache_key: Optional[str] = None,
        debug: Optional[bool] = None,
    ) -> None:
        existing_config = getattr(cls, "default_config", ScenarioConfig())

        cls.default_config = existing_config.merge(
            ScenarioConfig(
                testing_agent=testing_agent,
                max_turns=max_turns,
                verbose=verbose,
                cache_key=cache_key,
                debug=debug,
            )
        )
