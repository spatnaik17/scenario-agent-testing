"""
ScenarioExecutor module: holds the scenario execution logic and state, orchestrating the conversation between the testing agent and the agent under test.
"""

import json
import sys
from typing import TYPE_CHECKING, Awaitable, Dict, List, Any, Optional, Union, cast
import time
import termcolor

from scenario.error_messages import message_return_error_message
from scenario.utils import (
    print_openai_messages,
    safe_attr_or_key,
    safe_list_at,
    show_spinner,
)
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam

from .types import AgentInput, AgentReturnTypes, ScenarioResult
from .error_messages import default_config_error_message
from .cache import context_scenario
from pksuid import PKSUID

if TYPE_CHECKING:
    from scenario.scenario import Scenario
    from scenario.scenario_agent import ScenarioAgent


class ScenarioExecutor:
    scenario: "Scenario"
    messages: List[ChatCompletionMessageParam]
    thread_id: str
    current_turn: int

    _context: Optional[Dict[str, Any]]
    _testing_agent: "ScenarioAgent"
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

        TestingAgentClass = self.scenario.testing_agent
        if not TestingAgentClass:
            raise Exception(default_config_error_message)

        self._testing_agent = TestingAgentClass(
            input=AgentInput(
                thread_id=self.thread_id,
                messages=[],
                context={},
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
        next_message = await self._generate_user_message(self.messages)

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
            # TODO: temporary until main agent is converted to ScenarioAgent
            next_message_str = (
                str(self.last_user_message()["content"])
                if "content" in next_message
                else str(next_message)
            )

            # Get response from the agent under test
            start_time = time.time()

            context_scenario.set(self.scenario)
            with show_spinner(
                text="Agent:", color="blue", enabled=self.scenario.verbose
            ):
                agent_response = self.scenario.agent(next_message_str, self._context)
                if isinstance(agent_response, Awaitable):
                    agent_response = await agent_response

            has_valid_message = (
                "message" in agent_response
                and type(agent_response["message"]) is str
                and agent_response["message"] is not None
            )
            has_valid_messages = (
                "messages" in agent_response
                and isinstance(agent_response["messages"], list)
                and all(
                    "role" in msg or hasattr(msg, "role")
                    for msg in agent_response["messages"]
                )
            )
            if not has_valid_message and not has_valid_messages:
                raise Exception(
                    message_return_error_message(
                        got=agent_response,
                        class_name=self.scenario.agent.__class__.__name__,
                    )
                )

            messages: list[ChatCompletionMessageParam] = []
            if has_valid_messages and len(agent_response["messages"]) > 0:
                messages = agent_response["messages"]

                # Drop the first messages both if they are system or user messages
                if safe_attr_or_key(safe_list_at(messages, 0), "role") == "system":
                    messages = messages[1:]
                if safe_attr_or_key(safe_list_at(messages, 0), "role") == "user":
                    messages = messages[1:]

            if has_valid_message and self.scenario.verbose:
                print(
                    self._scenario_name() + termcolor.colored("Agent:", "blue"),
                    agent_response["message"],
                )

            if messages and self.scenario.verbose:
                print_openai_messages(self._scenario_name(), messages)

            if (
                self.scenario.verbose
                and "extra" in agent_response
                and len(agent_response["extra"].keys()) > 0
            ):
                print(
                    termcolor.colored(
                        "Extra:" + json.dumps(agent_response["extra"]),
                        "magenta",
                    )
                )
            response_time = time.time() - start_time
            agent_time += response_time

            if messages:
                self.messages.extend(agent_response["messages"])
            if "message" in agent_response:
                self.messages.append(
                    {"role": "assistant", "content": agent_response["message"]}
                )
            if "extra" in agent_response:
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": json.dumps(agent_response["extra"]),
                    }
                )

            # Generate the next message OR finish the test based on the agent's evaluation
            result = await self._generate_user_message(
                self.messages,
            )

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
        messages: List[ChatCompletionMessageParam],
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
            return_value = await self._testing_agent._call_wrapped(
                AgentInput(
                    thread_id=self.thread_id,
                    messages=messages,
                    context={},
                    scenario_state=self,
                ),
            )

            messages = []
            if isinstance(return_value, list):
                messages.extend(return_value)
            elif isinstance(return_value, str):
                messages.append(
                    ChatCompletionUserMessageParam(role="user", content=return_value)
                )
            elif isinstance(return_value, dict):
                messages.append(return_value)
            elif isinstance(return_value, ScenarioResult):
                return return_value

            self.messages.extend(messages)

            if self.scenario.verbose:
                print(
                    self._scenario_name() + termcolor.colored("User:", "green"),
                    self.last_user_message()["content"],
                )

            return messages

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
