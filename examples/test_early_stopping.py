"""
Example demonstrating the early stopping functionality with the updated TestingAgent.

This example shows how the testing process stops immediately when failure criteria are met,
without continuing the conversation unnecessarily.
"""

from typing import Dict, Any, Optional
from dotenv import load_dotenv
import litellm

load_dotenv()

from scenario import Scenario
from scenario.config import config


def buggy_calculator_agent(
    message: str, context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    response = litellm.completion(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a buggy calculator that always adds 1 to the requested result.",
            },
            {"role": "user", "content": message},
        ],
    )
    return {"message": response.choices[0].message.content}  # type: ignore


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
            "Calculator provides the exact correct result",
        ],
        failure_criteria=[
            "Calculator gives incorrect result for addition",
            "Calculator fails to respond with a numerical answer",
        ],
        strategy="Ask the calculator to add two numbers and verify the result (e.g. 5 + 5).",
    )

    # Run the scenario and print the result
    result = scenario.run()

    print("\n=== ADDITION TEST RESULT ===")

    # print("\n\nresult", result, "\n\n")

    print(f"\nSuccess: {result.success}")
    if result.success:
        print(f"Met criteria: {result.met_criteria}")
    else:
        print(f"Failure reason: {result.failure_reason}")



# def test_incorrect_multiplication():
#     """
#     Test scenario: The calculator should fail on multiplication due to deliberate errors.
#     Expected: Failure - Calculator provides incorrect multiplication result.
#     """
#     # Configure a scenario for testing multiplication
#     custom_testing_agent = config(
#         model="openai/gpt-4o-mini",  # Using a smaller model for testing
#     )

#     scenario = Scenario(
#         description="Test if the calculator can correctly perform multiplication.",
#         agent=buggy_calculator_agent,
#         testing_agent=custom_testing_agent,
#         success_criteria=[
#             "Calculator correctly multiplies two numbers",
#             "Calculator provides the exact correct result",
#         ],
#         failure_criteria=[
#             "Calculator gives incorrect result for multiplication",
#             "Result differs from the correct mathematical product",
#             "Calculator fails to respond with a numerical answer",
#         ],
#         strategy="Ask the calculator to multiply two numbers with an obvious result (like 5 * 5) and verify the result.",
#     )

#     # Run the scenario and print the result
#     result = scenario.run()

#     print("\n=== MULTIPLICATION TEST RESULT ===")
#     print(f"Success: {result.success}")
#     if result.success:
#         print(f"Met criteria: {result.met_criteria}")
#     else:
#         print(f"Failure reason: {result.failure_reason}")
#         if hasattr(result, "triggered_failures") and result.triggered_failures:
#             print(f"Triggered failures: {result.triggered_failures}")

#     print("\nConversation:")
#     for i, msg in enumerate(result.conversation):
#         prefix = "User: " if msg["role"] == "user" else "Agent: "
#         print(f"{prefix}{msg['content']}")

#     return result


if __name__ == "__main__":
    print("Running calculator tests with early stopping...")

    # Test addition (should succeed)
    test_correct_addition()

    # # Test multiplication (should fail early due to incorrect result)
    # multiplication_result = test_incorrect_multiplication()

    # # Verify early stopping worked by checking the conversation length
    # print("\n=== EARLY STOPPING VERIFICATION ===")
    # conversation_turns = (
    #     len(multiplication_result.conversation) // 2
    # )  # Each turn is 2 messages
    # print(f"Conversation completed in {conversation_turns} turns")
    # print(f"Early stopping: {'Yes' if conversation_turns < 3 else 'No'}")
