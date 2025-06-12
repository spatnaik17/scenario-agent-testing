from typing import cast
import litellm
import pytest

from openai.types.chat import ChatCompletionMessageParam
from scenario import Scenario, TestingAgent
from scenario.scenario_agent_adapter import ScenarioAgentAdapter
from scenario.types import AgentInput, AgentReturnTypes

Scenario.configure(
    testing_agent=TestingAgent.with_config(model="anthropic/claude-3-5-sonnet-latest")
)


class AiAssistantAgentAdapter(ScenarioAgentAdapter):
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        response = litellm.completion(
            model="openai/gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant",
                },
                *input.messages,
            ],
        )
        message = response.choices[0].message  # type: ignore

        return [cast(ChatCompletionMessageParam, message)]


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_ai_assistant_agent():
    scenario = Scenario(
        name="false assumptions",
        description="""
            The agent makes false assumption about being an ATM bank, and user corrects it
        """,
        agent=AiAssistantAgentAdapter,
        criteria=[
            "user should get good recommendations on river crossing",
            "agent should NOT follow up about ATM recommendation after user has corrected them they are just hiking",
        ],
        max_turns=5,
    )

    result = await scenario.script(
        [
            scenario.user("how do I safely approach a bank?"),
            scenario.agent(),
            scenario.user(),
            scenario.agent(),
            scenario.judge(),
        ]
    ).run()

    assert result.success
