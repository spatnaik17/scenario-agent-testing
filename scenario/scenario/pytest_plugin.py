"""
Pytest plugin for Scenario testing library.
"""
import pytest
from typing import Dict, List, Any, Optional

from .scenario import Scenario


def pytest_configure(config):
    """Register the agent_test marker."""
    config.addinivalue_line(
        "markers",
        "agent_test: mark test as an agent scenario test"
    )


@pytest.fixture
def scenario_reporter():
    """
    A pytest fixture for collecting and reporting scenario test results.

    This fixture can be used to collect results from multiple scenario tests
    and generate a summary report at the end of the test session.
    """
    class ScenarioReporter:
        def __init__(self):
            self.results = []

        def add_result(self, scenario, result):
            """Add a test result to the reporter."""
            self.results.append({
                "scenario": scenario,
                "result": result
            })

        def get_summary(self):
            """Get a summary of all test results."""
            total = len(self.results)
            passed = sum(1 for r in self.results if r["result"].success)
            failed = total - passed

            return {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": round(passed / total * 100, 2) if total else 0
            }

        def print_report(self):
            """Print a detailed report of all test results."""
            summary = self.get_summary()

            print("\n=== Scenario Test Report ===")
            print(f"Total Scenarios: {summary['total']}")
            print(f"Passed: {summary['passed']}")
            print(f"Failed: {summary['failed']}")
            print(f"Success Rate: {summary['success_rate']}%")

            print("\nDetailed Results:")
            for idx, item in enumerate(self.results, 1):
                scenario = item["scenario"]
                result = item["result"]

                status = "PASSED" if result.success else "FAILED"
                print(f"\n{idx}. {scenario.description} - {status}")

                if not result.success:
                    print(f"   Failure Reason: {result.failure_reason}")

                if result.met_criteria:
                    print(f"   Met Criteria: {len(result.met_criteria)}/{len(scenario.success_criteria)}")

                if result.triggered_failures:
                    print(f"   Triggered Failures: {len(result.triggered_failures)}")

    reporter = ScenarioReporter()
    yield reporter
    # Print the report when the fixture is torn down
    reporter.print_report()