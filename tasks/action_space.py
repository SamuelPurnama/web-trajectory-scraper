from typing import Literal, Union

from pydantic import Field

from agent.actions import (
    ActionOutput,
    BrowserNav,
    Click,
    Goto,
    KeyboardPress,
    KeyboardType,
    Noop,
    Scroll,
    SendMsgToUser,
)

SYNTHETIC_DATA_BASE_ACTIONS = Union[
    BrowserNav,
    Click,
    Goto,
    KeyboardPress,
    KeyboardType,
    Scroll,
    SendMsgToUser,
    Noop,
]


class SyntheticDataBaseActionOutput(ActionOutput):
    action: SYNTHETIC_DATA_BASE_ACTIONS = Field(description="The action to take.")  # type: ignore
