"""
Sample configuration for the Scenario testing library.

This file demonstrates how to configure the Scenario testing library
with different options for different use cases.
"""
import os
from scenario import config


def basic_configuration():
    """Basic configuration example."""
    # Configure with default OpenAI model
    config(
        model="openai/gpt-4o-mini",
        temperature=0.1,
        max_tokens=1000,
    )

    print("Basic configuration set up with OpenAI model")


def advanced_configuration():
    """Advanced configuration with LiteLLM and custom settings."""
    # Configure with a different model provider and custom settings
    config(
        model="anthropic/claude-3-haiku-20240307",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        temperature=0,  # Zero temperature for maximum determinism
        max_tokens=2000,
        timeout=120,    # Longer timeout for complex scenarios
        verbose=True,   # Enable verbose mode for debugging
    )

    print("Advanced configuration set up with Anthropic model")


def azure_openai_configuration():
    """Configuration for Azure OpenAI."""
    # Configure for Azure OpenAI
    config(
        model="azure/gpt-4",
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        api_base=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        api_version="2023-05-15",
    )

    print("Azure OpenAI configuration set up")


if __name__ == "__main__":
    """Show configuration examples."""
    print("Scenario Configuration Examples")
    print("==============================")

    # Show current configuration
    print("\nCurrent configuration:")
    current_config = config.to_dict()
    for key, value in current_config.items():
        # Don't print API keys
        if key == "api_key" and value:
            print(f"  {key}: ****")
        else:
            print(f"  {key}: {value}")

    # Example configurations
    print("\nExample configurations:")
    print("\n1. Basic Configuration")
    basic_configuration()

    print("\n2. Advanced Configuration with Anthropic")
    advanced_configuration()

    print("\n3. Azure OpenAI Configuration")
    azure_openai_configuration()

    print("\nConfiguration complete!")