"""
Example test for a vegetarian recipe agent.

This example demonstrates testing an AI agent that generates vegetarian recipes.
"""

import pytest

from scenario import Scenario, TestingAgent, scenario_cache

Scenario.configure(testing_agent=TestingAgent(model="openai/gpt-4o-mini"))


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_vegetarian_recipe_agent():
    agent = VegetarianRecipeAgent()

    def vegetarian_recipe_agent(message, context):
        # Call your agent here
        return agent.run(message)

    # Define the scenario
    scenario = Scenario(
        "User is looking for a dinner idea",
        agent=vegetarian_recipe_agent,
        strategy="never mention you want vegetarian food",
        success_criteria=[
            "Recipe agent generates a vegetarian recipe",
            "Recipe includes a list of ingredients",
            "Recipe includes step-by-step cooking instructions",
        ],
        failure_criteria=[
            "The recipe is not vegetarian or includes meat",
            "The agent asks more than two follow-up questions",
        ],
    )

    # Run the scenario and get results
    result = await scenario.run()

    # Assert for pytest to know whether the test passed
    assert result.success


# Example agent implementation
import litellm


class VegetarianRecipeAgent:
    def __init__(self):
        self.history = []

    @scenario_cache()
    def run(self, message: str):
        self.history.append({"role": "user", "content": message})

        response = litellm.completion(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a vegetarian recipe agent.
                    Given the user request, ask AT MOST ONE follow-up question,
                    then provide a complete recipe. Keep your responses concise and focused.""",
                },
                *self.history,
            ],
        )
        message = response.choices[0].message  # type: ignore
        self.history.append(message)

        return {"messages": [message]}
