"""
ScenarioExecutor module: holds the scenario execution logic and state, orchestrating the conversation between the testing agent and the agent under test.
"""

import sys
from typing import (
    TYPE_CHECKING,
    Awaitable,
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
    check_valid_return_type,
    convert_agent_return_types_to_openai_messages,
    print_openai_messages,
    show_spinner,
)
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam

from .types import AgentInput, ScenarioAgentRole, ScenarioResult
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
    _agents: List[ScenarioAgentAdapter]
    _total_start_time: float
    _pending_messages: Dict[int, List[ChatCompletionMessageParam]]

    _pending_roles_on_turn: List[ScenarioAgentRole] = []
    _pending_agents_on_turn: Set[ScenarioAgentAdapter] = set()
    _agent_times: Dict[int, float] = {}

    def __init__(self, scenario: "Scenario", context: Optional[Dict[str, Any]] = None):
        super().__init__()

        self.scenario = scenario.model_copy()
        self._context = context
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
        if len(self._pending_roles_on_turn) == 0:
            self._new_turn()
            if self.current_turn >= (self.scenario.max_turns or 10):
                return self._reached_max_turns()

        current_role = self._pending_roles_on_turn[0]
        idx, next_agent = self._next_agent_for_role(current_role)
        if not next_agent:
            self._pending_roles_on_turn.pop(0)
            return await self.step()

        self._pending_agents_on_turn.remove(next_agent)
        if current_role == ScenarioAgentRole.USER:
            return await self._call_agent(idx, reverse_roles=True)
        else:
            return await self._call_agent(idx)

    def _next_agent_for_role(
        self, role: ScenarioAgentRole
    ) -> Tuple[int, Optional[ScenarioAgentAdapter]]:
        for idx, agent in enumerate(self._agents):
            if role in agent.roles and agent in self._pending_agents_on_turn:
                return idx, agent
        return -1, None

    def _reached_max_turns(self) -> ScenarioResult:
        # If we reached max turns without conclusion, fail the test
        agent_roles_agents_idx = [
            idx
            for idx, agent in enumerate(self._agents)
            if ScenarioAgentRole.AGENT in agent.roles
        ]
        agent_times = [self._agent_times[idx] for idx in agent_roles_agents_idx]
        agent_time = sum(agent_times)

        return ScenarioResult(
            success=False,
            messages=self.messages,
            reasoning=f"Reached maximum turns ({self.scenario.max_turns or 10}) without conclusion",
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

        while True:
            next_message = await self.step()

            if isinstance(next_message, ScenarioResult):
                return next_message

    async def _call_agent(
        self, idx: int, reverse_roles: bool = False
    ) -> Union[List[ChatCompletionMessageParam], ScenarioResult]:
        agent = self._agents[idx]

        first_role = next(iter(agent.roles), "Unknown")

        if first_role == ScenarioAgentRole.USER and self.scenario.debug:
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
            text=f"{first_role.value if isinstance(first_role, ScenarioAgentRole) else first_role}:",
            color=(
                "blue"
                if first_role == ScenarioAgentRole.AGENT
                else "green" if first_role == ScenarioAgentRole.USER else "yellow"
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
                    agent_response, role="user" if reverse_roles else "assistant"
                )

            self.add_messages(messages, from_agent_idx=idx)

            if messages and self.scenario.verbose:
                print_openai_messages(
                    self._scenario_name(),
                    [m for m in messages if m["role"] != "system"],
                )

            return messages

    def last_message(self) -> ChatCompletionMessageParam:
        if len(self.messages) == 0:
            raise ValueError("No messages found")
        return self.messages[-1]

    def last_user_message(self) -> ChatCompletionUserMessageParam:
        user_messages = [m for m in self.messages if m["role"] == "user"]
        if not user_messages:
            raise ValueError("No user messages found")
        return user_messages[-1]

    def _scenario_name(self):
        if self.scenario.verbose == 2:
            return termcolor.colored(f"[Scenario: {self.scenario.name}] ", "yellow")
        else:
            return ""
