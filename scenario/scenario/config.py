"""
Configuration module for Scenario.
"""
from typing import Dict, Any, Optional


class ScenarioConfig:
    """
    Configuration class for the Scenario library.

    This allows users to set global configuration settings for the library,
    such as the LLM provider and model to use for the testing agent.
    """

    _instance = None

    def __new__(cls):
        """Ensure singleton pattern for configuration."""
        if cls._instance is None:
            cls._instance = super(ScenarioConfig, cls).__new__(cls)
            cls._instance._init_defaults()
        return cls._instance

    def _init_defaults(self) -> None:
        """Initialize default configuration values."""
        self._config = {
            "model": "gpt-3.5-turbo",         # Default model
            "llm_provider": "openai",         # Default provider
            "api_key": None,                  # API key (defaults to env var)
            "temperature": 0.1,               # Low temperature for consistency
            "max_tokens": 1000,               # Default token limit
            "verbose": False,                 # Verbose output mode
            "timeout": 60,                    # Timeout in seconds
        }

    def __call__(self, **kwargs) -> "ScenarioConfig":
        """Allow calling the config instance to update settings."""
        for key, value in kwargs.items():
            if key not in self._config:
                raise ValueError(f"Unknown configuration key: {key}")
            self._config[key] = value
        return self

    def get(self, key: str) -> Any:
        """Get a configuration value."""
        if key not in self._config:
            raise ValueError(f"Unknown configuration key: {key}")
        return self._config[key]

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        if key not in self._config:
            raise ValueError(f"Unknown configuration key: {key}")
        self._config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Get a copy of the configuration dictionary."""
        return self._config.copy()


# Create singleton instance
config = ScenarioConfig()