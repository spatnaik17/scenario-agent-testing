![scenario](./assets/scenario-wide.webp)

<div align="center">
<!-- Discord, PyPI, Docs, etc links -->
</div>

# Scenario: Use an Agent to test your Agent

Scenario is a library for testing agents end-to-end as a human would, but without having to manually do it. The automated testing agent covers every single scenario for you.

You define the scenarios, and the testing agent will simulate your users as it follows them, it will keep chatting and evaluating your agent until it reaches the desired goal or detects an unexpected behavior.

## Getting Started

Install pytest and scenario:

```bash
pip install pytest scenario-testing
```

Now create your first scenario:

```python
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
```

Save it as `tests/test_vegetarian_recipe_agent.py` and run it with pytest:

```bash
pytest -s tests/test_vegetarian_recipe_agent.py
```

Once you connect a real agent on the callback, this is how it will look like:

[![asciicast](https://asciinema.org/a/nvO5GWGzqKTTCd8gtNSezQw11.svg)](https://asciinema.org/a/nvO5GWGzqKTTCd8gtNSezQw11)

You can find a fully working example in [examples/test_vegetarian_recipe_agent.py](examples/test_vegetarian_recipe_agent.py).

## License

MIT License
