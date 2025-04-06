import pytest

from scenario import Scenario, TestingAgent

Scenario.configure(testing_agent=TestingAgent(model="openai/gpt-4o-mini"))


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_vegetarian_recipe_agent():
    def vegetarian_recipe_agent(message, context):
        # Call your agent here
        response = "<Your agent's response>"

        return {"message": response}

    scenario = Scenario(
        "User is looking for a dinner idea",
        agent=vegetarian_recipe_agent,
        success_criteria=[
            "Recipe agent generates a vegetarian recipe",
            "Recipe includes step-by-step cooking instructions",
        ],
        failure_criteria=[
            "The recipe includes meat",
            "The agent asks more than two follow-up questions",
        ],
    )

    result = await scenario.run()

    assert result.success