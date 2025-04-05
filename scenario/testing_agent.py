"""
TestingAgent module: defines the testing agent that interacts with the agent under test.
"""

import json
import logging
from typing import TYPE_CHECKING, Dict, List, Any, Union, cast

from litellm import Choices, completion
from litellm.files.main import ModelResponse

from scenario.utils import scenario_cache

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
    1. Generating messages to send to the agent based on the scenario
    2. Evaluating the responses from the agent against the success/failure criteria
    3. Determining when to end the test and return a result
    """

    def __init__(self):
        """
        Initialize the testing agent.
        """
        pass

    @scenario_cache(ignore=["scenario"])
    def generate_next_message(
        self, scenario: "Scenario", conversation: List[Dict[str, Any]], first_message: bool = False
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
<role>
You are pretending to be a user, you are testing an AI Agent based on a scenario.
</role>

<goal>
Your goal is to interact with the Agent Under Test as if you were a human user to see if it can complete the scenario successfully.
</goal>

<scenario>
{scenario.description}
</scenario>

<strategy>
{scenario.strategy or "Approach this naturally, as a human user would, with very short inputs, few words, all lowercase, like when they google or talk to chatgpt."}
</strategy>

<success_criteria>
{json.dumps(scenario.success_criteria, indent=2)}
</success_criteria>

<failure_criteria>
{json.dumps(scenario.failure_criteria, indent=2)}
</failure_criteria>

<execution_flow>
1. Generate the first message to start the scenario
2. After the Agent Under Test responds, generate the next message to send to the Agent Under Test, keep repeating step 2 until the test should end
3. If the test should end, use the finish_test tool to determine if success or failure criteria have been met
</execution_flow>

<rules>
1. Test should end immediately if a failure criteria is triggered
2. Test should continue until all success criteria have been met
3. DO NOT make any judgment calls that are not explicitly listed in the success or failure criteria, withhold judgement if necessary
</rules>
""",
            }
        ]

        # Add the conversation history
        for msg in conversation:
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
                    tools=tools if not first_message else None,
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
                                    conversation=conversation,
                                    met_criteria=met_criteria,
                                )
                            elif verdict == "failure":
                                return ScenarioResult.failure_result(
                                    conversation=conversation,
                                    failure_reason=reasoning,
                                    met_criteria=met_criteria,
                                    unmet_criteria=unmet_criteria,
                                    triggered_failures=triggered_failures,
                                )
                            else:  # inconclusive
                                return ScenarioResult(
                                    success=False,
                                    conversation=conversation,
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
