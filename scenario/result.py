"""
Result module: defines the class for scenario test results.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class ScenarioResult:
    """
    Represents the results of a scenario test run.

    Attributes:
        success: Whether the scenario passed
        conversation: The conversation history
        artifacts: Additional artifacts from the test
        failure_reason: Reason for failure, if failed
        met_criteria: List of success criteria that were met
        unmet_criteria: List of success criteria that were not met
        triggered_failures: List of failure criteria that were triggered
    """

    success: bool
    conversation: List[Dict[str, str]]
    artifacts: Dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None
    met_criteria: List[str] = field(default_factory=list)
    unmet_criteria: List[str] = field(default_factory=list)
    triggered_failures: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the result after initialization."""
        if not self.success and not self.failure_reason:
            raise ValueError("Failed scenarios must have a failure reason")

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a dictionary representation."""
        return {
            "success": self.success,
            "conversation": self.conversation,
            "artifacts": self.artifacts,
            "failure_reason": self.failure_reason,
            "met_criteria": self.met_criteria,
            "unmet_criteria": self.unmet_criteria,
            "triggered_failures": self.triggered_failures,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioResult":
        """Create a result from a dictionary representation."""
        return cls(
            success=data["success"],
            conversation=data["conversation"],
            artifacts=data.get("artifacts", {}),
            failure_reason=data.get("failure_reason"),
            met_criteria=data.get("met_criteria", []),
            unmet_criteria=data.get("unmet_criteria", []),
            triggered_failures=data.get("triggered_failures", []),
        )

    @classmethod
    def success_result(
        cls,
        conversation: List[Dict[str, str]],
        artifacts: Dict[str, Any],
        met_criteria: List[str]
    ) -> "ScenarioResult":
        """Create a successful result."""
        return cls(
            success=True,
            conversation=conversation,
            artifacts=artifacts,
            met_criteria=met_criteria,
            unmet_criteria=[],
            triggered_failures=[],
        )

    @classmethod
    def failure_result(
        cls,
        conversation: List[Dict[str, str]],
        artifacts: Dict[str, Any],
        failure_reason: str,
        met_criteria: Optional[List[str]] = None,
        unmet_criteria: Optional[List[str]] = None,
        triggered_failures: Optional[List[str]] = None,
    ) -> "ScenarioResult":
        """Create a failed result."""
        return cls(
            success=False,
            conversation=conversation,
            artifacts=artifacts,
            failure_reason=failure_reason,
            met_criteria=met_criteria if met_criteria is not None else [],
            unmet_criteria=unmet_criteria if unmet_criteria is not None else [],
            triggered_failures=triggered_failures if triggered_failures is not None else [],
        )