import pytest

from examples.lovable_clone.lovable_agent import LovableAgent
from scenario import Scenario

Scenario.configure(testing_agent={"model": "openai/gpt-4o-mini"})


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
        "user wants to create a new landing page for their dog walking startup",
        agent=lovable_agent,
        strategy="send the first message to generate the landing page, then a single follow up request to extend it, then give your final verdict",
        success_criteria=[
            "agent reads the files before go and making changes",
            "agent modifies index.css file",
            "agent modifies App.tsx file",
            "agent creates a comprehensive landing page",
        ],
        failure_criteria=[
            "agent says it can't read the file",
            "agent produces incomplete code or is too lazy to finish",
        ],
        max_turns=5,
    )

    result = await scenario.run()

    print(f"\n-> Done, check the results at: {template_path}\n")

    assert result.success
