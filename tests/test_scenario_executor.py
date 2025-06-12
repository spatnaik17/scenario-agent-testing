from typing import Union

import pytest
from scenario import Scenario, TestingAgent
from scenario.scenario_agent_adapter import ScenarioAgentAdapter
from scenario.types import AgentInput, AgentReturnTypes, ScenarioResult

from scenario.scenario_executor import ScenarioExecutor


class MockTestingAgent(TestingAgent):
    async def call(
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


class MockAgent(ScenarioAgentAdapter):
    async def call(self, input: AgentInput) -> AgentReturnTypes:
        return {"role": "assistant", "content": "Hey, how can I help you?"}


scenario = Scenario(
    name="test name",
    description="test description",
    agent=MockAgent,
    testing_agent=MockTestingAgent.with_config(model="none"),
    criteria=["test criteria"],
)


@pytest.mark.asyncio
async def test_advance_a_step():

    executor = ScenarioExecutor(scenario)

    assert executor.messages == [], "starts with no messages"

    await executor.step()

    assert executor.messages == [
        {"role": "user", "content": "Hi, I'm a user"},
    ], "starts with the user message"

    assert executor.current_turn == 0, "stays at turn 0 until agent replied"

    await executor.step()

    assert executor.messages == [
        {"role": "user", "content": "Hi, I'm a user"},
        {"role": "assistant", "content": "Hey, how can I help you?"},
    ], "starts with the user message"

    assert executor.current_turn == 0, "stays at turn 0 until next step"

    await executor.step()

    assert executor.current_turn == 1, "increments turn"


@pytest.mark.asyncio
async def test_sends_the_right_new_messages():
    class MockTestingAgent(TestingAgent):
        async def call(
            self,
            input: AgentInput,
        ) -> Union[str, ScenarioResult]:
            if input.scenario_state.current_turn == 0:
                assert input.new_messages == []
                return "Hi, I'm a user"

            if input.scenario_state.current_turn == 1:
                assert input.messages == [
                    {"role": "user", "content": "Hi, I'm a user"},
                    {"role": "assistant", "content": "Hey, how can I help you?"},
                ]
                assert input.new_messages == [
                    {"role": "assistant", "content": "Hey, how can I help you?"}
                ]
                return "You can help me testing"

            return ScenarioResult(
                success=True,
                messages=[],
                reasoning="test reasoning",
                passed_criteria=["test criteria"],
            )

    class MockAgent(ScenarioAgentAdapter):
        async def call(self, input: AgentInput) -> AgentReturnTypes:
            if input.scenario_state.current_turn == 0:
                assert input.new_messages == [
                    {"role": "user", "content": "Hi, I'm a user"}
                ]
                return {"role": "assistant", "content": "Hey, how can I help you?"}
            else:
                assert input.messages == [
                    {"role": "user", "content": "Hi, I'm a user"},
                    {"role": "assistant", "content": "Hey, how can I help you?"},
                    {"role": "user", "content": "You can help me testing"},
                ]
                assert input.new_messages == [
                    {"role": "user", "content": "You can help me testing"}
                ]
                return {"role": "assistant", "content": "Is it working?"}

    scenario = Scenario(
        name="test name",
        description="test description",
        agent=MockAgent,
        testing_agent=MockTestingAgent.with_config(model="none"),
        criteria=["test criteria"],
    )

    executor = ScenarioExecutor(scenario)

    # Run first turn
    await executor.step()
    await executor.step()

    assert executor.current_turn == 0

    # Run a second turn to trigger the new_messages assertion
    await executor.step()
    await executor.step()


@pytest.mark.asyncio
async def test_for_tool_calls():
    executor = ScenarioExecutor(scenario)
    executor.add_message(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "123",
                    "function": {"name": "foo", "arguments": "{}"},
                    "type": "function",
                }
            ],
        }
    )

    assert executor.last_tool_call("foo") == {
        "id": "123",
        "function": {"name": "foo", "arguments": "{}"},
        "type": "function",
    }
    assert executor.last_tool_call("bar") is None

    assert executor.has_tool_call("foo")
    assert not executor.has_tool_call("bar")
