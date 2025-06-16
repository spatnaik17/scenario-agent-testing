"""
Configuration module for Scenario.
"""

from typing import Optional, Union, ClassVar
from pydantic import BaseModel

class ModelConfig(BaseModel):
    model: str
    api_key: Optional[str] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None


class ScenarioConfig(BaseModel):
    """
    Configuration class for the Scenario library.

    This allows users to set global configuration settings for the library,
    such as the LLM provider and model to use for the testing agent.
    """

    default_model: Optional[Union[str, ModelConfig]] = None
    max_turns: Optional[int] = 10
    verbose: Optional[Union[bool, int]] = True
    cache_key: Optional[str] = None
    debug: Optional[bool] = False

    default_config: ClassVar[Optional["ScenarioConfig"]] = None

    @classmethod
    def configure(
        cls,
        default_model: Optional[str] = None,
        max_turns: Optional[int] = None,
        verbose: Optional[Union[bool, int]] = None,
        cache_key: Optional[str] = None,
        debug: Optional[bool] = None,
    ) -> None:
        existing_config = cls.default_config or ScenarioConfig()

        cls.default_config = existing_config.merge(
            ScenarioConfig(
                default_model=default_model,
                max_turns=max_turns,
                verbose=verbose,
                cache_key=cache_key,
                debug=debug,
            )
        )

    def merge(self, other: "ScenarioConfig") -> "ScenarioConfig":
        return ScenarioConfig(
            **{
                **self.items(),
                **other.items(),
            }
        )

    def items(self):
        return {k: getattr(self, k) for k in self.model_dump(exclude_none=True).keys()}
