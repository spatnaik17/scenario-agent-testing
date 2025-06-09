import pytest

from examples.lovable_clone.lovable_agent import LovableAgent
from scenario import Scenario, TestingAgent

Scenario.configure(testing_agent=TestingAgent(model="anthropic/claude-3-5-sonnet-latest"))


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_lovable_clone():
    template_path = LovableAgent.clone_template()
    print(f"\n-> Lovable clone template path: {template_path}\n")

    async def lovable_agent(message: str, context):
        lovable_agent = LovableAgent()

        _, messages = await lovable_agent.process_user_message(message, template_path)

        return {"messages": messages}

    scenario = Scenario(
        name="dog walking startup landing page",
        description="""
            the user wants to create a new landing page for their dog walking startup

            send the first message to generate the landing page, then a single follow up request to extend it, then give your final verdict
        """,
        agent=lovable_agent,
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

    result = await scenario.run()

    print(f"\n-> Done, check the results at: {template_path}\n")

    assert result.success
