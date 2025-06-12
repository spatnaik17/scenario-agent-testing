"""
Example test for a vegetarian recipe agent.

This example demonstrates testing an AI agent that generates vegetarian recipes.
"""

import pytest

from scenario import (
    Scenario,
    TestingAgent,
    scenario_cache,
    ScenarioAgentAdapter,
    AgentInput,
    AgentReturnTypes,
)

Scenario.configure(testing_agent=TestingAgent.with_config(model="openai/gpt-4o-mini"))


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_vegetarian_recipe_agent():
    class VegetarianRecipeAgentAdapter(ScenarioAgentAdapter):
        def __init__(self):
            self.agent = VegetarianRecipeAgent()

        async def call(self, input: AgentInput) -> AgentReturnTypes:
            return self.agent.run(input.last_new_user_message_str())

    # Define the scenario
    scenario = Scenario(
        name="dinner idea",
        description="""
            It's saturday evening, the user is very hungry and tired,
            but have no money to order out, so they are looking for a recipe.

            The user never mentions they want a vegetarian recipe.
        """,
        agent=VegetarianRecipeAgentAdapter,
        criteria=[
            "Agent should not ask more than two follow-up questions",
            "Agent should generate a recipe",
            "Recipe should include a list of ingredients",
            "Recipe should include step-by-step cooking instructions",
            "Recipe should be vegetarian and not include any sort of meat",
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
                    "content": """
                        You are a vegetarian recipe agent.
                        Given the user request, ask AT MOST ONE follow-up question,
                        then provide a complete recipe. Keep your responses concise and focused.
                    """,
                },
                *self.history,
            ],
        )
        message = response.choices[0].message  # type: ignore
        self.history.append(message)

        return message
