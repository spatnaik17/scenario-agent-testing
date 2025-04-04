# Scenario Example Tests

This directory contains examples of how to use the Scenario testing library for different use cases and agent types.

## Running Examples

To run the examples, make sure you have installed the Scenario library:

```bash
# From the root of the repository
pip install -e .
```

Then run the examples using Python:

```bash
# From the root of the repository
python -m scenario.examples.test_early_stopping
python -m scenario.examples.test_travel_agent
python -m scenario.examples.test_website_builder
python -m scenario.examples.test_code_assistant
```

## Examples Overview

### 1. Calculator with Early Stopping (test_early_stopping.py)

Demonstrates how the TestingAgent can immediately stop testing when failure criteria are met, without continuing the conversation unnecessarily. This example uses:

- A buggy calculator agent that deliberately makes errors in multiplication and division
- Function calling in the TestingAgent to immediately end the test when errors are detected
- Comparison between successful and failing test cases

This example specifically illustrates the efficiency of early stopping when testing agents that may contain known flaws.

### 2. Travel Agent (test_travel_agent.py)

Demonstrates testing a travel booking assistant with scenarios for:
- Successfully booking a hotel in Paris for 2 nights
- Handling incomplete information failures
- Using custom validation functions

### 3. Website Builder (test_website_builder.py)

Shows how to test agents that modify website code, with:
- Testing site modifications like changing menu colors
- Validation of HTML/CSS changes
- Detecting unintended changes to website code

### 4. Code Assistant (test_code_assistant.py)

Illustrates testing a code-generating assistant with scenarios for:
- Implementing specific algorithms (Fibonacci, sorting)
- Validating code correctness
- Testing code optimization capabilities
- Assessing unit test creation ability

## Writing Your Own Tests

When creating your own tests with Scenario:

1. Define your agent function that takes a message and returns a response
2. Create a Scenario with appropriate success/failure criteria
3. Run the scenario and inspect the results

Example structure:

```python
from scenario.scenario import Scenario

def my_agent(message, context=None):
    # Your agent implementation
    return {"message": "Agent response"}

# Define a test scenario
scenario = Scenario(
    description="Test my agent's ability to X",
    agent=my_agent,
    success_criteria=["Agent does X correctly"],
    failure_criteria=["Agent fails to do X"]
)

# Run the test
result = scenario.run()
print(f"Success: {result.success}")
```