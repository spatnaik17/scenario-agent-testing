from typing import cast
import litellm
import pytest

from openai.types.chat import ChatCompletionMessageParam
import scenario

scenario.configure(default_model="anthropic/claude-3-5-sonnet-latest")


class Agent(scenario.AgentAdapter):
    async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
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
    result = await scenario.run(
        name="false assumptions",
        description="""
            The agent makes false assumption that the user is talking about an ATM bank, and user corrects it
        """,
        agents=[
            Agent(),
            scenario.TestingAgent(
                criteria=[
                    "user should get good recommendations on river crossing",
                    "agent should NOT follow up about ATM recommendation after user has corrected them they are just hiking",
                ],
            ),
        ],
        max_turns=5,
        script=[
            scenario.user("how do I safely approach a bank?"),
            scenario.agent(),
            scenario.user(),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success
