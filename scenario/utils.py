import inspect
from typing import Callable, TYPE_CHECKING
from pydantic import BaseModel

import json

from scenario.config import get_cache
import wrapt
import termcolor
from textwrap import indent
from openai.types.chat import ChatCompletionMessageParam

if TYPE_CHECKING:
    from scenario.scenario import Scenario


memory = get_cache()


def scenario_cache(ignore=[]):
    @wrapt.decorator
    def wrapper(wrapped: Callable, instance=None, args=[], kwargs={}):
        from scenario.scenario_executor import context_scenario

        scenario: "Scenario" = context_scenario.get()

        if not scenario.config.cache_key:
            return wrapped(*args, **kwargs)

        sig = inspect.signature(wrapped)
        parameters = list(sig.parameters.values())

        all_args = {
            str(parameter.name): value for parameter, value in zip(parameters, args)
        }
        for arg in ["self"] + ignore:
            if arg in all_args:
                del all_args[arg]

        cache_key = json.dumps(
            {
                "cache_key": scenario.config.cache_key,
                "scenario": scenario.to_dict(),
                "all_args": all_args,
            },
            cls=SerializableWithStringFallback,
        )

        return _cached_call(wrapped, args, kwargs, cache_key=cache_key)

    return wrapper


@memory.cache(ignore=["func", "args", "kwargs"])
def _cached_call(func: Callable, args, kwargs, cache_key):
    return func(*args, **kwargs)


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


def print_openai_messages(messages: list[ChatCompletionMessageParam]):
    for msg in messages:
        role = safe_attr_or_key(msg, "role")
        content = safe_attr_or_key(msg, "content")
        if role == "assistant":
            tool_calls = safe_attr_or_key(msg, "tool_calls")
            if content:
                print(termcolor.colored("Agent:", "blue"), content)
            if tool_calls:
                for tool_call in tool_calls:
                    function = safe_attr_or_key(tool_call, "function")
                    name = safe_attr_or_key(function, "name")
                    args = safe_attr_or_key(function, "arguments", "{}")
                    args = _take_maybe_json_first_lines(args)
                    print(
                        termcolor.colored(f"ToolCall({name}):", "magenta"),
                        f"\n\n{indent(args, ' ' * 4)}\n",
                    )
        elif role == "tool":
            content = _take_maybe_json_first_lines(content or msg.__repr__())
            print(
                termcolor.colored(f"ToolResult:", "magenta"),
                f"\n\n{indent(content, ' ' * 4)}\n",
            )
        else:
            print(
                termcolor.colored(f"{title_case(role)}:", "magenta"),
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
