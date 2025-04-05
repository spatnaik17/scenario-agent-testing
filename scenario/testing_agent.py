"""
TestingAgent module: defines the testing agent that interacts with the agent under test.
"""

import json
import logging
from typing import TYPE_CHECKING, Dict, List, Any, Optional, Callable, Union, cast
import time

from litellm import Choices, completion
from litellm.files.main import ModelResponse
import termcolor

from scenario.config import ScenarioConfig
from scenario.error_messages import message_return_error_message

# Fix imports for local modules
from .result import ScenarioResult

if TYPE_CHECKING:
    from scenario.scenario import Scenario


# Set up logging
logger = logging.getLogger("scenario")


class TestingAgent:
    """
    The Testing Agent that interacts with the agent under test.

    This agent is responsible for:
    1. Taking a scenario and running it against the agent under test
    2. Generating messages to send to the agent based on the scenario
    3. Evaluating the responses from the agent against the success/failure criteria
    4. Determining when to end the test and return a result
    """

    def __init__(self):
        """
        Initialize the testing agent.
        """

        # Initialize conversation history
        self._conversation: List[Dict[str, str]] = []
        self._artifacts: Dict[str, Any] = {}

    def run_scenario(
        self,
        agent_fn: Callable[[str, Optional[Dict[str, Any]]], Dict[str, Any]],
        scenario: "Scenario",
        context: Optional[Dict[str, Any]] = None,
    ) -> ScenarioResult:
        """
        Run a scenario against the agent under test.

        Args:
            agent_fn: Function that takes a message and returns agent response
            scenario: The scenario to test
            context: Optional initial context for the agent

        Returns:
            ScenarioResult containing the test outcome
        """
        # Reset state for this run
        self._conversation = []
        self._artifacts = {}

        if scenario.config.verbose:
            print("")  # new line

        # Run the initial testing agent prompt to get started
        start_time = time.time()
        initial_message = self._generate_next_message(scenario)

        if isinstance(initial_message, ScenarioResult):
            raise Exception(
                "Unexpectedly generated a ScenarioResult for the initial message"
            )

        # Execute the conversation
        current_turn = 0
        max_turns = scenario.max_turns
        agent_time = 0

        # Start the test with the initial message
        while current_turn < max_turns:
            # Record the testing agent's message
            self._conversation.append({"role": "user", "content": initial_message})

            # Get response from the agent under test
            start_time = time.time()
            try:
                agent_response = agent_fn(initial_message, context)
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
                if "messages" in agent_response and scenario.config.verbose:
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
                    scenario.config.verbose
                    and "extra" in agent_response
                    and len(agent_response["extra"].keys()) > 0
                ):
                    print(
                        termcolor.colored(
                            "Extra:" + json.dumps(agent_response["extra"]), "magenta"
                        )
                    )
                response_time = time.time() - start_time
                agent_time += response_time
            except Exception as e:
                logger.error(f"Agent function raised an exception: {e}")
                return ScenarioResult.failure_result(
                    conversation=self._conversation,
                    artifacts=self._artifacts,
                    failure_reason=f"Agent function raised an exception: {str(e)}",
                    total_time=time.time() - start_time,
                    agent_time=agent_time,
                )

            if "messages" in agent_response:
                self._conversation.extend(agent_response["messages"])
            if "message" in agent_response:
                self._conversation.append(
                    {"role": "assistant", "content": agent_response["message"]}
                )
            if "extra" in agent_response:
                self._conversation.append(
                    {
                        "role": "assistant",
                        "content": json.dumps(agent_response["extra"]),
                    }
                )

            # Generate the next message OR finish the test based on the agent's evaluation
            result = self._generate_next_message(scenario)

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
            conversation=self._conversation,
            artifacts=self._artifacts,
            failure_reason=f"Reached maximum turns ({max_turns}) without conclusion",
            total_time=time.time() - start_time,
            agent_time=agent_time,
        )

    def _generate_next_message(
        self, scenario: "Scenario"
    ) -> Union[str, ScenarioResult]:
        """
        Generate the next message in the conversation based on history OR
        return a ScenarioResult if the test should conclude.

        Returns either:
          - A string message to send to the agent (if conversation should continue)
          - A ScenarioResult (if the test should conclude)
        """
        # Prepare the conversation history for the LLM
        messages = [
            {
                "role": "system",
                "content": f"""
You are pretending to be a user, you are testing an AI Agent based on a scenario.

Your goal is to interact with the Agent Under Test as if you were a human user to see if it can complete the scenario successfully.

SCENARIO DESCRIPTION:
{scenario.description}

TESTING STRATEGY:
{scenario.strategy or "Approach this naturally, as a human user would. Use context from the conversation."}

SUCCESS CRITERIA:
{json.dumps(scenario.success_criteria, indent=2)}

FAILURE CRITERIA:
{json.dumps(scenario.failure_criteria, indent=2)}

You have two responsibilities:
1. Generate the next message to send to the Agent Under Test
2. Evaluate the conversation to determine if success or failure criteria have been met

After each response from the Agent Under Test, decide whether:
- success: All success criteria have been met and the test is successful
- failure: Any failure criteria have been triggered and the test has failed
- continue: The test should continue with a new message

Failure criteria should be evaluated first, and if any are triggered, the test should END IMMEDIATELY as a failure.
Success criteria should be evaluated next, and if all are met, the test should END as a success.
If neither has been met conclusively, the test should CONTINUE.

You have access to a special tool: finish_test(verdict, reasoning)
- Use this tool ONLY if you've determined the test should conclude (success or inconclusive)
- If you use this tool, do NOT also return a next message
- If the test should continue, do NOT use this tool and instead provide a next message

For the verdict parameter, use one of: "success", "failure", "inconclusive"
""",
            }
        ]

        # Add the conversation history
        for msg in self._conversation:
            if msg["role"] == "user":
                messages.append({"role": "assistant", "content": msg["content"]})
            else:
                messages.append({"role": "user", "content": msg["content"]})

        # Define the tool
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "finish_test",
                    "description": "Complete the test with a final verdict",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "verdict": {
                                "type": "string",
                                "enum": ["success", "failure", "inconclusive"],
                                "description": "The final verdict of the test",
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Explanation of why this verdict was reached",
                            },
                            "details": {
                                "type": "object",
                                "properties": {
                                    "met_criteria": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of success criteria that have been met",
                                    },
                                    "unmet_criteria": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of success criteria that have not been met",
                                    },
                                    "triggered_failures": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of failure criteria that have been triggered",
                                    },
                                },
                                "required": ["met_criteria"],
                                "description": "Detailed information about criteria evaluation",
                            },
                        },
                        "required": ["verdict", "reasoning"],
                    },
                },
            }
        ]

        try:
            response = cast(
                ModelResponse,
                completion(
                    model=scenario.config.testing_agent.get("model", "invalid"),
                    messages=messages,
                    temperature=scenario.config.testing_agent.get("temperature"),
                    max_tokens=scenario.config.testing_agent.get("max_tokens"),
                    tools=tools,
                ),
            )

            # Extract the content from the response
            if hasattr(response, "choices") and len(response.choices) > 0:
                message = cast(Choices, response.choices[0]).message

                # Check if the LLM chose to use the tool
                if message.tool_calls:
                    tool_call = message.tool_calls[0]
                    if tool_call.function.name == "finish_test":
                        # Parse the tool call arguments
                        try:
                            args = json.loads(tool_call.function.arguments)
                            verdict = args.get("verdict", "inconclusive")
                            reasoning = args.get("reasoning", "No reasoning provided")
                            details = args.get("details", {})

                            met_criteria = details.get("met_criteria", [])
                            unmet_criteria = details.get("unmet_criteria", [])
                            triggered_failures = details.get("triggered_failures", [])

                            # Return the appropriate ScenarioResult based on the verdict
                            if verdict == "success":
                                return ScenarioResult.success_result(
                                    conversation=self._conversation,
                                    artifacts=self._artifacts,
                                    met_criteria=met_criteria,
                                )
                            elif verdict == "failure":
                                return ScenarioResult.failure_result(
                                    conversation=self._conversation,
                                    artifacts=self._artifacts,
                                    failure_reason=reasoning,
                                    met_criteria=met_criteria,
                                    unmet_criteria=unmet_criteria,
                                    triggered_failures=triggered_failures,
                                )
                            else:  # inconclusive
                                return ScenarioResult(
                                    success=False,
                                    conversation=self._conversation,
                                    artifacts=self._artifacts,
                                    met_criteria=met_criteria,
                                    unmet_criteria=unmet_criteria,
                                    triggered_failures=triggered_failures,
                                )
                        except json.JSONDecodeError:
                            logger.error("Failed to parse tool call arguments")

                # If no tool call or invalid tool call, use the message content as next message
                message_content = message.content
                if message_content is None:
                    raise Exception(f"No response from LLM: {response.__repr__()}")

                if scenario.config.verbose:
                    print(termcolor.colored("User:", "green"), message_content)

                return message_content
            else:
                raise Exception(
                    f"Unexpected response format from LLM: {response.__repr__()}"
                )
        except Exception as e:
            logger.error(f"Error generating next message: {e}")
            # Continue the conversation if there's an error
            return "Let's continue our conversation. Can you tell me more about that?"


# Create a default testing agent instance to be used when none is provided
DEFAULT_TESTING_AGENT = TestingAgent()
