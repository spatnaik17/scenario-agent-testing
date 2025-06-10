from typing import List, Union

import pytest
from scenario import Scenario, TestingAgent
from scenario.types import ScenarioResult
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam

from scenario.scenario_executor import ScenarioExecutor


class MockTestingAgent(TestingAgent):
    def generate_next_message(
        self,
        scenario: Scenario,
        messages: List[ChatCompletionMessageParam],
        first_message: bool = False,
        last_message: bool = False,
    ) -> Union[str, ScenarioResult]:
        if first_message:
            return "Hi, I'm a user"

        return ScenarioResult(
            success=True,
            messages=[],
            reasoning="test reasoning",
            passed_criteria=["test criteria"],
        )

@pytest.mark.asyncio
async def test_advance_a_step():
    scenario = Scenario(
        name="test name",
        description="test description",
        agent=lambda _, __: {"message": "Hey, how can I help you?"},
        testing_agent=MockTestingAgent(model="none"),
        criteria=["test criteria"],
    )

    executor = ScenarioExecutor(scenario)

    assert executor.messages == [], "starts with no messages"

    await executor.step()

    assert executor.messages == [
        ChatCompletionUserMessageParam(role="user", content="Hi, I'm a user")
    ], "starts with the user message"