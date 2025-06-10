"""
Pytest plugin for Scenario testing library.
"""

import pytest
from typing import TypedDict
import functools
from termcolor import colored

from scenario.types import ScenarioResult

from .scenario import Scenario


class ScenarioReporterResults(TypedDict):
    scenario: Scenario
    result: ScenarioResult


# ScenarioReporter class definition moved outside the fixture for global use
class ScenarioReporter:
    def __init__(self):
        self.results: list[ScenarioReporterResults] = []

    def add_result(self, scenario, result):
        """Add a test result to the reporter."""
        self.results.append({"scenario": scenario, "result": result})

    def get_summary(self):
        """Get a summary of all test results."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["result"].success)
        failed = total - passed

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": round(passed / total * 100, 2) if total else 0,
        }

    def print_report(self):
        """Print a detailed report of all test results."""
        if not self.results:
            return  # Skip report if no results

        summary = self.get_summary()

        print("\n" + colored("=== Scenario Test Report ===", "cyan", attrs=["bold"]))
        print(colored(f"Total Scenarios: {summary['total']}", "white"))
        print(
            colored(
                f"Passed: {summary['passed']}",
                "green" if summary["passed"] > 0 else "white",
            )
        )
        print(
            colored(
                f"Failed: {summary['failed']}",
                "red" if summary["failed"] > 0 else "white",
            )
        )

        # Color the success rate based on its value
        success_rate = summary["success_rate"]
        rate_color = (
            "green"
            if success_rate == 100
            else "yellow" if success_rate >= 70 else "red"
        )
        print(colored(f"Success Rate: {success_rate}%", rate_color))

        for idx, item in enumerate(self.results, 1):
            scenario = item["scenario"]
            result = item["result"]

            status = "PASSED" if result.success else "FAILED"
            status_color = "green" if result.success else "red"

            time = ""
            if result.total_time and result.agent_time:
                time = f" in {result.total_time:.2f}s (agent: {result.agent_time:.2f}s)"

            print(
                f"\n{idx}. {scenario.name} - {colored(status, status_color, attrs=['bold'])}{time}"
            )

            print(
                colored(
                    f"   Reasoning: {result.reasoning}",
                    "green" if result.success else "red",
                )
            )

            if hasattr(result, "passed_criteria") and result.passed_criteria:
                criteria_count = len(result.passed_criteria)
                total_criteria = len(scenario.criteria)
                criteria_color = (
                    "green" if criteria_count == total_criteria else "yellow"
                )
                print(
                    colored(
                        f"   Passed Criteria: {criteria_count}/{total_criteria}",
                        criteria_color,
                    )
                )

            if hasattr(result, "failed_criteria") and result.failed_criteria:
                print(
                    colored(
                        f"   Failed Criteria: {len(result.failed_criteria)}",
                        "red",
                    )
                )


# Store the original run method
original_run = Scenario.run


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Register the agent_test marker and set up automatic reporting."""
    # Register the marker
    config.addinivalue_line(
        "markers", "agent_test: mark test as an agent scenario test"
    )

    if config.getoption("--debug"):
        print(colored("\nScenario debug mode enabled (--debug).", "yellow"))
        Scenario.configure(verbose=True, debug=True)

    # Create a global reporter instance
    config._scenario_reporter = ScenarioReporter()

    # Create a patched version of Scenario.run that auto-reports
    @functools.wraps(original_run)
    async def auto_reporting_run(self, *args, **kwargs):
        result = await original_run(self, *args, **kwargs)

        # Always report to the global reporter
        # Ensure the reporter exists before adding result
        if hasattr(config, "_scenario_reporter"):
            config._scenario_reporter.add_result(self, result)
        else:
            # Handle case where reporter might not be initialized (should not happen with current setup)
            print(colored("Warning: Scenario reporter not found during run.", "yellow"))

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
