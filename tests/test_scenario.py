import pytest
from scenario import Scenario, TestingAgent
from scenario.scenario_agent import ScenarioAgentAdapter
from scenario.types import AgentInput, AgentReturnTypes, ScenarioResult


class MockTestingAgent(TestingAgent):
    async def call(
        self,
        input: AgentInput,
    ) -> AgentReturnTypes:
        if len(input.messages) == 0:
            return {"role": "user", "content": "Hi, I'm a user"}

        return ScenarioResult(
            success=True,
            messages=[],
            reasoning="test reasoning",
            passed_criteria=["test criteria"],
        )


class MockAgent(ScenarioAgentAdapter):
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        return {"role": "assistant", "content": "Hey, how can I help you?"}


@pytest.mark.asyncio
async def test_scenario_high_level_api():
    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        criteria=["test criteria"],
    )

    result = await scenario.run()

    assert result.success
