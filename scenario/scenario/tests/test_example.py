"""
Example tests using the Scenario testing library.
"""
import pytest
from scenario import Scenario, TestingAgent, config


# Mock implementation of a simple travel booking agent
def travel_agent(message, context=None):
    """
    A simple mock travel booking agent for demonstration purposes.

    This simulates a travel booking agent that can handle hotel bookings.
    In a real implementation, this would be your actual agent function.
    """
    # Simple context tracking
    context = context or {}
    context["history"] = context.get("history", [])
    context["history"].append({"role": "user", "content": message})

    # Track booking state
    booking_state = context.get("booking", {})

    # Simple pattern matching for demonstration
    message_lower = message.lower()

    # Initial greeting
    if "hello" in message_lower or "hi " in message_lower:
        response = "Hello! I'm your travel assistant. I can help you book hotels. Where would you like to stay?"

    # Capture location
    elif "in paris" in message_lower or "paris" in message_lower:
        booking_state["location"] = "Paris"
        response = "Great choice! Paris is beautiful. When would you like to check in, and for how many nights?"

    # Capture dates
    elif "check in" in message_lower or "stay" in message_lower or "night" in message_lower:
        if "tomorrow" in message_lower:
            booking_state["check_in"] = "tomorrow"

        if "for" in message_lower and "night" in message_lower:
            try:
                nights = int(message_lower.split("for")[1].split("night")[0].strip())
                booking_state["nights"] = nights
            except:
                booking_state["nights"] = 1

        if "booking_state" in context:
            response = "Perfect. How many guests will be staying?"
        else:
            response = "I'll need to know your destination first. Where would you like to stay?"

    # Capture guests
    elif "guest" in message_lower or "people" in message_lower or "person" in message_lower:
        if "1" in message or "one" in message_lower:
            booking_state["guests"] = 1
        elif "2" in message or "two" in message_lower:
            booking_state["guests"] = 2
        else:
            booking_state["guests"] = int(message.split()[0])

        response = "Great! Would you like me to find you a hotel with breakfast included?"

    # Capture preferences
    elif "breakfast" in message_lower:
        if "yes" in message_lower or "yeah" in message_lower:
            booking_state["breakfast"] = True
            response = "Perfect! I'll find options with breakfast. Would you like to confirm your booking now?"
        else:
            booking_state["breakfast"] = False
            response = "No problem. Would you like to confirm your booking now?"

    # Confirmation
    elif "confirm" in message_lower or "book" in message_lower or "yes" in message_lower:
        # Check if we have enough information
        required_fields = ["location", "check_in", "nights", "guests"]
        missing_fields = [field for field in required_fields if field not in booking_state]

        if missing_fields:
            response = f"I still need some information to complete your booking: {', '.join(missing_fields)}"
        else:
            booking_state["confirmed"] = True
            booking_state["confirmation_number"] = "BK12345"
            response = (
                f"Great! I've confirmed your booking in {booking_state['location']} "
                f"for {booking_state['nights']} nights starting {booking_state['check_in']} "
                f"for {booking_state['guests']} guests. "
                f"Your confirmation number is {booking_state['confirmation_number']}. "
                f"Would you like me to arrange an airport transfer as well?"
            )

    # Additional services
    elif "transfer" in message_lower or "airport" in message_lower:
        if "yes" in message_lower:
            booking_state["airport_transfer"] = True
            response = "Perfect! I've added an airport transfer to your booking. Is there anything else you need?"
        else:
            response = "No problem. Your hotel booking is all set. Is there anything else you need?"

    # Default fallback
    else:
        response = "I'm not sure I understood. I can help you book a hotel. Where would you like to stay?"

    # Update context
    context["booking"] = booking_state
    context["history"].append({"role": "assistant", "content": response})

    # Return the response and the context as artifacts
    return {
        "message": response,
        "booking_state": booking_state,
        "conversation_length": len(context["history"]) // 2
    }


# Configure the testing agent
config(model="gpt-3.5-turbo")


