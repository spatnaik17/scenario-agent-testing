from contextvars import ContextVar
import inspect
import os
from pathlib import Path
from typing import Callable, TYPE_CHECKING
from joblib import Memory

import json

import wrapt
from scenario.utils import SerializableWithStringFallback

if TYPE_CHECKING:
    from scenario.scenario import Scenario


context_scenario = ContextVar("scenario")

def get_cache() -> Memory:
    """Get a cross-platform cache directory for scenario."""
    home_dir = str(Path.home())
    cache_dir = os.path.join(home_dir, ".scenario", "cache")

    return Memory(location=os.environ.get("SCENARIO_CACHE_DIR", cache_dir), verbose=0)

memory = get_cache()

def scenario_cache(ignore=[]):
    @wrapt.decorator
    def wrapper(wrapped: Callable, instance=None, args=[], kwargs={}):
        scenario: "Scenario" = context_scenario.get()

        if not scenario.cache_key:
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
                "cache_key": scenario.cache_key,
                "scenario": scenario.model_dump(exclude={"agent"}),
                "all_args": all_args,
            },
            cls=SerializableWithStringFallback,
        )

        return _cached_call(wrapped, args, kwargs, cache_key=cache_key)

    return wrapper


@memory.cache(ignore=["func", "args", "kwargs"])
def _cached_call(func: Callable, args, kwargs, cache_key):
    return func(*args, **kwargs)