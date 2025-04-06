from contextlib import contextmanager
import sys
from typing import Optional, Union
from pydantic import BaseModel

import json

import termcolor
from textwrap import indent
from openai.types.chat import ChatCompletionMessageParam
from rich.live import Live
from rich.spinner import Spinner
from rich.console import Console
from rich.text import Text
from rich.errors import LiveError



class SerializableAndPydanticEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, BaseModel):
            return o.model_dump(exclude_unset=True)
        return super().default(o)


class SerializableWithStringFallback(SerializableAndPydanticEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except:
            return str(o)


def safe_list_at(list, index, default=None):
    try:
        return list[index]
    except:
        return default


def safe_attr_or_key(obj, attr_or_key, default=None):
    return getattr(obj, attr_or_key, obj.get(attr_or_key))


def title_case(string):
    return " ".join(word.capitalize() for word in string.split("_"))


def print_openai_messages(scenario_name: str, messages: list[ChatCompletionMessageParam]):
    for msg in messages:
        role = safe_attr_or_key(msg, "role")
        content = safe_attr_or_key(msg, "content")
        if role == "assistant":
            tool_calls = safe_attr_or_key(msg, "tool_calls")
            if content:
                print(scenario_name + termcolor.colored("Agent:", "blue"), content)
            if tool_calls:
                for tool_call in tool_calls:
                    function = safe_attr_or_key(tool_call, "function")
                    name = safe_attr_or_key(function, "name")
                    args = safe_attr_or_key(function, "arguments", "{}")
                    args = _take_maybe_json_first_lines(args)
                    print(
                        scenario_name + termcolor.colored(f"ToolCall({name}):", "magenta"),
                        f"\n\n{indent(args, ' ' * 4)}\n",
                    )
        elif role == "tool":
            content = _take_maybe_json_first_lines(content or msg.__repr__())
            print(
                scenario_name + termcolor.colored(f"ToolResult:", "magenta"),
                f"\n\n{indent(content, ' ' * 4)}\n",
            )
        else:
            print(
                scenario_name + termcolor.colored(f"{title_case(role)}:", "magenta"),
                msg.__repr__(),
            )


def _take_maybe_json_first_lines(string, max_lines=5):
    content = str(string)
    try:
        content = json.dumps(json.loads(content), indent=2)
    except:
        pass
    content = content.split("\n")
    if len(content) > max_lines:
        content = content[:max_lines] + ["..."]
    return "\n".join(content)


console = Console()

class TextFirstSpinner(Spinner):
    def __init__(self, name, text: str, color: str, **kwargs):
        super().__init__(name, "", style="bold white", **kwargs)  # Initialize with empty text
        self.text_before = text
        self.color = color

    def render(self, time):
        # Get the original spinner frame
        spinner_frame = super().render(time)
        # Create a composite with text first, then spinner
        return Text(f"{self.text_before} ", style=self.color) + spinner_frame


@contextmanager
def show_spinner(text: str, color: str = "white", enabled: Optional[Union[bool, int]] = None):
    if not enabled:
        yield
    else:
        spinner = TextFirstSpinner("dots", text, color=color)
        try:
            with Live(spinner, console=console, refresh_per_second=20):
                yield
        # It happens when we are multi-threading, it's fine, just ignore it, you probably don't want multiple spinners at once anyway
        except LiveError:
            yield

        # Cursor up one line
        sys.stdout.write("\033[F")
