"""
Scenario module: defines the core Scenario class for agent testing.
"""

from typing import (
    Awaitable,
    Callable,
    List,
    Dict,
    Any,
    Optional,
    Type,
    TypedDict,
    Union,
)
import asyncio
import concurrent.futures

from scenario.config import ScenarioConfig
from scenario.error_messages import (
    default_config_error_message,
    message_invalid_agent_type,
)
from scenario.scenario_agent_adapter import ScenarioAgentAdapter
from scenario.scenario_executor import ScenarioExecutor

from .types import ScenarioResult, ScriptStep

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
    agents: List[Type[ScenarioAgentAdapter]]
    criteria: List[str]

    def __init__(
        self,
        name: str,
        description: str,
        criteria: List[str] = [],
        agent: Optional[Type[ScenarioAgentAdapter]] = None,
        testing_agent: Optional[Type[ScenarioAgentAdapter]] = None,
        agents: List[Type[ScenarioAgentAdapter]] = [],
        max_turns: Optional[int] = None,
        verbose: Optional[Union[bool, int]] = None,
        cache_key: Optional[str] = None,
        debug: Optional[bool] = None,
    ):
        """Validate scenario configuration after initialization."""

        config = ScenarioConfig(
            testing_agent=testing_agent,
            max_turns=max_turns,
            verbose=verbose,
            cache_key=cache_key,
            debug=debug,
        )

        kwargs = config.items()
        default_config: Optional[ScenarioConfig] = getattr(
            Scenario, "default_config", None
        )
        if default_config:
            kwargs = default_config.merge(config).items()

        if not name:
            raise ValueError("Scenario name cannot be empty")
        kwargs["name"] = name

        if not description:
            raise ValueError("Scenario description cannot be empty")
        kwargs["description"] = description

        kwargs["criteria"] = criteria

        if kwargs.get("max_turns", 10) < 1:
            raise ValueError("max_turns must be a positive integer")

        if not agents and not agent:
            raise ValueError(
                "Missing required argument `agent`. Either `agent` or `agents` argument must be provided for the Scenario"
            )

        if not agents and not kwargs.get("testing_agent"):
            raise Exception(default_config_error_message)

        agents = agents or [
            kwargs.get("testing_agent"),
            agent,  # type: ignore
        ]

        # Ensure each agent is a ScenarioAgentAdapter
        for agent in agents:
            if (
                not agent
                or not isinstance(agent, type)
                or not issubclass(agent, ScenarioAgentAdapter)
            ):
                raise ValueError(message_invalid_agent_type(agent))
        kwargs["agents"] = agents

        super().__init__(**kwargs)

    def script(self, script: List[ScriptStep]):
        class ScriptedScenario:
            def __init__(self, scenario: "Scenario"):
                self._scenario = scenario

            async def run(
                self, context: Optional[Dict[str, Any]] = None
            ) -> ScenarioResult:
                return await self._scenario._run(context, script)

        return ScriptedScenario(self)

    async def run(self, context: Optional[Dict[str, Any]] = None) -> ScenarioResult:
        """
        Run the scenario against the agent under test.

        Args:
            context: Optional initial context for the agent

        Returns:
            ScenarioResult containing the test outcome
        """

        return await self._run(context, None)

    async def _run(
        self,
        context: Optional[Dict[str, Any]] = None,
        script: Optional[List[ScriptStep]] = None,
    ) -> ScenarioResult:
        # We'll use a thread pool to run the execution logic, we
        # require a separate thread because even though asyncio is
        # being used throughout, any user code on the callback can
        # be blocking, preventing them from running scenarios in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:

            def run_in_thread():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    return loop.run_until_complete(
                        ScenarioExecutor(self, context, script).run()
                    )
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
        testing_agent: Optional[Type[ScenarioAgentAdapter]] = None,
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

    # Scenario Scripting

    def message(self, message: ChatCompletionMessageParam) -> ScriptStep:
        return lambda state: state.message(message)

    def user(
        self, content: Optional[Union[str, ChatCompletionMessageParam]] = None
    ) -> ScriptStep:
        return lambda state: state.user(content)

    def agent(
        self, content: Optional[Union[str, ChatCompletionMessageParam]] = None
    ) -> ScriptStep:
        return lambda state: state.agent(content)

    def judge(
        self, content: Optional[Union[str, ChatCompletionMessageParam]] = None
    ) -> ScriptStep:
        return lambda state: state.judge(content)

    def proceed(
        self,
        turns: Optional[int] = None,
        on_turn: Optional[
            Union[
                Callable[[ScenarioExecutor], None],
                Callable[[ScenarioExecutor], Awaitable[None]],
            ]
        ] = None,
        on_step: Optional[
            Union[
                Callable[[ScenarioExecutor], None],
                Callable[[ScenarioExecutor], Awaitable[None]],
            ]
        ] = None,
    ) -> ScriptStep:
        return lambda state: state.proceed(turns, on_turn, on_step)

    def succeed(self) -> ScriptStep:
        return lambda state: state.succeed()

    def fail(self) -> ScriptStep:
        return lambda state: state.fail()
