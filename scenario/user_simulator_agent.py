import logging
from typing import Optional, cast

from litellm import Choices, completion
from litellm.files.main import ModelResponse

from scenario.cache import scenario_cache
from scenario.agent_adapter import AgentAdapter
from scenario.utils import reverse_roles
from scenario.config import ModelConfig, ScenarioConfig

from .error_messages import agent_not_configured_error_message
from .types import AgentInput, AgentReturnTypes, AgentRole


logger = logging.getLogger("scenario")


class UserSimulatorAgent(AgentAdapter):
    role = AgentRole.USER

    model: str
    api_key: Optional[str]
    temperature: float
    max_tokens: Optional[int]
    system_prompt: Optional[str]

    def __init__(
        self,
        *,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        # Override the default system prompt for the user simulator agent
        system_prompt: Optional[str] = None,
    ):
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

        Returns:
          - A string message to send to the agent (if conversation should continue)
        """

        scenario = input.scenario_state

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
                or f"""
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

<rules>
- DO NOT carry over any requests yourself, YOU ARE NOT the assistant today, you are the user
</rules>
""",
            },
            {"role": "assistant", "content": "Hello, how can I help you today?"},
            *input.messages,
        ]

        # User to assistant role reversal
        # LLM models are biased to always be the assistant not the user, so we need to do this reversal otherwise models like GPT 4.5 is
        # super confused, and Claude 3.7 even starts throwing exceptions.
        messages = reverse_roles(messages)

        response = cast(
            ModelResponse,
            completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=[],
            ),
        )

        # Extract the content from the response
        if hasattr(response, "choices") and len(response.choices) > 0:
            message = cast(Choices, response.choices[0]).message

            message_content = message.content
            if message_content is None:
                raise Exception(f"No response from LLM: {response.__repr__()}")

            return {"role": "user", "content": message_content}
        else:
            raise Exception(
                f"Unexpected response format from LLM: {response.__repr__()}"
            )
