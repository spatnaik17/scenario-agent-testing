"""
ScenarioExecutor module: holds the scenario execution logic and state, orchestrating the conversation between the testing agent and the agent under test.
"""

import sys
from typing import TYPE_CHECKING, Awaitable, Dict, List, Any, Optional, Union
import time
import termcolor

import scenario.utils
from scenario.utils import (
    check_valid_return_type,
    convert_agent_return_types_to_openai_messages,
    print_openai_messages,
    show_spinner,
)
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam

from .types import AgentInput, ScenarioResult
from .error_messages import agent_response_not_awaitable, default_config_error_message
from .cache import context_scenario
from pksuid import PKSUID

if TYPE_CHECKING:
    from scenario.scenario import Scenario
    from scenario.scenario_agent import ScenarioAgentAdapter


class ScenarioExecutor:
    scenario: "Scenario"
    messages: List[ChatCompletionMessageParam]
    thread_id: str
    current_turn: int

    _context: Optional[Dict[str, Any]]
    _agent: "ScenarioAgentAdapter"
    _testing_agent: "ScenarioAgentAdapter"
    _total_start_time: float

    def __init__(self, scenario: "Scenario", context: Optional[Dict[str, Any]] = None):
        super().__init__()

        self.scenario = scenario.model_copy()
        self._context = context
        self.reset()

    def reset(self):
        self.messages = []
        self.thread_id = str(PKSUID("thread"))
        self._total_start_time = time.time()
        self.current_turn = 0

        # TODO: array of agents instead
        TestingAgentClass = self.scenario.testing_agent
        if not TestingAgentClass:
            raise Exception(default_config_error_message)

        self._testing_agent = TestingAgentClass(
            input=AgentInput(
                thread_id=self.thread_id,
                messages=[],
                context=self._context or {},
                scenario_state=self,
            )
        )

        AgentClass = self.scenario.agent
        self._agent = AgentClass(
            input=AgentInput(
                thread_id=self.thread_id,
                messages=[],
                context=self._context or {},
                scenario_state=self,
            )
        )

        context_scenario.set(self.scenario)

    def add_message(self, message: ChatCompletionMessageParam):
        self.messages.append(message)

    async def step(self):
        pass

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

        # Run the initial testing agent prompt to get started
        next_message = await self._generate_user_message()

        if isinstance(next_message, ScenarioResult):
            raise Exception(
                "Unexpectedly generated a ScenarioResult for the initial message",
                next_message.__repr__(),
            )

        # Execute the conversation
        max_turns = self.scenario.max_turns or 10
        agent_time = 0

        # Start the test with the initial message
        while self.current_turn < max_turns:
            # Get response from the agent under test
            start_time = time.time()

            context_scenario.set(self.scenario)
            await self._generate_agent_response()

            response_time = time.time() - start_time
            agent_time += response_time

            # Generate the next message OR finish the test based on the agent's evaluation
            result = await self._generate_user_message()

            # Check if the result is a ScenarioResult (indicating test completion)
            if isinstance(result, ScenarioResult):
                result.total_time = time.time() - start_time
                result.agent_time = agent_time
                return result

            # Otherwise, it's the next message to send to the agent
            next_message = result

            # Increment turn counter
            self.current_turn += 1

        # If we reached max turns without conclusion, fail the test
        return ScenarioResult(
            success=False,
            messages=self.messages,
            reasoning=f"Reached maximum turns ({max_turns}) without conclusion",
            total_time=time.time() - self._total_start_time,
            agent_time=agent_time,
        )

    async def _generate_user_message(
        self,
    ) -> Union[List[ChatCompletionMessageParam], ScenarioResult]:
        if self.scenario.debug:
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
            text=f"{self._scenario_name()}User:",
            color="green",
            enabled=self.scenario.verbose,
        ):
            return await self._call_agent(self._testing_agent, reverse_roles=True)

    async def _generate_agent_response(
        self,
    ) -> List[ChatCompletionMessageParam]:
        with show_spinner(text="Agent:", color="blue", enabled=self.scenario.verbose):
            agent_response = await self._call_agent(self._agent)

        if isinstance(agent_response, ScenarioResult):
            raise Exception(
                "Unexpectedly generated a ScenarioResult for the agent response",
                agent_response.__repr__(),
            )

        return agent_response

    async def _call_agent(
        self, agent: "ScenarioAgentAdapter", reverse_roles: bool = False
    ) -> Union[List[ChatCompletionMessageParam], ScenarioResult]:
        agent_response = agent.call(
            AgentInput(
                # TODO: test thread_id
                thread_id=self.thread_id,
                messages=self.messages,
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
        check_valid_return_type(agent_response, agent.__class__.__name__)

        messages = []
        if isinstance(agent_response, list):
            messages.extend(agent_response)
        elif isinstance(agent_response, str):
            messages.append(
                {
                    "role": "user" if reverse_roles else "assistant",
                    "content": agent_response,
                }
            )
        elif isinstance(agent_response, dict):
            messages.append(agent_response)

        if isinstance(agent_response, ScenarioResult):
            # TODO: should be an event
            return agent_response
        else:
            messages = convert_agent_return_types_to_openai_messages(
                agent_response, role="user" if reverse_roles else "assistant"
            )

        self.messages.extend(messages)

        if messages and self.scenario.verbose:
            print_openai_messages(
                self._scenario_name(), [m for m in messages if m["role"] != "system"]
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
