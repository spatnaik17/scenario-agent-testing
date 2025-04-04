"""
Scenario module: defines the core Scenario class for agent testing.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, Callable

from .result import ScenarioResult
from .testing_agent import DEFAULT_TESTING_AGENT


@dataclass
class Scenario:
    """
    A scenario represents a specific testing case for an agent.

    It includes:
    - A description of the scenario
    - Success criteria to determine if the agent behaved correctly
    - Failure criteria to determine if the agent failed
    - An optional strategy that guides the testing agent
    - Optional additional parameters
    """

    description: str
    success_criteria: List[str]
    failure_criteria: List[str]
    agent: Callable[[str, Optional[Dict[str, Any]]], Dict[str, Any]]
    testing_agent: Any = None  # Will use DEFAULT_TESTING_AGENT if None
    strategy: Optional[str] = None
    max_turns: int = 10
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate scenario configuration after initialization."""
        if not self.description:
            raise ValueError("Scenario description cannot be empty")

        if not self.success_criteria:
            raise ValueError("Scenario must have at least one success criterion")

        if not self.failure_criteria:
            raise ValueError("Scenario must have at least one failure criterion")

        if self.max_turns < 1:
            raise ValueError("max_turns must be a positive integer")

        # Ensure agent is callable
        if not callable(self.agent):
            raise ValueError("Agent must be a callable function")

    def run(self, context: Optional[Dict[str, Any]] = None) -> ScenarioResult:
        """
        Run the scenario against the agent under test.

        Args:
            context: Optional initial context for the agent

        Returns:
            ScenarioResult containing the test outcome
        """
        # Use the provided testing agent or the default
        testing_agent = self.testing_agent or DEFAULT_TESTING_AGENT

        # Run the scenario using the testing agent
        return testing_agent.run_scenario(self.agent, self, context)

    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to a dictionary representation."""
        return {
            "description": self.description,
            "success_criteria": self.success_criteria,
            "failure_criteria": self.failure_criteria,
            "strategy": self.strategy,
            "max_turns": self.max_turns,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], agent: Callable, testing_agent: Any = None) -> "Scenario":
        """Create a scenario from a dictionary representation."""
        return cls(
            description=data["description"],
            success_criteria=data["success_criteria"],
            failure_criteria=data["failure_criteria"],
            agent=agent,
            testing_agent=testing_agent,
            strategy=data.get("strategy"),
            max_turns=data.get("max_turns", 10),
            metadata=data.get("metadata", {}),
        )