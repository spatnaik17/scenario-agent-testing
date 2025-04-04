"""
Example of using custom validation functions with Scenario testing.

This example demonstrates how to implement and use custom validation logic
beyond what the testing agent can automatically evaluate.
"""
import json
import pytest
import re
from typing import Dict, Any, List

from scenario import Scenario, TestingAgent, config


# This is a mock implementation of a website building agent
def website_builder_agent(message, context=None):
    """
    A simple mock website builder agent for demonstration purposes.

    This simulates a website builder agent that can modify website code.
    In a real implementation, this would be your actual agent function.
    """
    # Initialize context if needed
    context = context or {}
    context["history"] = context.get("history", [])
    context["history"].append({"role": "user", "content": message})

    # Track the current state of the website code
    website_code = context.get("website_code", get_initial_website_code())

    # Process the message
    message_lower = message.lower()

    # Handle different requests
    if "hello" in message_lower or "hi" in message_lower:
        response = "Hello! I'm your website building assistant. What would you like to change on your website?"

    elif "change" in message_lower and "menu" in message_lower and "color" in message_lower:
        # Extract the color
        colors = ["red", "blue", "green", "yellow", "black", "white", "purple", "orange"]
        color = next((c for c in colors if c in message_lower), None)

        if color:
            # Update the CSS in the code
            website_code = modify_menu_color(website_code, color)
            context["last_action"] = f"Changed menu color to {color}"
            response = f"I've updated the menu color to {color}. Is there anything else you'd like to change?"
        else:
            response = "What color would you like the menu to be?"

    elif "add" in message_lower and "section" in message_lower:
        # Add a new section to the website
        section_title = "New Section"
        if "about" in message_lower:
            section_title = "About Us"
        elif "contact" in message_lower:
            section_title = "Contact"

        website_code = add_new_section(website_code, section_title)
        context["last_action"] = f"Added new section: {section_title}"
        response = f"I've added a new '{section_title}' section to your website. Would you like to customize it further?"

    elif "change" in message_lower and "font" in message_lower:
        # Change the font
        fonts = ["arial", "verdana", "helvetica", "times", "courier", "georgia"]
        font = next((f for f in fonts if f in message_lower), None)

        if font:
            website_code = change_font(website_code, font)
            context["last_action"] = f"Changed font to {font}"
            response = f"I've updated the font to {font}. How does that look?"
        else:
            response = "What font would you like to use?"

    else:
        response = "I'm not sure what you want to change. I can help with changing colors, fonts, or adding new sections."

    # Update the context
    context["website_code"] = website_code
    context["history"].append({"role": "assistant", "content": response})

    # Return response with artifacts
    return {
        "message": response,
        "website_code": website_code,
        "last_action": context.get("last_action", "No action taken"),
        "is_valid_css": validate_css(website_code),
        "is_valid_html": validate_html(website_code),
    }


# Helper functions for the website builder agent
def get_initial_website_code() -> str:
    """Return the initial website code."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>My Website</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        .menu {
            background-color: #333;
            color: white;
            padding: 15px;
        }
        .menu a {
            color: white;
            text-decoration: none;
            margin-right: 15px;
        }
        .content {
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="menu">
        <a href="#">Home</a>
        <a href="#">Products</a>
        <a href="#">Services</a>
    </div>
    <div class="content">
        <h1>Welcome to My Website</h1>
        <p>This is a sample website.</p>
    </div>
</body>
</html>
"""


def modify_menu_color(code: str, color: str) -> str:
    """Modify the menu background color in the CSS."""
    # Find and replace the menu background-color in CSS
    pattern = r'(\.menu\s*\{[^}]*background-color:)\s*[^;]+;'
    replacement = f'\\1 {color};'
    return re.sub(pattern, replacement, code)


def add_new_section(code: str, title: str) -> str:
    """Add a new section to the HTML."""
    # Find the end of the content div
    content_end = code.rfind('</div>')
    if content_end == -1:
        return code

    # Prepare the new section
    new_section = f"""
    <div class="section">
        <h2>{title}</h2>
        <p>This is the {title} section content.</p>
    </div>
"""

    # Insert the new section before the content div ends
    return code[:content_end] + new_section + code[content_end:]


