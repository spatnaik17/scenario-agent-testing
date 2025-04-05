import inspect
from typing import Callable, TYPE_CHECKING
from pydantic import BaseModel

import json

from scenario.config import get_cache
import wrapt

if TYPE_CHECKING:
    from scenario.scenario import Scenario


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
