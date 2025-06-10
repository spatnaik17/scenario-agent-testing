from typing import Union

import pytest
from scenario import Scenario, TestingAgent
from scenario.types import AgentInput, ScenarioResult
from openai.types.chat import ChatCompletionUserMessageParam

from scenario.scenario_executor import ScenarioExecutor


class MockTestingAgent(TestingAgent):
    def call(
        self,
        input: AgentInput,
    ) -> Union[str, ScenarioResult]:
        if len(input.messages) == 0:
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
        testing_agent=MockTestingAgent.with_config(model="none"),
        criteria=["test criteria"],
    )

    executor = ScenarioExecutor(scenario)

    assert executor.messages == [], "starts with no messages"

    await executor.step()

    assert executor.messages == [
        ChatCompletionUserMessageParam(role="user", content="Hi, I'm a user")
    ], "starts with the user message"
