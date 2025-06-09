![scenario](https://github.com/langwatch/scenario/raw/main/assets/scenario-wide.webp)

<div align="center">
<!-- Discord, PyPI, Docs, etc links -->
</div>

# Scenario: Use an Agent to test your Agent

Scenario is a library for testing agents end-to-end as a human would, but without having to manually do it. The automated testing agent covers every single scenario for you.

You define the scenarios, and the testing agent will simulate your users as it follows them, it will keep chatting and evaluating your agent until it reaches the desired goal or detects an unexpected behavior.

[📺 Video Tutorial](https://www.youtube.com/watch?v=f8NLpkY0Av4)

### See also

- [Scenario TypeScript](https://github.com/langwatch/scenario-ts/)
- [Scenario Go](https://github.com/langwatch/scenario-go/)

## Getting Started

Install pytest and scenario:

```bash
pip install pytest langwatch-scenario
```

Now create your first scenario and save it as `tests/test_vegetarian_recipe_agent.py`:

```python
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

    # Define the simulated scenario
    scenario = Scenario(
        name="dinner idea",
        description="""
            It's saturday evening, the user is very hungry and tired,
            but have no money to order out, so they are looking for a recipe.

            The user never mentions they want a vegetarian recipe.
        """,
        agent=vegetarian_recipe_agent,
        # List the evaluation criteria for the scenario to be considered successful
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

        return {"messages": [message]}

```

Create a `.env` file and put your OpenAI API key in it:

```bash
OPENAI_API_KEY=<your-api-key>
```

Now run it with pytest:

```bash
pytest -s tests/test_vegetarian_recipe_agent.py
```

This is how it will look like:

[![asciicast](https://asciinema.org/a/nvO5GWGzqKTTCd8gtNSezQw11.svg)](https://asciinema.org/a/nvO5GWGzqKTTCd8gtNSezQw11)

You can find a fully working example in [examples/test_vegetarian_recipe_agent.py](examples/test_vegetarian_recipe_agent.py).

## Customize strategy and max_turns

You can customize how should the testing agent go about testing by defining a `strategy` field. You can also limit the maximum number of turns the scenario will take by setting the `max_turns` field (defaults to 10).

For example, in this Lovable Clone scenario test:

```python
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
```

You can find a fully working Lovable Clone example in [examples/test_lovable_clone.py](examples/test_lovable_clone.py).

## Debug mode

You can enable debug mode by setting the `debug` field to `True` in the `Scenario.configure` method or in the specific scenario you are running, or by passing the `--debug` flag to pytest.

Debug mode allows you to see the messages in slow motion step by step, and intervene with your own inputs to debug your agent from the middle of the conversation.

```python
Scenario.configure(testing_agent=TestingAgent(model="openai/gpt-4o-mini"), debug=True)
```

or

```bash
pytest -s tests/test_vegetarian_recipe_agent.py --debug
```

## Cache

Each time the scenario runs, the testing agent might chose a different input to start, this is good to make sure it covers the variance of real users as well, however we understand that the non-deterministic nature of it might make it less repeatable, costly and harder to debug. To solve for it, you can use the `cache_key` field in the `Scenario.configure` method or in the specific scenario you are running, this will make the testing agent give the same input for given the same scenario:

```python
Scenario.configure(testing_agent=TestingAgent(model="openai/gpt-4o-mini"), cache_key="42")
```

To bust the cache, you can simply pass a different `cache_key`, disable it, or delete the cache files located at `~/.scenario/cache`.

To go a step further and fully cache the test end-to-end, you can also wrap the LLM calls or any other non-deterministic functions in your application side with the `@scenario_cache` decorator:

```python
class MyAgent:
    @scenario_cache(ignore=["self"])
    def invoke(self, message, context):
        return client.chat.completions.create(
            # ...
        )
```

This will cache any function call you decorate when running the tests and make them repeatable, hashed by the function arguments, the scenario being executed, and the `cache_key` you provided. You can exclude arguments that should not be hashed for the cache key by naming them in the `ignore` argument.

## Disable Output

You can remove the `-s` flag from pytest to hide the output during test, which will only show up if the test fails. Alternatively, you can set `verbose=False` in the `Scenario.configure` method or in the specific scenario you are running.

## Running in parallel

As the number of your scenarios grows, you might want to run them in parallel to speed up your whole test suite. We suggest you to use the [pytest-asyncio-concurrent](https://pypi.org/project/pytest-asyncio-concurrent/) plugin to do so.

Simply install the plugin from the link above, then replace the `@pytest.mark.asyncio` annotation in the tests with `@pytest.mark.asyncio_concurrent`, adding a group name to it to mark the group of scenarions that should be run in parallel together, e.g.:

```python
@pytest.mark.agent_test
@pytest.mark.asyncio_concurrent(group="vegetarian_recipe_agent")
async def test_vegetarian_recipe_agent():
    # ...

@pytest.mark.agent_test
@pytest.mark.asyncio_concurrent(group="vegetarian_recipe_agent")
async def test_user_is_very_hungry():
    # ...
```

Those two scenarios should now run in parallel.

## License

MIT License
