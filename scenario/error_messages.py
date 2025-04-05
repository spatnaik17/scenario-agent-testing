import termcolor


default_config_error_message = f"""

 {termcolor.colored("->", "cyan")} Please set a default config for running your scenarios at the top of your test file, for example:

    from scenario import Scenario

    Scenario.configure(testing_agent_model="openai/gpt-4o-mini")
    {termcolor.colored("^" * 46, "green")}

    @pytest.mark.agent_test
    def test_vegetarian_recipe_agent():
        scenario = Scenario(
            # ...
        )
        result = scenario.run()

        assert result.success

 {termcolor.colored("->", "cyan")} Alternatively, you can set the config specifically for this scenario:

    from scenario import Scenario, ScenarioConfig

    @pytest.mark.agent_test
    def test_vegetarian_recipe_agent():
        scenario = Scenario(
            # ...
            config=ScenarioConfig(testing_agent_model="openai/gpt-4o-mini")
            {termcolor.colored("^" * 49, "green")}
        )
        result = scenario.run()

        assert result.success
                          """


message_return_error_message = f"""

 {termcolor.colored("->", "cyan")} Your agent should return a dict with either a "message" string key or a "messages" key in OpenAI messages format so the testing agent can understand what happened. For example:

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