@pytest.mark.agent_test
def test_hotel_booking_scenario(scenario_reporter):
    """
    Test scenario for booking a hotel in Paris.

    This tests the happy path of a user booking a hotel in Paris.
    """
    # Define the test scenario
    scenario = Scenario(
        description="User wants to book a hotel in Paris for 2 nights",
        agent=travel_agent,  # Specify the agent here

        strategy="""
        Begin with a greeting.
        When asked, say you want to book a hotel in Paris.
        When asked about dates, say you want to check in tomorrow for 2 nights.
        When asked about guests, say 2 people.
        When asked about breakfast, say yes.
        Confirm the booking when asked.
        Decline airport transfer when offered.
        """,

        success_criteria=[
            "Agent confirms the booking with a confirmation number",
            "Agent correctly captures Paris as the location",
            "Agent correctly captures 2 nights for the stay duration",
            "Agent correctly captures 2 guests",
        ],

        failure_criteria=[
            "Agent fails to provide a confirmation number",
            "Agent books wrong location (not Paris)",
            "Agent books wrong number of nights (not 2)",
            "Agent books wrong number of guests (not 2)",
            "More than 10 interaction turns without completing booking",
        ]
    )

    # Run the test directly with the scenario
    result = scenario.run()

    # Add result to the reporter
    scenario_reporter.add_result(scenario, result)

    # Check assertions
    assert result.success, f"Scenario failed: {result.failure_reason}"

    # Verify specific booking details using extracted artifacts
    booking_state = result.artifacts.get("booking_state", {})
    assert booking_state.get("location") == "Paris", "Wrong location booked"
    assert booking_state.get("nights") == 2, "Wrong number of nights booked"
    assert booking_state.get("guests") == 2, "Wrong number of guests booked"
    assert booking_state.get("confirmed") is True, "Booking was not confirmed"
    assert "confirmation_number" in booking_state, "No confirmation number provided"


@pytest.mark.agent_test
def test_hotel_booking_failure_scenario(scenario_reporter):
    """
    Test scenario for failing to book a hotel due to missing information.

    This tests a negative path where the user doesn't provide all required information.
    """
    # Define the test scenario
    scenario = Scenario(
        description="User provides incomplete information for hotel booking",
        agent=travel_agent,  # Specify the agent here

        strategy="""
        Begin with a greeting.
        When asked, say you want to book a hotel in Paris.
        When asked about dates, ignore the question and ask about breakfast.
        If the agent persists, continue asking off-topic questions.
        See if the agent will confirm a booking without all the required information.
        """,

        success_criteria=[
            "Agent refuses to confirm booking without all required information",
            "Agent persists in asking for missing information",
            "Agent correctly identifies what information is missing",
        ],

        failure_criteria=[
            "Agent confirms a booking without having all required information",
            "Agent becomes confused and cannot continue the conversation coherently",
            "Agent gives up trying to collect required information",
        ]
    )

    # Run the test directly with the scenario
    result = scenario.run()

    # Add result to the reporter
    scenario_reporter.add_result(scenario, result)

    # This scenario should succeed (agent should correctly refuse incomplete booking)
    assert result.success, f"Scenario failed: {result.failure_reason}"


@pytest.mark.agent_test
def test_hotel_booking_with_custom_testing_agent(scenario_reporter):
    """
    Test scenario for booking a hotel using a custom testing agent.

    This demonstrates how to use a custom testing agent with different configuration.
    """
    # Create a custom testing agent with different settings
    custom_testing_agent = TestingAgent({
        "model": "gpt-4",  # Use a more powerful model for testing
        "temperature": 0.0,  # Deterministic responses
        "max_tokens": 2000,  # Allow longer responses
    })

    # Define the test scenario with the custom testing agent
    scenario = Scenario(
        description="User wants to book a hotel in Paris with specific requirements",
        agent=travel_agent,
        testing_agent=custom_testing_agent,  # Use the custom testing agent

        strategy="""
        Begin with a greeting.
        When asked, say you want to book a hotel in Paris.
        When asked about dates, say you want to check in tomorrow for 3 nights.
        When asked about guests, say 2 people.
        Specify that you need breakfast included.
        Confirm the booking when asked.
        Request an airport transfer as well.
        """,

        success_criteria=[
            "Agent confirms the booking with a confirmation number",
            "Agent correctly captures Paris as the location",
            "Agent correctly captures 3 nights for the stay duration",
            "Agent correctly captures 2 guests",
            "Agent includes breakfast in the booking",
            "Agent arranges airport transfer when requested",
        ],

        failure_criteria=[
            "Agent fails to provide a confirmation number",
            "Agent books wrong location (not Paris)",
            "Agent does not include breakfast in the booking",
            "Agent fails to arrange airport transfer when requested",
        ]
    )

    # Run the test directly with the scenario
    result = scenario.run()

    # Add result to the reporter
    scenario_reporter.add_result(scenario, result)

    # Check assertions
    assert result.success, f"Scenario failed: {result.failure_reason}"