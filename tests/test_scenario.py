import pytest
from scenario import Scenario, TestingAgent
from scenario.scenario_agent_adapter import ScenarioAgentAdapter
from scenario.scenario_executor import ScenarioExecutor
from scenario.types import (
    AgentInput,
    AgentReturnTypes,
    ScenarioAgentRole,
    ScenarioResult,
)


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
        max_turns=2,
    )

    result = await scenario.run()

    assert not result.success
    assert result.reasoning and "Reached maximum turns" in result.reasoning


@pytest.mark.asyncio
async def test_scenario_high_level_api_allow_to_skip_criteria():
    class MockTestingAgent(TestingAgent):
        async def call(
            self,
            input: AgentInput,
        ) -> AgentReturnTypes:
            return {"role": "user", "content": "Hi, I'm a user"}

    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        max_turns=2,
    )

    result = await scenario.run()

    assert not result.success
    assert result.reasoning and "Reached maximum turns" in result.reasoning


@pytest.mark.asyncio
async def test_scenario_allow_scripted_scenario():
    class MockAgent(ScenarioAgentAdapter):
        async def call(
            self,
            input: AgentInput,
        ) -> AgentReturnTypes:
            assert input.new_messages == [
                {
                    "role": "user",
                    "content": "Hi, I'm a hardcoded user message",
                }
            ]

            return [
                {
                    "role": "assistant",
                    "content": "Hey, how can I help you?",
                }
            ]

    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        criteria=["test criteria"],
    )

    result = await scenario.script(
        [
            scenario.user("Hi, I'm a hardcoded user message"),
            scenario.proceed(),
        ]
    ).run()

    assert result.success


@pytest.mark.asyncio
async def test_scenario_allow_scripted_scenario_with_lower_level_openai_messages():
    class MockAgent(ScenarioAgentAdapter):
        async def call(
            self,
            input: AgentInput,
        ) -> AgentReturnTypes:
            assert input.new_messages == [
                {
                    "role": "user",
                    "content": "Hi, I'm a hardcoded user message",
                }
            ]

            return [
                {
                    "role": "assistant",
                    "content": "Hey, how can I help you?",
                }
            ]

    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        criteria=["test criteria"],
    )

    result = await scenario.script(
        [
            scenario.message(
                {"role": "user", "content": "Hi, I'm a hardcoded user message"}
            ),
            scenario.proceed(),
        ]
    ).run()

    assert result.success


@pytest.mark.asyncio
async def test_scenario_scripted_fails_if_script_ends_without_conclusion():
    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        criteria=["test criteria"],
    )

    result = await scenario.script(
        [
            scenario.user("Hi, I'm a hardcoded user message"),
        ]
    ).run()

    assert not result.success
    assert (
        result.reasoning
        and "Reached end of script without conclusion" in result.reasoning
    )


@pytest.mark.asyncio
async def test_scenario_scripted_force_success():
    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        criteria=["test criteria"],
    )

    result = await scenario.script(
        [
            scenario.user("Hi, I'm a hardcoded user message"),
            scenario.succeed(),
        ]
    ).run()

    assert result.success
    assert (
        result.reasoning
        and "Scenario marked as successful with scenario.succeed()" in result.reasoning
    )


@pytest.mark.asyncio
async def test_scenario_scripted_force_failure():
    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        criteria=["test criteria"],
    )

    result = await scenario.script(
        [
            scenario.user("Hi, I'm a hardcoded user message"),
            scenario.fail(),
        ]
    ).run()

    assert not result.success
    assert (
        result.reasoning
        and "Scenario marked as failed with scenario.fail()" in result.reasoning
    )


@pytest.mark.asyncio
async def test_scenario_scripted_force_judgment():
    class MockTestingAgent(TestingAgent):
        async def call(
            self,
            input: AgentInput,
        ) -> AgentReturnTypes:
            if input.requested_role == ScenarioAgentRole.JUDGE:
                return ScenarioResult(
                    success=True,
                    messages=[],
                    reasoning="judgement enforced",
                    passed_criteria=["test criteria"],
                )

            return {"role": "user", "content": "Hi, I'm a user"}

    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        criteria=["test criteria"],
    )

    result = await scenario.script(
        [
            scenario.user("Hi, I'm a hardcoded user message"),
            scenario.agent(),
            scenario.judge(),
        ]
    ).run()

    assert result.success
    assert result.reasoning and "judgement enforced" in result.reasoning


@pytest.mark.asyncio
async def test_scenario_proceeds_the_amount_of_turns_specified():
    class MockTestingAgent(TestingAgent):
        async def call(
            self,
            input: AgentInput,
        ) -> AgentReturnTypes:
            return {"role": "user", "content": "Hi, I'm a user"}

    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        criteria=["test criteria"],
    )

    result = await scenario.script(
        [
            scenario.user("Hi, I'm a hardcoded user message"),
            scenario.agent(),
            scenario.proceed(turns=2),
            scenario.succeed(),
        ]
    ).run()

    assert result.success
    assert len(result.messages) == 6


@pytest.mark.asyncio
async def test_scenario_proceeds_the_amount_of_turns_specified_as_expected_when_halfway_through_a_turn():
    class MockTestingAgent(TestingAgent):
        async def call(
            self,
            input: AgentInput,
        ) -> AgentReturnTypes:
            return {"role": "user", "content": "Hi, I'm a user"}

    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        criteria=["test criteria"],
    )

    result = await scenario.script(
        [
            scenario.user("Hi, I'm a hardcoded user message"),
            scenario.proceed(turns=2),
            scenario.succeed(),
        ]
    ).run()

    assert result.success
    assert len(result.messages) == 4


@pytest.mark.asyncio
async def test_scenario_accepts_custom_callbacks():
    class MockAgent(ScenarioAgentAdapter):
        async def call(self, input: AgentInput) -> AgentReturnTypes:
            return [{"role": "tool", "tool_call_id": "tool_call_id", "content": "{}"}]

    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        criteria=["test criteria"],
    )

    def check_for_tool_calls(state: ScenarioExecutor) -> None:
        assert state.last_message()["role"] == "tool"

    result = await scenario.script(
        [
            scenario.user("Hi, I'm a hardcoded user message"),
            scenario.agent(),
            check_for_tool_calls,
            scenario.succeed(),
        ]
    ).run()

    assert result.success


@pytest.mark.asyncio
async def test_scenario_accepts_on_turn_and_on_step_callbacks():
    class MockAgent(ScenarioAgentAdapter):
        async def call(self, input: AgentInput) -> AgentReturnTypes:
            if input.scenario_state.current_turn == 0:
                return {"role": "assistant", "content": "Hey, how can I help you?"}
            else:
                return [
                    {"role": "tool", "tool_call_id": "tool_call_id", "content": "{}"}
                ]

    Scenario.configure(testing_agent=MockTestingAgent.with_config(model="none"))

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        criteria=["test criteria"],
    )

    step_calls = 0

    def check_for_tool_calls(state: ScenarioExecutor) -> None:
        if state.current_turn > 1:
            assert state.last_message()["role"] == "tool"

    def increment_step_calls(state: ScenarioExecutor) -> None:
        nonlocal step_calls
        step_calls += 1

    result = await scenario.script(
        [
            scenario.proceed(
                on_turn=check_for_tool_calls,
                on_step=increment_step_calls,
            ),
        ]
    ).run()

    assert result.success
    assert step_calls == 3
