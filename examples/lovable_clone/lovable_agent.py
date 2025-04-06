import os
import shutil
import tempfile
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, UserPromptPart
from pydantic_graph import End
from pydantic_ai.models.openai import OpenAIModel
from openai.types.chat import ChatCompletionMessageParam

from examples.lovable_clone.print_node import print_node
from examples.lovable_clone.directory_tree import generate_directory_tree

template_path = os.path.join(os.path.dirname(__file__), "template")


class LovableAgent:
    def __init__(self):
        agent = Agent(
            "anthropic:claude-3-5-sonnet-latest",
            system_prompt=f"""
        You are a coding assistant specialized in building whole new websites from scratch.

        You will be given a basic React, TypeScript, Vite, Tailwind and Radix UI template and will work on top of that. Use the components from the "@/components/ui" folder.

        On the first user request for building the application, start by the index.css and tailwind.config.ts files to define the colors and general application style.
        Then, start building the website, you can call tools in sequence as much as you want.

        You will be given tools to read file, create file and update file to carry on your work.

        ALWAYS read the file before updating it, and if the file is not present, create it.

        After the user request, you will be given the second part of this system prompt, containing the file present on the project using the <files/> tag.

        You CAN access local files by using the tools provided.
        """,
            model_settings={
                "parallel_tool_calls": False,
                "temperature": 0.0,
                "max_tokens": 8192,
            },
        )

        @agent.tool_plain(
            docstring_format="google", require_parameter_descriptions=True
        )
        def read_file(path: str) -> str:
            """Reads the content of a file.

            Args:
                path (str): The path to the file to read. Required.

            Returns:
                str: The content of the file.
            """
            with open(os.path.join(self.template_path, path), "r") as f:
                return f.read()

        @agent.tool_plain(
            docstring_format="google", require_parameter_descriptions=True
        )
        def update_file(content: str, path: str):
            """Updates the content of a file.

            Args:
                content (str): The full file content to write. Required.
                path (str): The path to the file to update. Required.
            """
            with open(os.path.join(self.template_path, path), "w") as f:
                f.write(content)

            return "ok"

        @agent.tool_plain(
            docstring_format="google", require_parameter_descriptions=True
        )
        def create_file(content: str, path: str):
            """Creates a new file with the given content.

            Args:
                content (str): The full file content to write. Required.
                path (str): The path to the file to create. Required.
            """
            with open(os.path.join(self.template_path, path), "w") as f:
                f.write(content)

            return "ok"

        self.agent = agent
        self.history: list[ModelMessage] = []

    async def process_user_message(
        self, message: str, template_path: str
    ) -> tuple[str, list[ChatCompletionMessageParam]]:
        self.template_path = template_path

        tree = generate_directory_tree(template_path)

        user_prompt = f"""{message}

<files>
{tree}
</files>
"""

        async with self.agent.iter(
            user_prompt, message_history=self.history
        ) as agent_run:
            next_node = agent_run.next_node  # start with the first node
            nodes = [next_node]
            while not isinstance(next_node, End):
                next_node = await agent_run.next(next_node)
                await print_node(agent_run, next_node)
                nodes.append(next_node)

            if not agent_run.result:
                raise Exception("No result from agent")

            new_messages = agent_run.result.new_messages()
            for message_ in new_messages:
                for part in message_.parts:
                    if isinstance(part, UserPromptPart) and part.content == user_prompt:
                        part.content = message

            self.history += new_messages

            new_messages_openai_format = await self.convert_to_openai_format(
                new_messages
            )

            return agent_run.result.data, new_messages_openai_format

    async def convert_to_openai_format(
        self, messages: list[ModelMessage]
    ) -> list[ChatCompletionMessageParam]:
        openai_model = OpenAIModel("any")
        new_messages_openai_format: list[ChatCompletionMessageParam] = []
        for message in messages:
            async for openai_message in openai_model._map_message(message):
                new_messages_openai_format.append(openai_message)

        return new_messages_openai_format

    @classmethod
    def clone_template(cls):
        temp_path = os.path.join(tempfile.mkdtemp(), "lovable_clone")
        shutil.copytree(template_path, temp_path)
        shutil.rmtree(os.path.join(temp_path, "node_modules"), ignore_errors=True)
        return temp_path
