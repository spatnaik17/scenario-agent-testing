"""
ScenarioExecutor module: holds the scenario execution logic and state, orchestrating the conversation between the testing agent and the agent under test.
"""

import sys
from typing import (
    TYPE_CHECKING,
    Awaitable,
    Callable,
    Dict,
    List,
    Any,
    Optional,
    Set,
    Tuple,
    Union,
)
import time
import termcolor

from scenario.utils import (
    await_if_awaitable,
    check_valid_return_type,
    convert_agent_return_types_to_openai_messages,
    print_openai_messages,
    show_spinner,
)
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionMessageToolCallParam,
)

from .types import AgentInput, ScenarioAgentRole, ScenarioResult, ScriptStep
from .error_messages import agent_response_not_awaitable
from .cache import context_scenario
from .scenario_agent_adapter import ScenarioAgentAdapter
from pksuid import PKSUID

if TYPE_CHECKING:
    from scenario.scenario import Scenario


class ScenarioExecutor:
    scenario: "Scenario"
    messages: List[ChatCompletionMessageParam]
    thread_id: str
    current_turn: int

    _context: Optional[Dict[str, Any]]
    _script: List[ScriptStep]
    _agents: List[ScenarioAgentAdapter]
    _total_start_time: float
    _pending_messages: Dict[int, List[ChatCompletionMessageParam]]

    _pending_roles_on_turn: List[ScenarioAgentRole] = []
    _pending_agents_on_turn: Set[ScenarioAgentAdapter] = set()
    _agent_times: Dict[int, float] = {}

    def __init__(
        self,
        scenario: "Scenario",
        context: Optional[Dict[str, Any]] = None,
        script: Optional[List[ScriptStep]] = None,
    ):
        super().__init__()

        self.scenario = scenario.model_copy()
        self._context = context
        self._script = script or [scenario.proceed()]
        self.current_turn = 0
        self.reset()

    def reset(self):
        self.messages = []
        self._agents = []
        self._pending_messages = {}
        self.thread_id = str(PKSUID("thread"))
        self._total_start_time = time.time()
        self._agent_times = {}

        for AgentClass in self.scenario.agents:
            self._agents.append(
                AgentClass(
                    input=AgentInput(
                        thread_id=self.thread_id,
                        messages=[],
                        new_messages=[],
                        context=self._context or {},
                        requested_role=list(AgentClass.roles)[0],
                        scenario_state=self,
                    )
                )
            )

        self._new_turn()
        self.current_turn = 0

        context_scenario.set(self.scenario)

    def add_message(
        self, message: ChatCompletionMessageParam, from_agent_idx: Optional[int] = None
    ):
        self.messages.append(message)

        # Broadcast the message to other agents
        for idx, _ in enumerate(self._agents):
            if idx == from_agent_idx:
                continue
            if idx not in self._pending_messages:
                self._pending_messages[idx] = []
            self._pending_messages[idx].append(message)

    def add_messages(
        self,
        messages: List[ChatCompletionMessageParam],
        from_agent_idx: Optional[int] = None,
    ):
        for message in messages:
            self.add_message(message, from_agent_idx)

    def _new_turn(self):
        self._pending_agents_on_turn = set(self._agents)
        self._pending_roles_on_turn = [
            ScenarioAgentRole.USER,
            ScenarioAgentRole.AGENT,
            ScenarioAgentRole.JUDGE,
        ]
        self.current_turn += 1

    async def step(self) -> Union[List[ChatCompletionMessageParam], ScenarioResult]:
        result = await self._step()
        if result is None:
            raise ValueError("No result from step")
        return result

    async def _step(
        self,
        go_to_next_turn=True,
        on_turn: Optional[
            Union[
                Callable[["ScenarioExecutor"], None],
                Callable[["ScenarioExecutor"], Awaitable[None]],
            ]
        ] = None,
    ) -> Union[List[ChatCompletionMessageParam], ScenarioResult, None]:
        if len(self._pending_roles_on_turn) == 0:
            if not go_to_next_turn:
                return None

            self._new_turn()

            if on_turn:
                await await_if_awaitable(on_turn(self))

            if self.current_turn >= (self.scenario.max_turns or 10):
                return self._reached_max_turns()

        current_role = self._pending_roles_on_turn[0]
        idx, next_agent = self._next_agent_for_role(current_role)
        if not next_agent:
            self._pending_roles_on_turn.pop(0)
            return await self._step(go_to_next_turn=go_to_next_turn, on_turn=on_turn)

        self._pending_agents_on_turn.remove(next_agent)
        return await self._call_agent(idx, role=current_role)

    def _next_agent_for_role(
        self, role: ScenarioAgentRole
    ) -> Tuple[int, Optional[ScenarioAgentAdapter]]:
        for idx, agent in enumerate(self._agents):
            if role in agent.roles and agent in self._pending_agents_on_turn:
                return idx, agent
        return -1, None

    def _reached_max_turns(self, error_message: Optional[str] = None) -> ScenarioResult:
        # If we reached max turns without conclusion, fail the test
        agent_roles_agents_idx = [
            idx
            for idx, agent in enumerate(self._agents)
            if ScenarioAgentRole.AGENT in agent.roles
        ]
        agent_times = [
            self._agent_times[idx]
            for idx in agent_roles_agents_idx
            if idx in self._agent_times
        ]
        agent_time = sum(agent_times)

        return ScenarioResult(
            success=False,
            messages=self.messages,
            reasoning=error_message
            or f"Reached maximum turns ({self.scenario.max_turns or 10}) without conclusion",
            total_time=time.time() - self._total_start_time,
            agent_time=agent_time,
        )

    async def run(self) -> ScenarioResult:
        """
        Run a scenario against the agent under test.

        Args:
            context: Optional initial context for the agent

        Returns:
            ScenarioResult containing the test outcome
        """

        if self.scenario.verbose:
            print("")  # new line

        self.reset()

        for script_step in self._script:
            callable = script_step(self)
            if isinstance(callable, Awaitable):
                result = await callable
            else:
                result = callable

            if isinstance(result, ScenarioResult):
                return result

        return self._reached_max_turns(
            """Reached end of script without conclusion, add one of the following to the end of the script:

- `scenario.proceed()` to let the simulation continue to play out
- `scenario.judge()` to force criteria judgement
- `scenario.succeed()` or `scenario.fail()` to end the test with an explicit result
            """
        )

    async def _call_agent(
        self, idx: int, role: ScenarioAgentRole
    ) -> Union[List[ChatCompletionMessageParam], ScenarioResult]:
        agent = self._agents[idx]

        if role == ScenarioAgentRole.USER and self.scenario.debug:
            print(
                f"\n{self._scenario_name()}{termcolor.colored('[Debug Mode]', 'yellow')} Press enter to continue or type a message to send"
            )
            input_message = input(
                self._scenario_name() + termcolor.colored("User: ", "green")
            )

            # Clear the input prompt lines completely
            for _ in range(3):
                sys.stdout.write("\033[F")  # Move up to the input line
                sys.stdout.write("\033[2K")  # Clear the entire input line
            sys.stdout.flush()  # Make sure the clearing is visible

            if input_message:
                return [
                    ChatCompletionUserMessageParam(role="user", content=input_message)
                ]

        with show_spinner(
            text=(
                "Judging..."
                if role == ScenarioAgentRole.JUDGE
                else f"{role.value if isinstance(role, ScenarioAgentRole) else role}:"
            ),
            color=(
                "blue"
                if role == ScenarioAgentRole.AGENT
                else "green" if role == ScenarioAgentRole.USER else "yellow"
            ),
            enabled=self.scenario.verbose,
        ):
            start_time = time.time()

            agent_response = agent.call(
                AgentInput(
                    # TODO: test thread_id
                    thread_id=self.thread_id,
                    messages=self.messages,
                    new_messages=self._pending_messages.get(idx, []),
                    # TODO: test context
                    context=self._context or {},
                    requested_role=role,
                    scenario_state=self,
                )
            )
            if not isinstance(agent_response, Awaitable):
                raise Exception(
                    agent_response_not_awaitable(agent.__class__.__name__),
                )

            agent_response = await agent_response

            if idx not in self._agent_times:
                self._agent_times[idx] = 0
            self._agent_times[idx] += time.time() - start_time

            self._pending_messages[idx] = []
            check_valid_return_type(agent_response, agent.__class__.__name__)

            messages = []
            if isinstance(agent_response, ScenarioResult):
                # TODO: should be an event
                return agent_response
            else:
                messages = convert_agent_return_types_to_openai_messages(
                    agent_response,
                    role="user" if role == ScenarioAgentRole.USER else "assistant",
                )

            self.add_messages(messages, from_agent_idx=idx)

            if messages and self.scenario.verbose:
                print_openai_messages(
                    self._scenario_name(),
                    [m for m in messages if m["role"] != "system"],
                )

            return messages

    def _scenario_name(self):
        if self.scenario.verbose == 2:
            return termcolor.colored(f"[Scenario: {self.scenario.name}] ", "yellow")
        else:
            return ""

    # State access utils

    def last_message(self) -> ChatCompletionMessageParam:
        if len(self.messages) == 0:
            raise ValueError("No messages found")
        return self.messages[-1]

    def last_user_message(self) -> ChatCompletionUserMessageParam:
        user_messages = [m for m in self.messages if m["role"] == "user"]
        if not user_messages:
            raise ValueError("No user messages found")
        return user_messages[-1]

    def last_tool_call(
        self, tool_name: str
    ) -> Optional[ChatCompletionMessageToolCallParam]:
        for message in reversed(self.messages):
            if message["role"] == "assistant" and "tool_calls" in message:
                for tool_call in message["tool_calls"]:
                    if tool_call["function"]["name"] == tool_name:
                        return tool_call
        return None

    def has_tool_call(self, tool_name: str) -> bool:
        return self.last_tool_call(tool_name) is not None

    # Scripting utils

    async def message(self, message: ChatCompletionMessageParam) -> None:
        if message["role"] == "user":
            await self._script_call_agent(ScenarioAgentRole.USER, message)
        elif message["role"] == "assistant":
            await self._script_call_agent(ScenarioAgentRole.AGENT, message)
        else:
            self.add_message(message)

    async def user(
        self, content: Optional[Union[str, ChatCompletionMessageParam]] = None
    ) -> None:
        await self._script_call_agent(ScenarioAgentRole.USER, content)

    async def agent(
        self, content: Optional[Union[str, ChatCompletionMessageParam]] = None
    ) -> None:
        await self._script_call_agent(ScenarioAgentRole.AGENT, content)

    async def judge(
        self, content: Optional[Union[str, ChatCompletionMessageParam]] = None
    ) -> Optional[ScenarioResult]:
        return await self._script_call_agent(ScenarioAgentRole.JUDGE, content)

    async def proceed(
        self,
        turns: Optional[int] = None,
        on_turn: Optional[
            Union[
                Callable[["ScenarioExecutor"], None],
                Callable[["ScenarioExecutor"], Awaitable[None]],
            ]
        ] = None,
        on_step: Optional[
            Union[
                Callable[["ScenarioExecutor"], None],
                Callable[["ScenarioExecutor"], Awaitable[None]],
            ]
        ] = None,
    ) -> Optional[ScenarioResult]:
        initial_turn: Optional[int] = None
        while True:
            next_message = await self._step(
                on_turn=on_turn,
                go_to_next_turn=(
                    turns is None
                    or initial_turn is None
                    or (self.current_turn + 1 < initial_turn + turns)
                ),
            )

            if initial_turn is None:
                initial_turn = self.current_turn

            if next_message is None:
                break

            if on_step:
                await await_if_awaitable(on_step(self))

            if isinstance(next_message, ScenarioResult):
                return next_message

    async def succeed(self) -> ScenarioResult:
        return ScenarioResult(
            success=True,
            messages=self.messages,
            reasoning="Scenario marked as successful with scenario.succeed()",
            passed_criteria=self.scenario.criteria,
        )

    async def fail(self) -> ScenarioResult:
        return ScenarioResult(
            success=False,
            messages=self.messages,
            reasoning="Scenario marked as failed with scenario.fail()",
            passed_criteria=self.scenario.criteria,
        )

    async def _script_call_agent(
        self,
        role: ScenarioAgentRole,
        content: Optional[Union[str, ChatCompletionMessageParam]] = None,
    ) -> Optional[ScenarioResult]:
        idx, next_agent = self._next_agent_for_role(role)
        if not next_agent:
            self._new_turn()
            idx, next_agent = self._next_agent_for_role(role)

            if not next_agent:
                if content:
                    raise ValueError(
                        f"Cannot generate a message for role `{role.value}` with content `{content}` because no agent with this role was found"
                    )
                raise ValueError(
                    f"Cannot generate a message for role `{role.value}` because no agent with this role was found"
                )

        self._pending_agents_on_turn.remove(next_agent)
        self._pending_roles_on_turn.remove(role)

        if content:
            if isinstance(content, str):
                message = ChatCompletionUserMessageParam(role="user", content=content)
            else:
                message = content

            self.add_message(message)
            if self.scenario.verbose:
                print_openai_messages(self._scenario_name(), [message])
            return

        result = await self._call_agent(idx, role=role)
        if isinstance(result, ScenarioResult):
            return result
