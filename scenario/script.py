from typing import Awaitable, Callable, Optional, Union, TYPE_CHECKING

from .types import ScriptStep

from openai.types.chat import ChatCompletionMessageParam

if TYPE_CHECKING:
    from scenario.scenario_state import ScenarioState


def message(message: ChatCompletionMessageParam) -> ScriptStep:
    return lambda state: state._executor.message(message)


def user(
    content: Optional[Union[str, ChatCompletionMessageParam]] = None,
) -> ScriptStep:
    return lambda state: state._executor.user(content)


def agent(
    content: Optional[Union[str, ChatCompletionMessageParam]] = None,
) -> ScriptStep:
    return lambda state: state._executor.agent(content)


def judge(
    content: Optional[Union[str, ChatCompletionMessageParam]] = None,
) -> ScriptStep:
    return lambda state: state._executor.judge(content)


def proceed(
    turns: Optional[int] = None,
    on_turn: Optional[
        Union[
            Callable[["ScenarioState"], None],
            Callable[["ScenarioState"], Awaitable[None]],
        ]
    ] = None,
    on_step: Optional[
        Union[
            Callable[["ScenarioState"], None],
            Callable[["ScenarioState"], Awaitable[None]],
        ]
    ] = None,
) -> ScriptStep:
    return lambda state: state._executor.proceed(turns, on_turn, on_step)


def succeed(reasoning: Optional[str] = None) -> ScriptStep:
    return lambda state: state._executor.succeed(reasoning)


def fail(reasoning: Optional[str] = None) -> ScriptStep:
    return lambda state: state._executor.fail(reasoning)
