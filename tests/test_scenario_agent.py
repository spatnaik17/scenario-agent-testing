from typing import Any, List, Union, cast

import pytest
from scenario import Scenario, TestingAgent
from scenario.types import ScenarioResult
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam

from scenario.scenario_agent import ScenarioAgentAdapter
from scenario.types import AgentInput, MessageTriggers


@pytest.mark.asyncio
async def test_should_be_able_to_override_scenario_agent():
    class MyCustomTestingAgent(ScenarioAgentAdapter):
        triggers = {MessageTriggers.ASSISTANT}

        async def call(self, input: AgentInput):
            return ScenarioResult(
                success=True,
                reasoning="",
                passed_criteria=[],
                messages=[
                    ChatCompletionUserMessageParam(
                        role="user", content="Hello, how can I help you?"
                    )
                ],
            )

    input = AgentInput(
        thread_id="1", messages=[], context={}, scenario_state=cast(Any, None)
    )

    agent = MyCustomTestingAgent(input)
    assert agent.triggers == {MessageTriggers.ASSISTANT}
    assert (await agent.call(input)).success
