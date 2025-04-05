"""
Example test for a vegetarian recipe agent.

This example demonstrates testing an AI agent that generates vegetarian recipes.
"""

from typing import Dict, Any, Optional
import pytest
from dotenv import load_dotenv
import litellm

load_dotenv()

from scenario import Scenario

Scenario.configure(testing_agent={"model": "openai/gpt-4o-mini"})


@pytest.mark.agent_test
def test_vegetarian_recipe_agent():
    # Define the agent under test
    history = []

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

    # Define the scenario
    scenario = Scenario(
        description="Test if the recipe agent can correctly generate a vegetarian recipe.",
        agent=vegetarian_recipe_agent,
        success_criteria=[
            "Recipe agent generates a complete vegetarian recipe",
            "Recipe includes a list of ingredients",
            "Recipe includes step-by-step cooking instructions",
        ],
        failure_criteria=[
            "The recipe is not vegetarian or includes meat",
            "The agent fails to provide a complete recipe",
            "The agent asks more than two follow-up questions",
        ],
        max_turns=5,
    )

    # Run the scenario and get results
    result = scenario.run()

    # Assert for pytest to know whether the test passed
    assert result.success
