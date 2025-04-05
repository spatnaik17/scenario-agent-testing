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
from scenario.config import config


@pytest.mark.agent_test
def test_vegetarian_recipe_agent():
    """Test if the recipe agent can correctly generate a vegetarian recipe."""
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

    # Configure with more specific criteria and strategy
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
        strategy="Ask for a quick vegetarian pasta recipe with vegetables. If asked for preferences, mention bell peppers and zucchini.",
        max_turns=5,  # Increase max turns to give the agent more chances to complete
    )

    # Run the scenario and get results - reporting is now automatic
    result = scenario.run()

    # Assert for pytest to know whether the test passed
    assert result.success, f"Test failed: {result.failure_reason}"


if __name__ == "__main__":
    """Direct execution will still work but won't show the full report"""
    test_vegetarian_recipe_agent()
