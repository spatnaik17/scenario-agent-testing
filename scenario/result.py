"""
Result module: defines the class for scenario test results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ScenarioResult:
    """
    Represents the results of a scenario test run.

    Attributes:
        success: Whether the scenario passed
        conversation: The conversation history
        reasoning: Reasoning for the result
        passed_criteria: List of criteria that were met
        failed_criteria: List of criteria that were not met
    """

    success: bool
    conversation: List[Dict[str, str]]
    reasoning: Optional[str] = None
    passed_criteria: List[str] = field(default_factory=list)
    failed_criteria: List[str] = field(default_factory=list)
    total_time: Optional[float] = None
    agent_time: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate the result after initialization."""
        if not self.success and not self.reasoning:
            raise ValueError("Failed scenarios must have a reasoning")

    @classmethod
    def success_result(
        cls,
        conversation: List[Dict[str, str]],
        reasoning: Optional[str],
        passed_criteria: List[str],
        total_time: Optional[float] = None,
        agent_time: Optional[float] = None,
    ) -> "ScenarioResult":
        """Create a successful result."""
        return cls(
            success=True,
            conversation=conversation,
            reasoning=reasoning,
            passed_criteria=passed_criteria,
            failed_criteria=[],
            total_time=total_time,
            agent_time=agent_time,
        )

    @classmethod
    def failure_result(
        cls,
        conversation: List[Dict[str, str]],
        reasoning: str,
        passed_criteria: Optional[List[str]] = None,
        failed_criteria: Optional[List[str]] = None,
        total_time: Optional[float] = None,
        agent_time: Optional[float] = None,
    ) -> "ScenarioResult":
        """Create a failed result."""
        return cls(
            success=False,
            conversation=conversation,
            reasoning=reasoning,
            passed_criteria=passed_criteria if passed_criteria is not None else [],
            failed_criteria=failed_criteria if failed_criteria is not None else [],
            total_time=total_time,
            agent_time=agent_time,
        )
