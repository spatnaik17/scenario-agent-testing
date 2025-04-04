"""
Example demonstrating the early stopping functionality with the updated TestingAgent.

This example shows how the testing process stops immediately when failure criteria are met,
without continuing the conversation unnecessarily.
"""

import json
from typing import Dict, Any, Optional

# Assuming the scenario package is installed or in the Python path
try:
    # Try to import from the installed package
    from scenario.scenario import Scenario
    from scenario.scenario.config import config
except ImportError:
    # Fallback to relative imports if running from within the package
    from ..scenario import Scenario
    from ..scenario.config import config


def buggy_calculator_agent(message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    A buggy calculator agent that makes mistakes on purpose.

    This agent will correctly process addition and subtraction,
    but will deliberately make errors for multiplication and division.

    Args:
        message: The user's message
        context: Optional context information

    Returns:
        Dictionary containing the agent's response
    """
    # Try to parse the mathematical operation from the message
    if "+" in message:
        # Handle addition correctly
        try:
            parts = message.split("+")
            num1 = float(parts[0].strip().split()[-1])
            num2 = float(parts[1].strip().split()[0])
            result = num1 + num2
            return {"message": f"The result of {num1} + {num2} is {result}"}
        except:
            return {"message": "I couldn't understand your addition problem. Please specify it clearly."}

    elif "-" in message:
        # Handle subtraction correctly
        try:
            parts = message.split("-")
            num1 = float(parts[0].strip().split()[-1])
            num2 = float(parts[1].strip().split()[0])
            result = num1 - num2
            return {"message": f"The result of {num1} - {num2} is {result}"}
        except:
            return {"message": "I couldn't understand your subtraction problem. Please specify it clearly."}

    elif "*" in message or "×" in message or " x " in message:
        # Handle multiplication incorrectly (deliberate error)
        try:
            if "*" in message:
                parts = message.split("*")
            elif "×" in message:
                parts = message.split("×")
            else:
                parts = message.split(" x ")

            num1 = float(parts[0].strip().split()[-1])
            num2 = float(parts[1].strip().split()[0])
            # Deliberately calculating incorrectly
            result = num1 * num2 + 1  # Wrong on purpose
            return {"message": f"The result of {num1} multiplied by {num2} is {result}"}
        except:
            return {"message": "I couldn't understand your multiplication problem. Please specify it clearly."}

    elif "/" in message or "÷" in message:
        # Handle division incorrectly (deliberate error)
        try:
            if "/" in message:
                parts = message.split("/")
            else:
                parts = message.split("÷")

            num1 = float(parts[0].strip().split()[-1])
            num2 = float(parts[1].strip().split()[0])

            if num2 == 0:
                return {"message": "I cannot divide by zero, that's undefined."}

            # Deliberately calculating incorrectly
            result = (num1 / num2) * 0.9  # Wrong on purpose
            return {"message": f"The result of {num1} divided by {num2} is {result}"}
        except:
            return {"message": "I couldn't understand your division problem. Please specify it clearly."}

    elif "help" in message.lower():
        return {
            "message": """
I'm a calculator that can perform basic operations. Try asking me:
- What is 25 + 13?
- Calculate 48 - 17
- Multiply 8 * 7
- Divide 100 / 4
"""
        }

    else:
        return {"message": "I can help you with calculations. Please specify an operation like '5 + 3' or ask for 'help'."}


def test_correct_addition():
    """
    Test scenario: The calculator should correctly handle addition operations.
    Expected: Success - Calculator provides correct addition result.
    """
    # Configure a scenario for testing addition
    scenario = Scenario(
        description="Test if the calculator can correctly perform addition.",
        agent=buggy_calculator_agent,
        success_criteria=[
            "Calculator correctly adds two numbers",
            "Calculator provides the exact correct result"
        ],
        failure_criteria=[
            "Calculator gives incorrect result for addition",
            "Calculator fails to respond with a numerical answer"
        ],
        strategy="Ask the calculator to add two numbers and verify the result."
    )

    # Run the scenario and print the result
    result = scenario.run()

    print("\n=== ADDITION TEST RESULT ===")
    print(f"Success: {result.success}")
    if result.success:
        print(f"Met criteria: {result.met_criteria}")
    else:
        print(f"Failure reason: {result.failure_reason}")

    print("\nConversation:")
    for i, msg in enumerate(result.conversation):
        prefix = "User: " if msg["role"] == "user" else "Agent: "
        print(f"{prefix}{msg['content']}")


def test_incorrect_multiplication():
    """
    Test scenario: The calculator should fail on multiplication due to deliberate errors.
    Expected: Failure - Calculator provides incorrect multiplication result.
    """
    # Configure a scenario for testing multiplication
    custom_testing_agent = config(
        model="gpt-3.5-turbo",  # Using a smaller model for testing
        temperature=0.1         # Lower temperature for more deterministic results
    )

    scenario = Scenario(
        description="Test if the calculator can correctly perform multiplication.",
        agent=buggy_calculator_agent,
        testing_agent=custom_testing_agent,
        success_criteria=[
            "Calculator correctly multiplies two numbers",
            "Calculator provides the exact correct result"
        ],
        failure_criteria=[
            "Calculator gives incorrect result for multiplication",
            "Result differs from the correct mathematical product",
            "Calculator fails to respond with a numerical answer"
        ],
        strategy="Ask the calculator to multiply two numbers with an obvious result (like 5 * 5) and verify the result."
    )

    # Run the scenario and print the result
    result = scenario.run()

    print("\n=== MULTIPLICATION TEST RESULT ===")
    print(f"Success: {result.success}")
    if result.success:
        print(f"Met criteria: {result.met_criteria}")
    else:
        print(f"Failure reason: {result.failure_reason}")
        if hasattr(result, "triggered_failures") and result.triggered_failures:
            print(f"Triggered failures: {result.triggered_failures}")

    print("\nConversation:")
    for i, msg in enumerate(result.conversation):
        prefix = "User: " if msg["role"] == "user" else "Agent: "
        print(f"{prefix}{msg['content']}")

    return result


if __name__ == "__main__":
    print("Running calculator tests with early stopping...")

    # Test addition (should succeed)
    test_correct_addition()

    # Test multiplication (should fail early due to incorrect result)
    multiplication_result = test_incorrect_multiplication()

    # Verify early stopping worked by checking the conversation length
    print("\n=== EARLY STOPPING VERIFICATION ===")
    conversation_turns = len(multiplication_result.conversation) // 2  # Each turn is 2 messages
    print(f"Conversation completed in {conversation_turns} turns")
    print(f"Early stopping: {'Yes' if conversation_turns < 3 else 'No'}")