"""
ScenarioExecutor module: holds the scenario execution logic and state, orchestrating the conversation between the testing agent and the agent under test.
"""

import json
import sys
from typing import TYPE_CHECKING, Awaitable, Dict, List, Any, Optional, Union
import time
import termcolor

from scenario.error_messages import message_return_error_message
from scenario.utils import print_openai_messages, safe_attr_or_key, safe_list_at, show_spinner
from openai.types.chat import ChatCompletionMessageParam

from .result import ScenarioResult
from .error_messages import default_config_error_message
from .cache import context_scenario

if TYPE_CHECKING:
    from scenario.scenario import Scenario



class ScenarioExecutor:
    def __init__(self, scenario: "Scenario"):
        self.scenario = scenario.model_copy()

        testing_agent = scenario.testing_agent
        if not testing_agent or not testing_agent.model:
            raise Exception(default_config_error_message)
        self.testing_agent = testing_agent

        self.conversation: List[Dict[str, Any]] = []

    async def run(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> ScenarioResult:
        """
        Run a scenario against the agent under test.

        Args:
            context: Optional initial context for the agent

        Returns:
            ScenarioResult containing the test outcome
        """

        if self.scenario.verbose:
            print("")  # new line

        # Run the initial testing agent prompt to get started
        total_start_time = time.time()
        context_scenario.set(self.scenario)
        next_message = self._generate_next_message(
            self.scenario, self.conversation, first_message=True
        )

        if isinstance(next_message, ScenarioResult):
            raise Exception(
                "Unexpectedly generated a ScenarioResult for the initial message",
                next_message.__repr__(),
            )
        elif self.scenario.verbose:
            print(self._scenario_name() + termcolor.colored("User:", "green"), next_message)

        # Execute the conversation
        current_turn = 0
        max_turns = self.scenario.max_turns or 10
        agent_time = 0

        # Start the test with the initial message
        while current_turn < max_turns:
            # Record the testing agent's message
            self.conversation.append({"role": "user", "content": next_message})

            # Get response from the agent under test
            start_time = time.time()

            context_scenario.set(self.scenario)
            with show_spinner(text="Agent:", color="blue", enabled=self.scenario.verbose):
                agent_response = self.scenario.agent(next_message, context)
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
                raise Exception(message_return_error_message(agent_response))

            messages: list[ChatCompletionMessageParam] = []
            if has_valid_messages and len(agent_response["messages"]) > 0:
                messages = agent_response["messages"]

                # Drop the first messages both if they are system or user messages
                if safe_attr_or_key(safe_list_at(messages, 0), "role") == "system":
                    messages = messages[1:]
                if safe_attr_or_key(safe_list_at(messages, 0), "role") == "user":
                    messages = messages[1:]

            if has_valid_message and self.scenario.verbose:
                print(self._scenario_name() + termcolor.colored("Agent:", "blue"), agent_response["message"])

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
                self.conversation.extend(agent_response["messages"])
            if "message" in agent_response:
                self.conversation.append(
                    {"role": "assistant", "content": agent_response["message"]}
                )
            if "extra" in agent_response:
                self.conversation.append(
                    {
                        "role": "assistant",
                        "content": json.dumps(agent_response["extra"]),
                    }
                )

            # Generate the next message OR finish the test based on the agent's evaluation
            result = self._generate_next_message(
                self.scenario,
                self.conversation,
                last_message=current_turn == max_turns - 1,
            )

            # Check if the result is a ScenarioResult (indicating test completion)
            if isinstance(result, ScenarioResult):
                result.total_time = time.time() - start_time
                result.agent_time = agent_time
                return result
            elif self.scenario.verbose:
                print(self._scenario_name() + termcolor.colored("User:", "green"), result)

            # Otherwise, it's the next message to send to the agent
            next_message = result

            # Increment turn counter
            current_turn += 1

        # If we reached max turns without conclusion, fail the test
        return ScenarioResult.failure_result(
            conversation=self.conversation,
            reasoning=f"Reached maximum turns ({max_turns}) without conclusion",
            total_time=time.time() - total_start_time,
            agent_time=agent_time,
        )

    def _generate_next_message(
        self,
        scenario: "Scenario",
        conversation: List[Dict[str, Any]],
        first_message: bool = False,
        last_message: bool = False,
    ) -> Union[str, ScenarioResult]:
        if self.scenario.debug:
            print(f"\n{self._scenario_name()}{termcolor.colored('[Debug Mode]', 'yellow')} Press enter to continue or type a message to send")
            input_message = input(self._scenario_name() + termcolor.colored('User: ', 'green'))

            # Clear the input prompt lines completely
            for _ in range(3):
                sys.stdout.write("\033[F")  # Move up to the input line
                sys.stdout.write("\033[2K")  # Clear the entire input line
            sys.stdout.flush()  # Make sure the clearing is visible

            if input_message:
                return input_message

        with show_spinner(text=f"{self._scenario_name()}User:", color="green", enabled=self.scenario.verbose):
            return self.testing_agent.generate_next_message(
                scenario, conversation, first_message, last_message
            )

    def _scenario_name(self):
        if self.scenario.verbose == 2:
            return termcolor.colored(f"[Scenario: {self.scenario.name}] ", "yellow")
        else:
            return ""
