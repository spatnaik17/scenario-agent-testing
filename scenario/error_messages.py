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


def message_return_error_message(got: Any, class_name: str):
    got_ = got.__repr__()
    if len(got_) > 100:
        got_ = got_[:100] + "..."

    return f"""
 {termcolor.colored("->", "cyan")} On the {termcolor.colored("call", "green")} method of the {class_name} agent adapter, you returned:

{indent(got_, ' ' * 4)}

 {termcolor.colored("->", "cyan")} But the adapter should return either a string, a dict on the OpenAI messages format, or a list of messages in the OpenAI messages format so the testing agent can understand what happened. For example:

    class MyAgentAdapter(OpenAIMessagesAgentAdapter):
        async def call(self, input: AgentInput) -> AgentReturnTypes:
            response = call_my_agent(message)

            return response.output_text
            {termcolor.colored("^" * 27, "green")}

 {termcolor.colored("->", "cyan")} Alternatively, you can return a list of messages in OpenAI messages format, this is useful for capturing tool calls and other before the final response:

    class MyAgentAdapter(OpenAIMessagesAgentAdapter):
        async def call(self, input: AgentInput) -> AgentReturnTypes:
            response = call_my_agent(message)

            return [
                {{"role": "assistant", "content": response.output_text}},
                {termcolor.colored("^" * 55, "green")}
            ]
"""
