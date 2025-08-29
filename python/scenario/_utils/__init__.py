"""
Utility functions for scenario execution and message handling.

This module provides various utility functions used throughout the Scenario framework,
including message formatting, validation, role reversal, and UI components like spinners
for better user experience during scenario execution.
"""

from .message_conversion import convert_agent_return_types_to_openai_messages
from .ids import (
    get_batch_run_id,
    get_or_create_batch_run_id,  # Backward compatibility
    generate_scenario_run_id,
    generate_scenario_id,
    generate_thread_id,
    generate_message_id,
    safe_parse_ksuid,
)
from .utils import (
    SerializableAndPydanticEncoder,
    SerializableWithStringFallback,
    print_openai_messages,
    show_spinner,
    check_valid_return_type,
    reverse_roles,
    await_if_awaitable,
)

__all__ = [
    "convert_agent_return_types_to_openai_messages",
    "get_batch_run_id",
    "get_or_create_batch_run_id",  # Backward compatibility
    "generate_scenario_run_id",
    "generate_scenario_id",
    "generate_thread_id",
    "generate_message_id",
    "safe_parse_ksuid",
    "SerializableAndPydanticEncoder",
    "SerializableWithStringFallback",
    "print_openai_messages",
    "show_spinner",
    "check_valid_return_type",
    "reverse_roles",
    "await_if_awaitable",
]
