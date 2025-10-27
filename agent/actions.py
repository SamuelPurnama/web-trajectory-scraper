import re
from typing import ClassVar, Literal, Union

from pydantic import BaseModel, Field

NOOP_WAIT_MS = 5000


class Click(BaseModel):
    bid: str = Field(description="The id of the html element to click on.")
    button: Literal["left", "right", "middle"] = Field(
        description="The mouse button to click with."
    )
    click_type: Literal["single", "double"] = Field(
        description="The type of click to perform."
    )

    @property
    def name(self):
        if self.click_type == "single":
            return "click"

        return "dblclick"


class MouseClick(BaseModel):
    x: int = Field(
        ..., description="The x coordinate of the click on the viewport."
    )
    y: int = Field(
        ..., description="The y coordinate of the click on the viewport."
    )
    button: Literal["left", "right", "middle"] = Field(
        default="left", description="The mouse button to click with."
    )
    click_type: Literal["single", "double"] = Field(
        default="single",
        description="The type of click to perform (single vs double click).",
    )

    @property
    def name(self) -> str:
        return (
            "mouse_click" if self.click_type == "single" else "mouse_dblclick"
        )

    def __str__(self) -> str:
        return f'{self.name}(x={self.x}, y={self.y}, button="{self.button}")'


class Scroll(BaseModel):
    name: ClassVar[str] = "scroll"
    delta_x: int = Field(
        description="The number of pixels to scroll by horizontally. Positive to scroll right and negative for left."
    )
    delta_y: int = Field(
        description="The number of pixels to scroll by vertically. Positive to scroll down and negative for up."
    )


class KeyboardType(BaseModel):
    name: ClassVar[str] = "keyboard_type"
    text: str = Field(description="The text to type.")


class KeyboardPress(BaseModel):
    name: ClassVar[str] = "keyboard_press"
    key: Literal[
        "Enter",
        "Escape",
        "Backspace",
        "Tab",
        "ArrowUp",
        "ArrowDown",
        "ArrowLeft",
        "ArrowRight",
    ] = Field(description="The key to press.")


class Copy(BaseModel):
    name: ClassVar[str] = "keyboard_press"
    key: Literal["ControlOrMeta+c"] = Field(
        "ControlOrMeta+c",
        description="The key combination to execute the copy command.",
    )

    def __str__(self) -> str:
        return f'{self.name}(key="{self.key}")'


class Paste(BaseModel):
    name: ClassVar[str] = "keyboard_press"
    key: Literal["ControlOrMeta+v"] = Field(
        "ControlOrMeta+v",
        description="The key combination to execute the paste command.",
    )

    def __str__(self) -> str:
        return f'{self.name}(key="{self.key}")'


class Select(BaseModel):
    name: ClassVar[str] = "select"
    text: str = Field(
        ..., description="The text that has been selected by the user."
    )

    def __str__(self) -> str:
        return f'{self.name}(text="{self.text}")'


class SelectAll(BaseModel):
    name: ClassVar[str] = "keyboard_press"
    key: Literal["ControlOrMeta+a"] = Field(
        "ControlOrMeta+a",
        description="The key combination to execute the selectall command.",
    )

    def __str__(self) -> str:
        return f'{self.name}(key="{self.key}")'


class Goto(BaseModel):
    name: ClassVar[str] = "goto"
    url: str = Field(
        description="The url to navigate to. Eg. https://www.google.com"
    )


class SendMsgToUser(BaseModel):
    name: ClassVar[str] = "send_msg_to_user"
    msg: str = Field(
        description="The message to send to the user. This is generally the final answer or a follow up question to the user-specified goal."
    )


class ReportInfeasible(BaseModel):
    name: ClassVar[str] = "report_infeasible"
    infeasibility_reason: str = Field(
        description="Reason why the task can not be completed or is infeasible."
    )


class BrowserNav(BaseModel):
    name: ClassVar[str] = "browser_nav"
    nav_type: Literal["go_back", "new_tab", "tab_focus"] = Field(
        description="Browser navigation. 'go_back' to navigate back to the previous page in the browser history. 'new_tab' to open a new blank tab in the browser. 'tab_focus' to switch focus to a different tab."
    )
    index: int = Field(
        description="The index of the browser tab to switch focus to. Should be -1 for new_tab and go_back. Should be the page index for tab_focus."
    )


class Noop(BaseModel):
    name: ClassVar[str] = "noop"
    noop_reason: Literal["loading", "captcha"] = Field(
        description="Reason for no-op (i.e no operation). This should be 'loading' to wait while the page is still loading (e.g. if the search results aren't fully displayed yet) or 'captcha' to wait while a captcha is being displayed on the page."
    )


ALL_ACTIONS = Union[
    Click,
    MouseClick,
    Scroll,
    KeyboardType,
    KeyboardPress,
    Copy,
    Paste,
    SelectAll,
    Select,
    Goto,
    BrowserNav,
    SendMsgToUser,
    ReportInfeasible,
    Noop,
]

