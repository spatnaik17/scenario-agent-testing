from textwrap import indent
from typing import Any
import termcolor


default_config_error_message = f"""

 {termcolor.colored("->", "cyan")} Please set a default config with at least a testing_agent model for running your scenarios at the top of your test file, for example:

    from scenario import Scenario, TestingAgent

    Scenario.configure(testing_agent=TestingAgent(model="openai/gpt-4o-mini"))
    {termcolor.colored("^" * 74, "green")}

    @pytest.mark.agent_test
    def test_vegetarian_recipe_agent():
        scenario = Scenario(
            # ...
        )
        result = scenario.run()

        assert result.success


 {termcolor.colored("->", "cyan")} Alternatively, you can set the config specifically for this scenario:

    from scenario import Scenario, TestingAgent

    @pytest.mark.agent_test
    def test_vegetarian_recipe_agent():
        scenario = Scenario(
            # ...
            testing_agent=TestingAgent(model="openai/gpt-4o-mini")
            {termcolor.colored("^" * 54, "green")}
        )
        result = scenario.run()

        assert result.success
                          """


def message_return_error_message(got: Any):
    got_ = got.__repr__()
    if len(got_) > 100:
        got_ = got_[:100] + "..."

    return f"""
 {termcolor.colored("->", "cyan")} Your agent returned:

{indent(got_, ' ' * 4)}

 {termcolor.colored("->", "cyan")} But your agent should return a dict with either a "message" string key or a "messages" key in OpenAI messages format so the testing agent can understand what happened. For example:

    def my_agent_under_test(message, context):
        response = call_my_agent(message)

        return {{
            "message": response.output_text
            {termcolor.colored("^" * 31, "green")}
        }}

 {termcolor.colored("->", "cyan")} Alternatively, you can return a list of messages in OpenAI messages format, you can also optionally provide extra artifacts:

    def my_agent_under_test(message, context):
        response = call_my_agent(message)

        return {{
            "messages": [
                {{"role": "assistant", "content": response}}
                {termcolor.colored("^" * 42, "green")}
            ],
            "extra": {{
                # ... optional extra artifacts
            }}
        }}
                          """
