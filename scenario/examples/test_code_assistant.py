"""
Example test for a code assistant agent.

This example demonstrates how to test a code-generating assistant
that can produce Python code based on user requests.
"""
import re
import ast
import pytest
from typing import Dict, Any, List, Optional

from scenario import Scenario, TestingAgent, config, ScenarioResult


# This simulates a code assistant agent
def code_assistant_agent(message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    A simulated code assistant agent that generates Python code.

    In a real implementation, this would call an actual LLM-based code assistant.
    This simplified version just handles a few common code generation tasks.
    """
    # Initialize context if needed
    context = context or {}
    context["history"] = context.get("history", [])
    context["history"].append({"role": "user", "content": message})

    # Track the current code state
    current_code = context.get("current_code", "")

    # Process the message
    message_lower = message.lower()

    # Initial greeting
    if "hello" in message_lower or "hi " in message_lower:
        response = "Hello! I'm a code assistant. What kind of Python code would you like me to write?"

    # Handle requests to create functions
    elif "function" in message_lower or "create" in message_lower or "write" in message_lower:
        if "fibonacci" in message_lower:
            # Generate Fibonacci function
            code = """
def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number."""
    if n <= 0:
        raise ValueError("Input must be a positive integer")
    if n == 1 or n == 2:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)
"""
            current_code = code
            response = "I've created a recursive Fibonacci function. Note that this implementation has exponential time complexity. Would you like me to optimize it?"

        elif "factorial" in message_lower:
            # Generate factorial function
            code = """
def factorial(n: int) -> int:
    """Calculate the factorial of n."""
    if n < 0:
        raise ValueError("Input must be a non-negative integer")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
"""
            current_code = code
            response = "I've created a recursive factorial function. Would you like me to create an iterative version instead?"

        elif "sort" in message_lower:
            # Generate sorting function
            code = """
def bubble_sort(arr: List[int]) -> List[int]:
    """Sort an array using bubble sort algorithm."""
    n = len(arr)
    # Create a copy to avoid modifying the original
    result = arr.copy()

    for i in range(n):
        # Flag to optimize if no swaps are made
        swapped = False

        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
                swapped = True

        # If no swaps were made in this pass, array is sorted
        if not swapped:
            break

    return result
"""
            current_code = code
            response = "I've created a bubble sort implementation. This has O(n²) time complexity. Would you like me to implement a more efficient sorting algorithm instead?"

        else:
            # Generic function template
            code = """
def example_function(param1: str, param2: int = 0) -> str:
    """Example function with parameters."""
    result = param1 * param2
    return result
"""
            current_code = code
            response = "I've created a simple example function. Please let me know what specific functionality you'd like it to have."

    # Handle optimization requests
    elif "optimize" in message_lower or "improve" in message_lower:
        if "fibonacci" in message_lower or "fibonacci" in current_code:
            # Optimize Fibonacci with memoization
            code = """
def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number using dynamic programming."""
    if n <= 0:
        raise ValueError("Input must be a positive integer")

    # Initialize cache
    fib_cache = {1: 1, 2: 1}

    def fib_memo(k: int) -> int:
        if k in fib_cache:
            return fib_cache[k]
        fib_cache[k] = fib_memo(k - 1) + fib_memo(k - 2)
        return fib_cache[k]

    return fib_memo(n)
"""
            current_code = code
            response = "I've optimized the Fibonacci function using memoization to avoid redundant calculations. This improves the time complexity from O(2ⁿ) to O(n)."

        elif "sort" in message_lower or "sort" in current_code:
            # Implement a more efficient sorting algorithm
            code = """
def merge_sort(arr: List[int]) -> List[int]:
    """Sort an array using the merge sort algorithm."""
    if len(arr) <= 1:
        return arr.copy()

    # Split the array into two halves
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    # Merge the sorted halves
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # Add remaining elements
    result.extend(left[i:])
    result.extend(right[j:])
    return result
"""
            current_code = code
            response = "I've replaced bubble sort with merge sort. This improves the time complexity from O(n²) to O(n log n)."

        else:
            response = "What code would you like me to optimize? Please share the code or tell me what functionality you need."

    # Handle requests to add tests
    elif "test" in message_lower or "unit test" in message_lower:
        if not current_code:
            response = "I need to see the code you want to test first. Please share it with me."
        elif "fibonacci" in current_code:
            # Add tests for Fibonacci
            test_code = """
import unittest

class TestFibonacci(unittest.TestCase):

    def test_fibonacci_base_cases(self):
        self.assertEqual(fibonacci(1), 1)
        self.assertEqual(fibonacci(2), 1)

    def test_fibonacci_values(self):
        self.assertEqual(fibonacci(3), 2)
        self.assertEqual(fibonacci(4), 3)
        self.assertEqual(fibonacci(5), 5)
        self.assertEqual(fibonacci(10), 55)

    def test_fibonacci_invalid_input(self):
        with self.assertRaises(ValueError):
            fibonacci(0)
        with self.assertRaises(ValueError):
            fibonacci(-1)

if __name__ == "__main__":
    unittest.main()
"""
            current_code += "\n" + test_code
            response = "I've added unit tests for the Fibonacci function. The tests cover base cases, typical values, and invalid inputs."

        elif "factorial" in current_code:
            # Add tests for factorial
            test_code = """
import unittest

class TestFactorial(unittest.TestCase):

    def test_factorial_base_cases(self):
        self.assertEqual(factorial(0), 1)
        self.assertEqual(factorial(1), 1)

    def test_factorial_values(self):
        self.assertEqual(factorial(2), 2)
        self.assertEqual(factorial(3), 6)
        self.assertEqual(factorial(5), 120)

    def test_factorial_invalid_input(self):
        with self.assertRaises(ValueError):
            factorial(-1)

if __name__ == "__main__":
    unittest.main()
"""
            current_code += "\n" + test_code
            response = "I've added unit tests for the factorial function. The tests cover base cases, typical values, and invalid inputs."

        elif "sort" in current_code:
            # Add tests for sorting
            if "bubble_sort" in current_code:
                function_name = "bubble_sort"
            elif "merge_sort" in current_code:
                function_name = "merge_sort"
            else:
                function_name = "sort_function"

            test_code = f"""
import unittest
from typing import List

class Test{function_name.title().replace('_', '')}(unittest.TestCase):

    def test_empty_list(self):
        self.assertEqual({function_name}([]), [])

    def test_sorted_list(self):
        arr = [1, 2, 3, 4, 5]
        self.assertEqual({function_name}(arr), [1, 2, 3, 4, 5])
        self.assertEqual(arr, [1, 2, 3, 4, 5])  # Original unchanged

    def test_reverse_sorted_list(self):
        self.assertEqual({function_name}([5, 4, 3, 2, 1]), [1, 2, 3, 4, 5])

    def test_random_list(self):
        self.assertEqual({function_name}([3, 1, 4, 1, 5, 9, 2]), [1, 1, 2, 3, 4, 5, 9])

    def test_duplicate_elements(self):
        self.assertEqual({function_name}([3, 3, 2, 1, 2, 1]), [1, 1, 2, 2, 3, 3])

if __name__ == "__main__":
    unittest.main()
"""
            current_code += "\n" + test_code
            response = f"I've added unit tests for the {function_name} function. The tests cover empty lists, pre-sorted lists, reverse-sorted lists, and lists with duplicate elements."

        else:
            response = "I'm not sure what code you'd like me to test. Please provide more details about the functionality."

    # Default response
    else:
        response = "I can help you write Python code. Would you like me to create a function, optimize existing code, or add unit tests?"

    # Update context with the current code
    context["current_code"] = current_code
    context["history"].append({"role": "assistant", "content": response})

    # Return the response and relevant artifacts
    return {
        "message": response,
        "code": current_code,
        "code_valid": is_valid_python(current_code),
        "functions_count": count_functions(current_code),
        "tests_count": count_tests(current_code),
    }


# Helper functions for code validation and analysis
def is_valid_python(code: str) -> bool:
    """Check if code is valid Python syntax."""
    if not code.strip():
        return True

    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def count_functions(code: str) -> int:
    """Count the number of function definitions in the code."""
    if not code.strip():
        return 0

    try:
        tree = ast.parse(code)
        return sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
    except SyntaxError:
        return 0


def count_tests(code: str) -> int:
    """Count the number of test methods in the code."""
    if not code.strip():
        return 0

    try:
        tree = ast.parse(code)
        test_methods = [node for node in ast.walk(tree)
                       if isinstance(node, ast.FunctionDef)
                       and node.name.startswith('test_')]
        return len(test_methods)
    except SyntaxError:
        return 0


# Custom validation functions
def validate_code_functionality(result: ScenarioResult, function_type: str) -> bool:
    """
    Validate that the generated code implements the expected functionality.

    Args:
        result: The test result containing code artifacts
        function_type: The type of function (e.g., 'fibonacci', 'factorial', 'sort')

    Returns:
        bool: True if the code correctly implements the functionality
    """
    code = result.artifacts.get("code", "")

    if not code or not result.artifacts.get("code_valid", False):
        return False

    # Set up a namespace to execute the code
    namespace = {}
    try:
        exec(code, namespace)
    except Exception:
        return False

    # Test function behavior based on type
    if function_type == "fibonacci":
        if "fibonacci" not in namespace:
            return False
        try:
            # Test basic Fibonacci properties
            fib = namespace["fibonacci"]
            return (fib(1) == 1 and
                    fib(2) == 1 and
                    fib(3) == 2 and
                    fib(4) == 3 and
                    fib(5) == 5)
        except Exception:
            return False

    elif function_type == "factorial":
        if "factorial" not in namespace:
            return False
        try:
            # Test basic factorial properties
            fact = namespace["factorial"]
            return (fact(0) == 1 and
                    fact(1) == 1 and
                    fact(2) == 2 and
                    fact(3) == 6 and
                    fact(5) == 120)
        except Exception:
            return False

    elif function_type == "sort":
        # Look for any sort function
        sort_function = None
        if "bubble_sort" in namespace:
            sort_function = namespace["bubble_sort"]
        elif "merge_sort" in namespace:
            sort_function = namespace["merge_sort"]
        elif "quick_sort" in namespace:
            sort_function = namespace["quick_sort"]

        if not sort_function:
            return False

        try:
            # Test sorting behavior
            return (sort_function([3, 1, 4, 1, 5, 9, 2]) == [1, 1, 2, 3, 4, 5, 9] and
                    sort_function([]) == [] and
                    sort_function([1]) == [1])
        except Exception:
            return False

    return False


# Configure the testing agent
config(model="gpt-3.5-turbo")


@pytest.mark.agent_test
def test_fibonacci_implementation(scenario_reporter):
    """
    Test that the code assistant can implement a Fibonacci function.
    """
    # Define the test scenario
    scenario = Scenario(
        description="User asks for a Fibonacci function implementation",
        agent=code_assistant_agent,  # Specify the agent to test

        strategy="""
        Start with a greeting.
        Ask the assistant to write a function that calculates Fibonacci numbers.
        Once it responds, ask it to optimize the function for better performance.
        Then ask for unit tests for the function.
        """,

        success_criteria=[
            "Assistant creates a working Fibonacci function",
            "Assistant optimizes the function when asked",
            "Assistant adds unit tests when requested",
            "All code is syntactically valid Python",
            "The final function correctly calculates Fibonacci numbers"
        ],

        failure_criteria=[
            "Assistant produces code with syntax errors",
            "Assistant fails to implement a Fibonacci function",
            "The function does not correctly calculate Fibonacci values",
            "Assistant fails to add unit tests when requested",
            "Assistant fails to improve the function when asked to optimize"
        ]
    )

    # Run the test directly from the scenario
    result = scenario.run()

    # Add result to the reporter
    scenario_reporter.add_result(scenario, result)

    # Assert the scenario passed
    assert result.success, f"Scenario failed: {result.failure_reason}"

    # Custom validations
    assert result.artifacts.get("code_valid", False), "Generated code is not valid Python"
    assert result.artifacts.get("functions_count", 0) >= 1, "No functions were defined"
    assert result.artifacts.get("tests_count", 0) >= 3, "Insufficient test methods were created"
    assert validate_code_functionality(result, "fibonacci"), "Fibonacci function doesn't work correctly"


@pytest.mark.agent_test
def test_sorting_algorithm_implementation(scenario_reporter):
    """
    Test that the code assistant can implement and optimize a sorting algorithm.
    """
    # Define the test scenario
    scenario = Scenario(
        description="User asks for a sorting algorithm implementation",
        agent=code_assistant_agent,  # Specify the agent to test

        strategy="""
        Start with a greeting.
        Ask the assistant to write a function that sorts a list of numbers.
        Once it responds, ask it to optimize the sorting algorithm for better performance.
        Then ask for unit tests for the sorting function.
        """,

        success_criteria=[
            "Assistant creates a working sorting function",
            "Assistant implements a more efficient algorithm when asked to optimize",
            "Assistant adds comprehensive unit tests when requested",
            "All code is syntactically valid Python",
            "The final function correctly sorts lists of numbers"
        ],

        failure_criteria=[
            "Assistant produces code with syntax errors",
            "Assistant fails to implement a sorting function",
            "The function does not correctly sort lists",
            "Assistant fails to add unit tests when requested",
            "Assistant doesn't improve efficiency when asked to optimize"
        ]
    )

    # Run the test directly from the scenario
    result = scenario.run()

    # Add result to the reporter
    scenario_reporter.add_result(scenario, result)

    # Assert the scenario passed
    assert result.success, f"Scenario failed: {result.failure_reason}"

    # Custom validations
    assert result.artifacts.get("code_valid", False), "Generated code is not valid Python"
    assert result.artifacts.get("functions_count", 0) >= 1, "No functions were defined"
    assert result.artifacts.get("tests_count", 0) >= 3, "Insufficient test methods were created"
    assert validate_code_functionality(result, "sort"), "Sorting function doesn't work correctly"