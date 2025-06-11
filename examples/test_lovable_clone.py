import pytest

from examples.lovable_clone.lovable_agent import LovableAgent
from scenario import Scenario, TestingAgent
from scenario.scenario_agent import ScenarioAgentAdapter
from scenario.types import AgentInput, AgentReturnTypes

Scenario.configure(
    testing_agent=TestingAgent.with_config(model="anthropic/claude-3-5-sonnet-latest"),
)


class LovableAgentAdapter(ScenarioAgentAdapter):
    def __init__(self, input: AgentInput):
        self.lovable_agent = LovableAgent()

    async def call(self, input: AgentInput) -> AgentReturnTypes:
        _, messages = await self.lovable_agent.process_user_message(
            input.last_new_user_message_str(), input.context["template_path"]
        )

        return messages


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_lovable_clone():
    scenario = Scenario(
        name="dog walking startup landing page",
        description="""
            the user wants to create a new landing page for their dog walking startup

            send the first message to generate the landing page, then a single follow up request to extend it, then give your final verdict
        """,
        agent=LovableAgentAdapter,
        criteria=[
            "agent reads the files before go and making changes",
            "agent modified the index.css file, not only the Index.tsx file",
            "agent created a comprehensive landing page",
            "agent extended the landing page with a new section",
            "agent should NOT say it can't read the file",
            "agent should NOT produce incomplete code or be too lazy to finish",
        ],
        max_turns=5,
    )

    template_path = LovableAgent.clone_template()
    print(f"\n-> Lovable clone template path: {template_path}\n")

    result = await scenario.run(context={"template_path": template_path})

    print(f"\n-> Done, check the results at: {template_path}\n")

    assert result.success
