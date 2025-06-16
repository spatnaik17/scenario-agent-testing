from typing import Awaitable, Callable, Optional, Union, TYPE_CHECKING

from .types import ScriptStep

from openai.types.chat import ChatCompletionMessageParam

if TYPE_CHECKING:
    from scenario.scenario_executor import ScenarioExecutor


def message(message: ChatCompletionMessageParam) -> ScriptStep:
    return lambda state: state.message(message)


def user(
    content: Optional[Union[str, ChatCompletionMessageParam]] = None,
) -> ScriptStep:
    return lambda state: state.user(content)


def agent(
    content: Optional[Union[str, ChatCompletionMessageParam]] = None,
) -> ScriptStep:
    return lambda state: state.agent(content)


def judge(
    content: Optional[Union[str, ChatCompletionMessageParam]] = None,
) -> ScriptStep:
    return lambda state: state.judge(content)


def proceed(
    turns: Optional[int] = None,
    on_turn: Optional[
        Union[
            Callable[["ScenarioExecutor"], None],
            Callable[["ScenarioExecutor"], Awaitable[None]],
        ]
    ] = None,
    on_step: Optional[
        Union[
            Callable[["ScenarioExecutor"], None],
            Callable[["ScenarioExecutor"], Awaitable[None]],
        ]
    ] = None,
) -> ScriptStep:
    return lambda state: state.proceed(turns, on_turn, on_step)


def succeed(reasoning: Optional[str] = None) -> ScriptStep:
    return lambda state: state.succeed(reasoning)


def fail(reasoning: Optional[str] = None) -> ScriptStep:
    return lambda state: state.fail(reasoning)
