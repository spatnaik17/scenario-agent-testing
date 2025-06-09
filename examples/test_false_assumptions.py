from typing import Any, Dict, Optional
import litellm
import pytest

from examples.lovable_clone.lovable_agent import LovableAgent
from scenario import Scenario, TestingAgent, scenario_cache

Scenario.configure(
    testing_agent=TestingAgent(model="anthropic/claude-3-5-sonnet-latest")
)


def create_ai_assistant_agent():
    history = []

    @scenario_cache()
    def ai_assistant_agent(
        message: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        nonlocal history

        history.append({"role": "user", "content": message})
        response = litellm.completion(
            model="openai/gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant",
                },
                *history,
            ],
        )
        message = response.choices[0].message  # type: ignore
        history.append(message)

        return {"messages": [message]}

    return ai_assistant_agent


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_ai_assistant_agent():
    ai_assistant_agent = create_ai_assistant_agent()

    scenario = Scenario(
        name="false assumptions",
        description="""
            The user asks simply "how do I safely approach a bank?"
            The agent makes false assumption about being an ATM bank, and user corrects it
        """,
        agent=ai_assistant_agent,
        messages=[
            {"role": "user", "content": "how do I safely approach a bank?"},
        ],
        criteria=[
            "user should get good recommendations on river crossing",
            "agent should NOT follow up about ATM recommendation after user has corrected them they are just hiking"
        ],
        max_turns=5,
    )

    result = await scenario.run()

    assert result.success
