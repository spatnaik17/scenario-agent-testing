# Scenario: Use an Agent to test your Agent

Scenario is a comprehensive library for testing conversational AI agents, designed to define natural language testing scenarios, interact with agents, and evaluate their performance.

## Features

- Define natural language testing scenarios with success and failure criteria
- Automatic test execution using TestingAgent
- Integrated with pytest for easy test creation and reporting
- Support for custom validation functions
- Early stopping when failure criteria are detected
- Function calling for efficient test execution
- Automatic test result reporting with detailed insights

## Installation

Using uv (recommended):
```bash
uv pip install scenario
```

Or with pip:
```bash
pip install scenario
```

## Quick Start

```python
from scenario import Scenario

# Define an agent to test
def weather_agent(message, context=None):
    """A simple agent that responds to weather inquiries."""
    if "weather" in message.lower():
        return {"message": "The weather is sunny and 75°F."}
    return {"message": "I can provide weather information. Ask me about the weather!"}

# Create a test scenario
scenario = Scenario(
    description="Test if the agent can respond to weather inquiries",
    agent=weather_agent,  # Pass the agent to test
    success_criteria=[
        "Agent provides temperature information",
        "Agent responds with weather conditions"
    ],
    failure_criteria=[
        "Agent fails to respond with any weather data",
        "Agent provides incorrect or inconsistent information"
    ],
    strategy="Ask for the current weather"
)

# Run the test and get results
result = scenario.run()
print(f"Test success: {result.success}")
print(f"Conversation: {result.conversation}")

# For more complex validation, you can use a custom testing agent
from scenario import config

# Create a scenario with a custom testing agent
complex_scenario = Scenario(
    description="Test complex weather information with persistence",
    agent=weather_agent,
    testing_agent=config(model="gpt-4"),  # Use a more powerful model
    success_criteria=[
        "Agent remembers previous city when asked for forecast",
        "Agent provides forecast for multiple days when requested"
    ],
    failure_criteria=[
        "Agent forgets the city being discussed",
        "Agent cannot provide multi-day forecast"
    ],
    strategy="First ask about weather in New York, then ask for the forecast without mentioning the city"
)

result = complex_scenario.run()
```

## Key Features

### Early Stopping for Efficiency

The TestingAgent actively evaluates agent responses against success and failure criteria during the conversation and can stop the test immediately when a conclusion is reached:

- When any failure criteria are triggered, the test stops immediately, preventing unnecessary conversation turns.
- When all success criteria are met, the test concludes as successful.
- The result includes detailed information about which criteria were met or unmet.

This is implemented using function calling within the LLM, where it can choose to continue the conversation or invoke a tool to finalize the test with a verdict.

### Pytest Integration with Automatic Reporting

Scenario provides seamless pytest integration with automatic reporting:

```python
import pytest
from scenario import Scenario

@pytest.mark.agent_test
def test_weather_agent():
    """Test if the weather agent provides accurate temperature information."""
    scenario = Scenario(
        description="Test weather information",
        agent=weather_agent,
        success_criteria=["Provides temperature"],
        failure_criteria=["Gives incorrect weather data"]
    )
    result = scenario.run()
    assert result.success
```

When you run your tests with pytest, you'll automatically get a comprehensive report:

```
=== Scenario Test Report ===
Total Scenarios: 2
Passed: 1
Failed: 1
Success Rate: 50.0%

Detailed Results:
1. Test weather information - PASSED
   Met Criteria: 1/1

2. Test complex weather interactions - FAILED
   Failure Reason: Agent failed to remember the previously mentioned city
   Met Criteria: 0/2
   Triggered Failures: 1
```

No manual configuration is needed - just create your scenarios and run them with pytest!

## Examples

The library includes examples for testing various types of agents:

- Travel booking agents
- Website builder agents
- Code assistant agents
- Calculator agents (demonstrating early stopping)
- Recipe agents

Check the `examples/` directory for complete examples.

## License

MIT License