"""
TestingAgent module: defines the testing agent that interacts with the agent under test.
"""

import json
import logging
from typing import TYPE_CHECKING, Dict, List, Any, Optional, Union, cast
from pydantic import BaseModel

from litellm import Choices, completion
from litellm.files.main import ModelResponse

from scenario.cache import scenario_cache
from scenario.utils import safe_attr_or_key

from .result import ScenarioResult

if TYPE_CHECKING:
    from scenario.scenario import Scenario


logger = logging.getLogger("scenario")


class TestingAgent(BaseModel):
    """
    The Testing Agent that interacts with the agent under test.

    This agent is responsible for:
    1. Generating messages to send to the agent based on the scenario
    2. Evaluating the responses from the agent against the success/failure criteria
    3. Determining when to end the test and return a result
    """

    model: str
    api_key: Optional[str] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None

    # To prevent pytest from thinking this is actually a test class
    __test__ = False

    @scenario_cache(ignore=["scenario"])
    def generate_next_message(
        self,
        scenario: "Scenario",
        conversation: List[Dict[str, Any]],
        first_message: bool = False,
        last_message: bool = False,
    ) -> Union[str, ScenarioResult]:
        """
        Generate the next message in the conversation based on history OR
        return a ScenarioResult if the test should conclude.

        Returns either:
          - A string message to send to the agent (if conversation should continue)
          - A ScenarioResult (if the test should conclude)
        """

        messages = [
            {
                "role": "system",
                "content": f"""
<role>
You are pretending to be a user, you are testing an AI Agent (shown as the user role) based on a scenario.
Approach this naturally, as a human user would, with very short inputs, few words, all lowercase, imperative, not periods, like when they google or talk to chatgpt.
</role>

<goal>
Your goal (assistant) is to interact with the Agent Under Test (user) as if you were a human user to see if it can complete the scenario successfully.
</goal>

<scenario>
{scenario.description}
</scenario>

<strategy>
{scenario.strategy or "Start with a first message and guide the conversation to play out the scenario."}
</strategy>

<success_criteria>
{json.dumps(scenario.success_criteria, indent=2)}
</success_criteria>

<failure_criteria>
{json.dumps(scenario.failure_criteria, indent=2)}
</failure_criteria>

<execution_flow>
1. Generate the first message to start the scenario
2. After the Agent Under Test (user) responds, generate the next message to send to the Agent Under Test, keep repeating step 2 until criterias match
3. If the test should end, use the finish_test tool to determine if success or failure criteria have been met
</execution_flow>

<rules>
1. Test should end immediately if a failure criteria is triggered
2. Test should continue until all success criteria have been met
3. DO NOT make any judgment calls that are not explicitly listed in the success or failure criteria, withhold judgement if necessary
4. DO NOT carry over any requests yourself, YOU ARE NOT the assistant today, wait for the user to do it
</rules>
""",
            },
            {"role": "assistant", "content": "Hello, how can I help you today?"},
            *conversation,
        ]

        if last_message:
            messages.append(
                {
                    "role": "user",
                    "content": """
System:

<finish_test>
This is the last message, conversation has reached the maximum number of turns, give your final verdict,
if you don't have enough information to make a verdict, say inconclusive with max turns reached.
</finish_test>
""",
                }
            )

        # User to assistant role reversal
        # LLM models are biased to always be the assistant not the user, so we need to do this reversal otherwise models like GPT 4.5 is
        # super confused, and Claude 3.7 even starts throwing exceptions.
        for message in messages:
            # Can't reverse tool calls
            if not safe_attr_or_key(message, "content") or safe_attr_or_key(
                message, "tool_calls"
            ):
                continue

            if type(message) == dict:
                if message["role"] == "user":
                    message["role"] = "assistant"
                elif message["role"] == "assistant":
                    message["role"] = "user"
            else:
                if getattr(message, "role", None) == "user":
                    message.role = "assistant"
                elif getattr(message, "role", None) == "assistant":
                    message.role = "user"

        # Define the tool
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "finish_test",
                    "description": "Complete the test with a final verdict",
                    "strict": True,
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
                                "required": ["met_criteria", "unmet_criteria", "triggered_failures"],
                                "additionalProperties": False,
                                "description": "Detailed information about criteria evaluation",
                            },
                        },
                        "required": ["verdict", "reasoning", "details"],
                        "additionalProperties": False,
                    },
                },
            }
        ]

        response = cast(
            ModelResponse,
            completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=tools if not first_message else None,
                tool_choice="required" if last_message else None,
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
                                reasoning=reasoning,
                                met_criteria=met_criteria,
                            )
                        elif verdict == "failure":
                            return ScenarioResult.failure_result(
                                conversation=conversation,
                                reasoning=reasoning,
                                met_criteria=met_criteria,
                                unmet_criteria=unmet_criteria,
                                triggered_failures=triggered_failures,
                            )
                        else:  # inconclusive
                            return ScenarioResult(
                                success=False,
                                conversation=conversation,
                                reasoning=reasoning,
                                met_criteria=met_criteria,
                                unmet_criteria=unmet_criteria,
                                triggered_failures=triggered_failures,
                            )
                    except json.JSONDecodeError:
                        logger.error("Failed to parse tool call arguments")

            # If no tool call use the message content as next message
            message_content = message.content
            if message_content is None:
                # If invalid tool call, raise an error
                if message.tool_calls:
                    raise Exception(f"Invalid tool call from testing agent: {message.tool_calls.__repr__()}")
                raise Exception(f"No response from LLM: {response.__repr__()}")

            return message_content
        else:
            raise Exception(
                f"Unexpected response format from LLM: {response.__repr__()}"
            )

