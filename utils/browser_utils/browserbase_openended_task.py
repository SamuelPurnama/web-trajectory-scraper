from functools import partial
from typing import Type

import gymnasium as gym
from browsergym.core import OpenEndedTask
from browsergym.core.registration import AbstractBrowserTask, frozen_partial

from utils.browser_utils.browserbase_env import BrowserbaseEnv


def register_browserbase_task(
    id: str,
    task_class: Type[AbstractBrowserTask],
    task_kwargs: dict = {},
    default_task_kwargs: dict = {},
    nondeterministic: bool = True,
    *args,
    **kwargs,
):
    """
    Registers a browser task as a gym environment with its unique id.

    Args:
        id: the id of the task to register (will be prepended by "browsergym/").
        task_class: the task class to register.
        task_kwargs: frozen task arguments (can not be overloaded at environment creation time).
        task_kwargs_default: default task arguments (can be overloaded at environment creation time).
        nondeterministic: whether the task cannot be guaranteed deterministic transitions.
        *args: additional sequential arguments for either the gym or the browsergym environment.
        *kwargs: additional keyword arguments for either the gym or the browsergym environment.
    """
    if task_kwargs and default_task_kwargs:
        # check overlap between frozen and default task_kwargs
        clashing_kwargs = set(task_kwargs) & set(
            default_task_kwargs
        )  # key set intersection
        if clashing_kwargs:
            raise ValueError(
                f"Illegal attempt to register Browsergym environment {id} with both frozen and default values for task parameters {clashing_kwargs}."
            )

    task_entrypoint = task_class

    # freeze task_kwargs (cannot be overriden at environment creation)
    task_entrypoint = frozen_partial(task_class, **task_kwargs)

    # pre-set default_task_kwargs (can be overriden at environment creation)
    task_entrypoint = partial(task_entrypoint, **default_task_kwargs)

    gym.register(
        id=f"browsergym/{id}",
        entry_point=lambda *env_args, **env_kwargs: BrowserbaseEnv(
            task_entrypoint, *env_args, **env_kwargs
        ),
        nondeterministic=nondeterministic,
        *args,
        **kwargs,
    )


register_browserbase_task("browserbase_openended", OpenEndedTask)
