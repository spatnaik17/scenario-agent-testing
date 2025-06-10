from typing import List, Union

import pytest
from scenario import Scenario, TestingAgent
from scenario.result import ScenarioResult
from openai.types.chat import ChatCompletionMessageParam


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

        return ScenarioResult.success_result(
            messages=[],
            reasoning="test reasoning",
            passed_criteria=["test criteria"],
        )


@pytest.mark.asyncio
async def test_scenario_high_level_api():
    Scenario.configure(testing_agent=MockTestingAgent(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=lambda _, __: {"message": "Hey, how can I help you?"},
        criteria=["test criteria"],
    )

    result = await scenario.run()

    assert result.success
