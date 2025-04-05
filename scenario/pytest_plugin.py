"""
Pytest plugin for Scenario testing library.
"""
import pytest
from typing import Dict, List, Any, Optional
import functools

from .scenario import Scenario


# ScenarioReporter class definition moved outside the fixture for global use
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
        if not self.results:
            return  # Skip report if no results

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

            if hasattr(result, 'met_criteria') and result.met_criteria:
                print(f"   Met Criteria: {len(result.met_criteria)}/{len(scenario.success_criteria)}")

            if hasattr(result, 'triggered_failures') and result.triggered_failures:
                print(f"   Triggered Failures: {len(result.triggered_failures)}")


# Store the original run method
original_run = Scenario.run


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Register the agent_test marker and set up automatic reporting."""
    # Register the marker
    config.addinivalue_line(
        "markers",
        "agent_test: mark test as an agent scenario test"
    )

    # Create a global reporter instance
    config._scenario_reporter = ScenarioReporter()

    # Create a patched version of Scenario.run that auto-reports
    @functools.wraps(original_run)
    def auto_reporting_run(self, *args, **kwargs):
        result = original_run(self, *args, **kwargs)

        # Always report to the global reporter
        config._scenario_reporter.add_result(self, result)

        return result

    # Apply the patch
    Scenario.run = auto_reporting_run


@pytest.hookimpl(trylast=True)
def pytest_unconfigure(config):
    """Clean up and print final report when pytest exits."""
    # Print the final report
    if hasattr(config, "_scenario_reporter"):
        config._scenario_reporter.print_report()

    # Restore the original method
    Scenario.run = original_run


@pytest.fixture
def scenario_reporter(request):
    """
    A pytest fixture for accessing the global scenario reporter.

    This fixture provides access to the same reporter that's used for automatic
    reporting, allowing tests to explicitly interact with the reporter if needed.
    """
    # Get the global reporter from pytest config
    reporter = request.config._scenario_reporter
    yield reporter
    # No need to print report here as it's handled by pytest_unconfigure