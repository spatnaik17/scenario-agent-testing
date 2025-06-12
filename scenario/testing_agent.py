"""
TestingAgent module: defines the testing agent that interacts with the agent under test.
"""

import json
import logging
import re
from typing import Optional, Type, cast

from litellm import Choices, completion
from litellm.files.main import ModelResponse

from scenario.cache import scenario_cache
from scenario.scenario_agent_adapter import ScenarioAgentAdapter
from scenario.utils import reverse_roles

from .error_messages import testing_agent_not_configured_error_message
from .types import AgentInput, AgentReturnTypes, ScenarioAgentRole, ScenarioResult


logger = logging.getLogger("scenario")


class TestingAgent(ScenarioAgentAdapter):
    """
    The Testing Agent that interacts with the agent under test.

    This agent is responsible for:
    1. Generating messages to send to the agent based on the scenario
    2. Evaluating the responses from the agent against the success/failure criteria
    3. Determining when to end the test and return a result
    """

    roles = {ScenarioAgentRole.USER, ScenarioAgentRole.JUDGE}

    model: str = ""
    api_key: Optional[str] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None

    # To prevent pytest from thinking this is actually a test class
    __test__ = False

    def __init__(self, input: AgentInput):
        super().__init__(input)

        if not self.model:
            raise Exception(testing_agent_not_configured_error_message)

    @classmethod
    def with_config(
        cls,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> Type["TestingAgent"]:
        class TestingAgentWithConfig(cls):
            def __init__(self, input: AgentInput):
                self.model = model
                self.api_key = api_key
                self.temperature = temperature
                self.max_tokens = max_tokens

                super().__init__(input)

        return TestingAgentWithConfig

    @scenario_cache(ignore=["scenario"])
    async def call(
        self,
        input: AgentInput,
    ) -> AgentReturnTypes:
        """
        Generate the next message in the conversation based on history OR
        return a ScenarioResult if the test should conclude.

        Returns either:
          - A string message to send to the agent (if conversation should continue)
          - A ScenarioResult (if the test should conclude)
        """

        scenario = input.scenario_state.scenario

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

<criteria>
{"\n".join([f"{idx + 1}. {criterion}" for idx, criterion in enumerate(scenario.criteria)])}
</criteria>

<execution_flow>
1. Generate the first message to start the scenario
2. After the Agent Under Test (user) responds, generate the next message to send to the Agent Under Test, keep repeating step 2 until criterias match
3. If the test should end, use the finish_test tool to determine if all the criteria have been met
</execution_flow>

<rules>
1. Test should end immediately if a criteria mentioning something the agent should NOT do is met
2. Test should continue until all scenario goals have been met to try going through all the criteria
3. DO NOT make any judgment calls that are not explicitly listed in the success or failure criteria, withhold judgement if necessary
4. DO NOT carry over any requests yourself, YOU ARE NOT the assistant today, wait for the user to do it
</rules>
""",
            },
            {"role": "assistant", "content": "Hello, how can I help you today?"},
            *input.messages,
        ]

        is_first_message = len(input.messages) == 0
        is_last_message = (
            input.scenario_state.current_turn == input.scenario_state.scenario.max_turns
        )

        if is_last_message:
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
        messages = reverse_roles(messages)

        # Define the tool
        criteria_names = [
            re.sub(
                r"[^a-zA-Z0-9]",
                "_",
                criterion.replace(" ", "_").replace("'", "").lower(),
            )[:70]
            for criterion in scenario.criteria
        ]
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
                            "criteria": {
                                "type": "object",
                                "properties": {
                                    criteria_names[idx]: {
                                        "enum": [True, False, "inconclusive"],
                                        "description": criterion,
                                    }
                                    for idx, criterion in enumerate(scenario.criteria)
                                },
                                "required": criteria_names,
                                "additionalProperties": False,
                                "description": "Strict verdict for each criterion",
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Explanation of what the final verdict should be",
                            },
                            "verdict": {
                                "type": "string",
                                "enum": ["success", "failure", "inconclusive"],
                                "description": "The final verdict of the test",
                            },
                        },
                        "required": ["criteria", "reasoning", "verdict"],
                        "additionalProperties": False,
                    },
                },
            }
        ]

        enforce_judgment = input.requested_role == ScenarioAgentRole.JUDGE
        has_criteria = len(scenario.criteria) > 0

        if enforce_judgment and not has_criteria:
            return ScenarioResult(
                success=False,
                messages=[],
                reasoning="TestingAgent was called as a judge, but it has no criteria to judge against",
            )

        response = cast(
            ModelResponse,
            completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=(
                    tools
                    if (not is_first_message or enforce_judgment) and has_criteria
                    else None
                ),
                tool_choice=(
                    "required"
                    if (is_last_message or enforce_judgment) and has_criteria
                    else None
                ),
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
                        criteria = args.get("criteria", {})

                        passed_criteria = [
                            scenario.criteria[idx]
                            for idx, criterion in enumerate(criteria.values())
                            if criterion == True
                        ]
                        failed_criteria = [
                            scenario.criteria[idx]
                            for idx, criterion in enumerate(criteria.values())
                            if criterion == False
                        ]

                        # Return the appropriate ScenarioResult based on the verdict
                        return ScenarioResult(
                            success=verdict == "success",
                            messages=messages,
                            reasoning=reasoning,
                            passed_criteria=passed_criteria,
                            failed_criteria=failed_criteria,
                        )
                    except json.JSONDecodeError:
                        logger.error("Failed to parse tool call arguments")

            # If no tool call use the message content as next message
            message_content = message.content
            if message_content is None:
                # If invalid tool call, raise an error
                if message.tool_calls:
                    raise Exception(
                        f"Invalid tool call from testing agent: {message.tool_calls.__repr__()}"
                    )
                raise Exception(f"No response from LLM: {response.__repr__()}")

            return {"role": "user", "content": message_content}
        else:
            raise Exception(
                f"Unexpected response format from LLM: {response.__repr__()}"
            )