def change_font(code: str, font: str) -> str:
    """Change the font family in the CSS."""
    # Find and replace the font-family in CSS
    pattern = r'(body\s*\{[^}]*font-family:)\s*[^;]+;'
    replacement = f'\\1 {font}, sans-serif;'
    return re.sub(pattern, replacement, code)


def validate_css(code: str) -> bool:
    """Basic validation for CSS syntax."""
    # Check for balanced braces in CSS
    css_start = code.find('<style>')
    css_end = code.find('</style>')

    if css_start == -1 or css_end == -1:
        return False

    css = code[css_start+7:css_end]
    return css.count('{') == css.count('}')


def validate_html(code: str) -> bool:
    """Basic validation for HTML syntax."""
    # Check for required HTML tags
    required_tags = ['<!DOCTYPE html>', '<html>', '</html>', '<head>', '</head>', '<body>', '</body>']
    return all(tag in code for tag in required_tags)


# Custom validation functions for the scenario tests
def validate_menu_color_change(result, color: str) -> bool:
    """
    Validate that the menu color was changed correctly to the specified color.

    Args:
        result: The test result containing artifacts
        color: The color the menu should have been changed to

    Returns:
        bool: True if the validation passes, False otherwise
    """
    # Get the website code from artifacts
    website_code = result.artifacts.get("website_code", "")

    # Check if the CSS contains the correct color
    css_start = website_code.find('<style>')
    css_end = website_code.find('</style>')

    if css_start == -1 or css_end == -1:
        return False

    css = website_code[css_start:css_end]

    # Look for the menu background-color with the specified color
    menu_color_pattern = r'\.menu\s*\{[^}]*background-color:\s*' + color + '\s*;'
    return bool(re.search(menu_color_pattern, css))


def validate_no_unintended_changes(result, original_code: str) -> bool:
    """
    Validate that no unintended changes were made to the website code.

    Args:
        result: The test result containing artifacts
        original_code: The original website code

    Returns:
        bool: True if only intended changes were made, False otherwise
    """
    # Get the modified code and last action
    modified_code = result.artifacts.get("website_code", "")
    last_action = result.artifacts.get("last_action", "")

    # Determine what should have changed based on the last action
    if "Changed menu color" in last_action:
        color = last_action.split("to ")[-1]
        # Remove whitespace and line breaks for comparison
        orig_cleaned = re.sub(r'\s+', ' ', original_code).strip()
        mod_cleaned = re.sub(r'\s+', ' ', modified_code).strip()

        # Replace the menu color in the original code
        expected_code = modify_menu_color(original_code, color)
        expected_cleaned = re.sub(r'\s+', ' ', expected_code).strip()

        # If the modified code matches the expected code, then no unintended changes
        return mod_cleaned == expected_cleaned

    # For other action types, implement similar logic
    return False


# Configure the testing agent
config(model="openai/gpt-4o-mini")


@pytest.mark.agent_test
def test_website_menu_color_change(scenario_reporter):
    """
    Test scenario for changing the website menu color to blue.

    This tests that the agent can correctly change the menu color without modifying other elements.
    """
    # Store the initial website code for comparison
    initial_code = get_initial_website_code()

    # Define the test scenario
    scenario = Scenario(
        description="User wants to change the website menu color to blue",
        agent=website_builder_agent,  # Specify the agent here

        strategy="""
        Start with a greeting.
        Ask the agent to change the menu color to blue.
        After the agent confirms the change, ask to see the result.
        Do not request any other changes.
        """,

        success_criteria=[
            "Agent changes the menu color to blue",
            "Agent confirms the change was made",
            "The CSS code is valid",
            "No unintended changes were made to other elements"
        ],

        failure_criteria=[
            "Agent fails to change the menu color",
            "Agent changes elements other than the menu color",
            "Agent produces invalid CSS or HTML",
            "Agent misunderstands what element to change"
        ]
    )

    # Run the test directly with the scenario
    result = scenario.run()

    # Add result to the reporter
    scenario_reporter.add_result(scenario, result)

    # Check assertions
    assert result.success, f"Scenario failed: {result.failure_reason}"

    # Perform custom validations
    assert result.artifacts.get("is_valid_css", False), "CSS validation failed"
    assert result.artifacts.get("is_valid_html", False), "HTML validation failed"
    assert validate_menu_color_change(result, "blue"), "Menu color was not changed to blue"
    assert validate_no_unintended_changes(result, initial_code), "Unintended changes were made"