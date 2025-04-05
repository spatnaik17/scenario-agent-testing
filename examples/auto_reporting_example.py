"""
Example demonstrating automatic reporting with pytest.

This example shows how scenario results are automatically reported without
manual configuration when running with pytest.
"""

import pytest
from typing import Dict, Any, Optional

from scenario import Scenario


def calculator_agent(message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    A simple calculator agent for testing purposes.

    Args:
        message: The user's message
        context: Optional context

    Returns:
        Dictionary containing the agent's response
    """
    # Simple calculator that handles basic operations
    if "+" in message:
        try:
            parts = message.split("+")
            num1 = float(parts[0].strip().split()[-1])
            num2 = float(parts[1].strip().split()[0])
            result = num1 + num2
            return {"message": f"The result of {num1} + {num2} is {result}"}
        except:
            return {"message": "I couldn't understand your addition problem."}

    elif "-" in message:
        try:
            parts = message.split("-")
            num1 = float(parts[0].strip().split()[-1])
            num2 = float(parts[1].strip().split()[0])
            result = num1 - num2
            return {"message": f"The result of {num1} - {num2} is {result}"}
        except:
            return {"message": "I couldn't understand your subtraction problem."}

    # Default response for unsupported operations
    return {"message": "I can only handle addition and subtraction. Try asking something like '5 + 3'."}


# Test that should pass - marked with agent_test
@pytest.mark.agent_test
def test_addition_success():
    """Test the calculator agent with a simple addition problem."""
    test_scenario = Scenario(
        description="Calculator can perform addition",
        agent=calculator_agent,
        success_criteria=["Calculator correctly adds numbers", "Result is numerically accurate"],
        failure_criteria=["Calculator gives incorrect result", "Calculator fails to provide a numerical answer"],
        strategy="Ask the calculator to add two simple numbers."
    )

    # Run the scenario - results will be automatically reported
    result = test_scenario.run()

    # We still need to assert for pytest to pass/fail the test
    assert result.success, f"Test failed: {result.failure_reason}"


# Test that should fail - not marked with agent_test, but will still be reported
def test_division_failure():
    """Test the calculator agent with division, which it doesn't support."""
    division_scenario = Scenario(
        description="Calculator handles division",
        agent=calculator_agent,
        success_criteria=["Calculator correctly divides numbers", "Result is numerically accurate"],
        failure_criteria=["Calculator cannot perform division", "Calculator fails to provide a numerical answer"],
        strategy="Ask the calculator to divide two simple numbers."
    )

    # Run the scenario - results will be automatically reported even though the test isn't marked
    result = division_scenario.run()

    # This will fail because the calculator doesn't support division
    assert result.success, f"Test failed: {result.failure_reason}"


if __name__ == "__main__":
    print("This example is meant to be run with pytest:")
    print("pytest examples/auto_reporting_example.py -v")
    print("\nThe scenario results will be automatically reported at the end of the test run.")