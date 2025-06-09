"""
Example test for a vegetarian recipe agent.

This example demonstrates testing an AI agent that generates vegetarian recipes.
"""

from typing import Dict, Any, Optional
import pytest
from dotenv import load_dotenv
import litellm

load_dotenv()

from scenario import Scenario, TestingAgent, scenario_cache

Scenario.configure(testing_agent=TestingAgent(model="openai/gpt-4o-mini"), verbose=2)


def create_vegetarian_recipe_agent():
    history = []

    @scenario_cache()
    def vegetarian_recipe_agent(
        message: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        nonlocal history

        history.append({"role": "user", "content": message})
        response = litellm.completion(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a vegetarian recipe agent.
                    Given the user request, ask AT MOST ONE follow-up question,
                    then provide a complete recipe. Keep your responses concise and focused.""",
                },
                *history,
            ],
        )
        message = response.choices[0].message  # type: ignore
        history.append(message)

        return {"messages": [message]}

    return vegetarian_recipe_agent


@pytest.mark.agent_test
@pytest.mark.asyncio_concurrent(group="vegetarian_recipe_agent")
async def test_vegetarian_recipe_agent():
    # Define the agent under test
    vegetarian_recipe_agent = create_vegetarian_recipe_agent()

    # Define the scenario
    scenario = Scenario(
        name="dinner idea",
        description="User is looking for a dinner idea",
        agent=vegetarian_recipe_agent,
        criteria=[
            "Recipe agent generates a vegetarian recipe",
            "Recipe includes a list of ingredients",
            "Recipe includes step-by-step cooking instructions",
            "The recipe is vegetarian and does not include meat",
            "The should NOT ask more than two follow-up questions",
        ],
        max_turns=5,
    )

    # Run the scenario and get results
    result = await scenario.run()

    # Assert for pytest to know whether the test passed
    assert result.success


@pytest.mark.agent_test
@pytest.mark.asyncio_concurrent(group="vegetarian_recipe_agent")
async def test_user_is_hungry():
    # Define the agent under test
    vegetarian_recipe_agent = create_vegetarian_recipe_agent()

    # Define the scenario
    scenario = Scenario(
        name="hungry user",
        description="User is very very hungry, they say they could eat a cow",
        agent=vegetarian_recipe_agent,
        criteria=[
            "Recipe agent generates a vegetarian recipe",
            "Recipe includes a list of ingredients",
            "Recipe includes step-by-step cooking instructions",
            "The recipe is vegetarian and does not include meat",
            "The agent should NOT ask more than two follow-up questions",
        ],
        max_turns=5,
    )

    # Run the scenario and get results
    result = await scenario.run()

    # Assert for pytest to know whether the test passed
    assert result.success
