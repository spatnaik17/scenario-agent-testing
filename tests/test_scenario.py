import pytest
from scenario import Scenario, TestingAgent
from scenario.config import ScenarioConfig
from scenario.scenario_agent_adapter import ScenarioAgentAdapter
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


@pytest.mark.asyncio
async def test_scenario_high_level_api_allow_to_pass_agents_as_list():
    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agents=[MockTestingAgent.with_config(model="openai/gpt-4.1-mini"), MockAgent],
        criteria=["test criteria"],
    )

    result = await scenario.run()

    assert result.success


@pytest.mark.asyncio
async def test_scenario_high_level_api_allow_to_skip_testing_agent_if_given_agents_list():
    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))
    # Make sure default testing agent is not set to allow this
    Scenario.default_config.testing_agent = None

    scenario = Scenario(
        name="test name",
        description="test description",
        agents=[MockAgent],
        criteria=["test criteria"],
        max_turns=2,
    )

    result = await scenario.run()

    assert not result.success
    assert result.reasoning and "Reached maximum turns" in result.reasoning
