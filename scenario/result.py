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
        met_criteria: List of success criteria that were met
        unmet_criteria: List of success criteria that were not met
        triggered_failures: List of failure criteria that were triggered
    """

    success: bool
    conversation: List[Dict[str, str]]
    reasoning: Optional[str] = None
    met_criteria: List[str] = field(default_factory=list)
    unmet_criteria: List[str] = field(default_factory=list)
    triggered_failures: List[str] = field(default_factory=list)
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
        met_criteria: List[str],
        total_time: Optional[float] = None,
        agent_time: Optional[float] = None,
    ) -> "ScenarioResult":
        """Create a successful result."""
        return cls(
            success=True,
            conversation=conversation,
            reasoning=reasoning,
            met_criteria=met_criteria,
            unmet_criteria=[],
            triggered_failures=[],
            total_time=total_time,
            agent_time=agent_time,
        )

    @classmethod
    def failure_result(
        cls,
        conversation: List[Dict[str, str]],
        reasoning: str,
        met_criteria: Optional[List[str]] = None,
        unmet_criteria: Optional[List[str]] = None,
        triggered_failures: Optional[List[str]] = None,
        total_time: Optional[float] = None,
        agent_time: Optional[float] = None,
    ) -> "ScenarioResult":
        """Create a failed result."""
        return cls(
            success=False,
            conversation=conversation,
            reasoning=reasoning,
            met_criteria=met_criteria if met_criteria is not None else [],
            unmet_criteria=unmet_criteria if unmet_criteria is not None else [],
            triggered_failures=(
                triggered_failures if triggered_failures is not None else []
            ),
            total_time=total_time,
            agent_time=agent_time,
        )