BID_MOUSE_KEYBOARD_ACTIONS = Union[
    Click,
    Scroll,
    KeyboardType,
    KeyboardPress,
    Goto,
    BrowserNav,
]


class ActionOutput(BaseModel):
    thought: str = Field(
        description="The reasoning behind the suggested action. Be brief but explain why the action is relevant to the goal. Or if you are reporting the task as infeasibility, explain why the task can not be completed."
    )
    action: ALL_ACTIONS = Field(
        description="The action to take. Use 'ReportInfeasible' action if the task can not be completed. Use 'noop' if you are waiting for the page to finish loading or displaying results or if you hit a captcha."
    )

    @property
    def name(self):
        return self.action.name

    @property
    def params(self):
        return self.action.model_dump()

    def to_str(self):
        # match the class name and arguments (excluding the brackets)
        match = re.search(r"(\w+)\((.*)\)", self.action.__repr__())
        if match:
            # if match is found replace the cls_name with the action name
            cls_name, args = match.groups()
            if isinstance(self.action, Click):
                return f"{self.name}(bid={self.action.bid!r}, button={self.action.button!r})"
            elif isinstance(self.action, SendMsgToUser):
                return f"{self.name}(text={self.action.msg!r})"
            elif isinstance(self.action, BrowserNav):
                if self.action.nav_type in ["go_back", "new_tab"]:
                    return f"{self.action.nav_type}()"
                elif self.action.nav_type == "tab_focus":
                    return f"{self.action.nav_type}(index={self.action.index})"
                else:
                    return self.action.__repr__()
            elif isinstance(self.action, ReportInfeasible):
                return (
                    f"{self.name}(reason={self.action.infeasibility_reason!r})"
                )
            elif isinstance(self.action, Noop):
                return f"{self.name}(wait_ms={NOOP_WAIT_MS})"
            return f"{self.name}({args})"

        return self.action.__repr__()


def node2str(node):
    role = node["role"]["value"]
    name = node["name"]["value"]
    if name == "":
        return role
    return f"{role} with value '{name}'"


def get_node_from_bid(bid, axtree):
    node_list = [
        node
        for node in axtree["nodes"]
        if "browsergym_id" in node and node["browsergym_id"] == bid
    ]
    if len(node_list) == 0:
        return None
    return node_list[0]


def get_node_properties(bid, axtree):
    node = get_node_from_bid(bid, axtree)
    if node is None:
        return None
    else:
        return dict(role=node["role"]["value"], value=node["name"]["value"])


def describe_action(action: ALL_ACTIONS, axtree, extra_element_properties=None):
    if isinstance(action, Click):
        node = get_node_from_bid(action.bid, axtree)
        if node is None:
            bid_str = f"element with bid={action.bid}"
        else:
            bid_str = node2str(node)
        is_clickable = (
            extra_element_properties[action.bid]["clickable"]
            if extra_element_properties is not None
            and action.bid in extra_element_properties
            else False
        )
        clickable_suffix = (
            "element is clickable"
            if is_clickable
            else "element is not clickable"
        )
        return (
            f"{action.button} {action.name} on {bid_str} ({clickable_suffix})"
        )
    elif isinstance(action, Scroll):
        if action.delta_x == 0:
            direction = "down" if action.delta_y > 0 else "up"
            return f"scroll {direction} by {action.delta_y} pixels"
        elif action.delta_y == 0:
            direction = "right" if action.delta_x > 0 else "left"
            return f"scroll {direction} by {action.delta_x} pixels"
        else:
            hdirection = "right" if action.delta_x > 0 else "left"
            vdirection = "down" if action.delta_y > 0 else "up"
            return f"scroll {hdirection} by {action.delta_x} pixels and {vdirection} by {action.delta_y} pixels"
    elif isinstance(action, KeyboardType):
        return f"type '{action.text}'"
    elif isinstance(action, KeyboardPress):
        return f"press {action.key} key"
    elif isinstance(action, Goto):
        return f"go to {action.url}"
    elif isinstance(action, SendMsgToUser):
        return f"send message to user: '{action.msg}'"
    elif isinstance(action, BrowserNav) and action.nav_type == "new_tab":
        return "open a new blank tab"
    elif isinstance(action, BrowserNav) and action.nav_type == "go_back":
        return "go back to the previous web page on the same browser tab"
    elif isinstance(action, BrowserNav) and action.nav_type == "tab_focus":
        return f"switch to tab {action.index}"
    elif isinstance(action, ReportInfeasible):
        return "task infeasible"
    elif isinstance(action, Noop):
        if action.noop_reason == "loading":
            return "wait for the page to finish loading"
        elif action.noop_reason == "captcha":
            return "wait for captcha to be solved"
        else:
            return f"noop(noop_reason={action.noop_reason})"
    else:
        return action.__repr__()
