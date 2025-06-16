import json
import logging
import re
from typing import List, Optional, cast

from litellm import Choices, completion
from litellm.files.main import ModelResponse

from scenario.cache import scenario_cache
from scenario.agent_adapter import AgentAdapter
from scenario.config import ModelConfig, ScenarioConfig

from .error_messages import agent_not_configured_error_message
from .types import AgentInput, AgentReturnTypes, AgentRole, ScenarioResult


logger = logging.getLogger("scenario")


class JudgeAgent(AgentAdapter):
    role = AgentRole.JUDGE

    model: str
    api_key: Optional[str]
    temperature: float
    max_tokens: Optional[int]
    criteria: List[str]
    system_prompt: Optional[str]

    def __init__(
        self,
        *,
        criteria: Optional[List[str]] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        # Override the default system prompt for the judge agent
        system_prompt: Optional[str] = None,
    ):
        self.criteria = criteria or []
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt

        if model:
            self.model = model

        if ScenarioConfig.default_config is not None and isinstance(
            ScenarioConfig.default_config.default_model, str
        ):
            self.model = model or ScenarioConfig.default_config.default_model
        elif ScenarioConfig.default_config is not None and isinstance(
            ScenarioConfig.default_config.default_model, ModelConfig
        ):
            self.model = model or ScenarioConfig.default_config.default_model.model
            self.api_key = (
                api_key or ScenarioConfig.default_config.default_model.api_key
            )
            self.temperature = (
                temperature or ScenarioConfig.default_config.default_model.temperature
            )
            self.max_tokens = (
                max_tokens or ScenarioConfig.default_config.default_model.max_tokens
            )

        if not hasattr(self, "model"):
            raise Exception(agent_not_configured_error_message("TestingAgent"))

    @scenario_cache()
    async def call(
        self,
        input: AgentInput,
    ) -> AgentReturnTypes:
        """
        Generate the next message in the conversation based on history OR
        return a ScenarioResult if the test should conclude.

        Returns either:
          - An empty list of messages (if the test should continue)
          - A ScenarioResult (if the test should conclude)
        """

        scenario = input.scenario_state

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
                or f"""
<role>
You are an LLM as a judge watching a simulated conversation as it plays out live to determine if the agent under test meets the criteria or not.
</role>

<goal>
Your goal is to determine if you already have enough information to make a verdict of the scenario below, or if the conversation should continue for longer.
If you do have enough information, use the finish_test tool to determine if all the criteria have been met, if not, use the continue_test tool to let the next step play out.
</goal>

<scenario>
{scenario.description}
</scenario>

<criteria>
{"\n".join([f"{idx + 1}. {criterion}" for idx, criterion in enumerate(self.criteria)])}
</criteria>

<rules>
- Be strict, do not let the conversation continue if the agent already broke one of the "do not" or "should not" criterias.
- DO NOT make any judgment calls that are not explicitly listed in the success or failure criteria, withhold judgement if necessary
</rules>
""",
            },
            *input.messages,
        ]

        is_last_message = (
            input.scenario_state.current_turn == input.scenario_state.config.max_turns
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

        # Define the tools
        criteria_names = [
            re.sub(
                r"[^a-zA-Z0-9]",
                "_",
                criterion.replace(" ", "_").replace("'", "").lower(),
            )[:70]
            for criterion in self.criteria
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "continue_test",
                    "description": "Continue the test with the next step",
                    "strict": True,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False,
                    },
                },
            },
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
                                    for idx, criterion in enumerate(self.criteria)
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
            },
        ]

        enforce_judgment = input.judgment_request
        has_criteria = len(self.criteria) > 0

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
                tools=tools,
                tool_choice=(
                    {"type": "function", "function": {"name": "finish_test"}}
                    if (is_last_message or enforce_judgment) and has_criteria
                    else "required"
                ),
            ),
        )

        # Extract the content from the response
        if hasattr(response, "choices") and len(response.choices) > 0:
            message = cast(Choices, response.choices[0]).message

            # Check if the LLM chose to use the tool
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                if tool_call.function.name == "continue_test":
                    return []

                if tool_call.function.name == "finish_test":
                    # Parse the tool call arguments
                    try:
                        args = json.loads(tool_call.function.arguments)
                        verdict = args.get("verdict", "inconclusive")
                        reasoning = args.get("reasoning", "No reasoning provided")
                        criteria = args.get("criteria", {})

                        passed_criteria = [
                            self.criteria[idx]
                            for idx, criterion in enumerate(criteria.values())
                            if criterion == True
                        ]
                        failed_criteria = [
                            self.criteria[idx]
                            for idx, criterion in enumerate(criteria.values())
                            if criterion == False
                        ]

                        # Return the appropriate ScenarioResult based on the verdict
                        return ScenarioResult(
                            success=verdict == "success" and len(failed_criteria) == 0,
                            messages=messages,
                            reasoning=reasoning,
                            passed_criteria=passed_criteria,
                            failed_criteria=failed_criteria,
                        )
                    except json.JSONDecodeError:
                        raise Exception(
                            f"Failed to parse tool call arguments from judge agent: {tool_call.function.arguments}"
                        )

                else:
                    raise Exception(
                        f"Invalid tool call from judge agent: {tool_call.function.name}"
                    )

            else:
                raise Exception(
                    f"Invalid response from judge agent, tool calls not found: {message.__repr__()}"
                )

        else:
            raise Exception(
                f"Unexpected response format from LLM: {response.__repr__()}"
            )
