"""
ScenarioExecutor module: holds the scenario execution logic and state, orchestrating the conversation between the testing agent and the agent under test.
"""

import json
from typing import TYPE_CHECKING, Dict, List, Any, Optional
import time
from copy import deepcopy
import termcolor

from scenario.error_messages import message_return_error_message

from .result import ScenarioResult

if TYPE_CHECKING:
    from scenario.scenario import Scenario


class ScenarioExecutor:
    def __init__(self, scenario: "Scenario"):
        self.scenario = deepcopy(scenario)
        self.config = scenario.config
        self.testing_agent = scenario.testing_agent

    def run(
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

        # Reset state for this run
        conversation: List[Dict[str, Any]] = []

        if self.config.verbose:
            print("")  # new line

        # Run the initial testing agent prompt to get started
        start_time = time.time()
        initial_message = self.testing_agent.generate_next_message(
            conversation, self.scenario, first_message=True
        )

        if isinstance(initial_message, ScenarioResult):
            raise Exception(
                "Unexpectedly generated a ScenarioResult for the initial message",
                initial_message.__repr__(),
            )

        # Execute the conversation
        current_turn = 0
        max_turns = self.scenario.max_turns
        agent_time = 0

        # Start the test with the initial message
        while current_turn < max_turns:
            # Record the testing agent's message
            conversation.append({"role": "user", "content": initial_message})

            # Get response from the agent under test
            start_time = time.time()
            try:
                agent_response = self.scenario.agent(initial_message, context)
                if (
                    "message" not in agent_response
                    or type(agent_response["message"]) is not str
                    or agent_response["message"] is None
                ) and (
                    "messages" not in agent_response
                    or not isinstance(agent_response["messages"], list)
                    or not all(
                        "role" in msg or hasattr(msg, "role")
                        for msg in agent_response["messages"]
                    )
                ):
                    raise Exception(message_return_error_message)
                if "messages" in agent_response and self.scenario.config.verbose:
                    for msg in agent_response["messages"]:
                        role = msg.get("role", getattr(msg, "role", None))
                        content = msg.get("content", getattr(msg, "content", None))
                        if role == "assistant":
                            print(termcolor.colored("Agent:", "blue"), content)
                        else:
                            print(
                                termcolor.colored(f"{role}:", "magenta"),
                                msg.__repr__(),
                            )

                if (
                    self.scenario.config.verbose
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
            except Exception as e:
                return ScenarioResult.failure_result(
                    conversation=conversation,
                    failure_reason=f"Agent function raised an exception: {str(e)}",
                    total_time=time.time() - start_time,
                    agent_time=agent_time,
                )

            if "messages" in agent_response:
                conversation.extend(agent_response["messages"])
            if "message" in agent_response:
                conversation.append(
                    {"role": "assistant", "content": agent_response["message"]}
                )
            if "extra" in agent_response:
                conversation.append(
                    {
                        "role": "assistant",
                        "content": json.dumps(agent_response["extra"]),
                    }
                )

            # Generate the next message OR finish the test based on the agent's evaluation
            result = self.testing_agent.generate_next_message(
                conversation, self.scenario
            )

            # Check if the result is a ScenarioResult (indicating test completion)
            if isinstance(result, ScenarioResult):
                result.total_time = time.time() - start_time
                result.agent_time = agent_time
                return result

            # Otherwise, it's the next message to send to the agent
            initial_message = result

            # Increment turn counter
            current_turn += 1

        # If we reached max turns without conclusion, fail the test
        return ScenarioResult.failure_result(
            conversation=conversation,
            failure_reason=f"Reached maximum turns ({max_turns}) without conclusion",
            total_time=time.time() - start_time,
            agent_time=agent_time,
        )
