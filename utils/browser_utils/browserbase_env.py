import os
import re
import time
from datetime import UTC, datetime

import playwright.sync_api
from browserbase import Browserbase
from browsergym.core import OpenEndedTask, _get_global_playwright, register_task
from browsergym.core.action.base import execute_python_code
from browsergym.core.chat import Chat
from browsergym.core.env import (
    BROWSERGYM_ID_ATTRIBUTE,
    BrowserEnv,
    logger,
)


def get_index_from_tab_focus(action):
    # Regular expression to extract the index value
    match = re.search(r"index=(\d+)", action)
    if match:
        index_value = int(match.group(1))
        return index_value  # Output: 1

    return None


class BrowserbaseEnv(BrowserEnv):
    def reset(self, seed=None, *args, **kwargs):
        super().reset(seed=seed, *args, **kwargs)
        self.np_random = None  # make sure all randomness is handled by the task

        if self.task:
            self.task.teardown()
            self.context.close()
            self.chat.close()
            self.browser.close()

        # create a new task
        self.task = self.task_entrypoint(seed=seed, **self.task_kwargs)

        def override_property(task, env, property):
            """Extract property value from env if not None, otherwise from task."""
            env_value = getattr(env, property)
            task_value = getattr(task, property)
            if env_value is None:
                return task_value
            else:
                if task_value is not None:
                    logger.warning(
                        f"Overriding the task's {property} parameter ({repr(task_value)} => {repr(env_value)}). This might change the task's behaviour and difficulty."
                    )
                return env_value

        # fetch task's desired parameters for browser setup
        viewport = override_property(self.task, self, "viewport")
        slow_mo = override_property(self.task, self, "slow_mo")
        timeout = override_property(self.task, self, "timeout")
        locale = override_property(self.task, self, "locale")
        timezone_id = override_property(self.task, self, "timezone_id")

        # use the global Playwright instance
        pw: playwright.sync_api.Playwright = _get_global_playwright()
        # important: change playwright's test id attribute from "data-testid" to "bid"
        pw.selectors.set_test_id_attribute(BROWSERGYM_ID_ATTRIBUTE)

        bb = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])
        self.bb_session = bb.sessions.create(
            project_id=os.environ["BROWSERBASE_PROJECT_ID"],
            proxies=True,
            browser_settings={
                "advanced_stealth": True,
            },
        )
        print(f"BB session id: {self.bb_session.id} | {self.task_kwargs}")

        self.browser = pw.chromium.connect_over_cdp(self.bb_session.connect_url)
        self.context = self.browser.contexts[0]
        # set default timeout
        self.context.set_default_timeout(timeout)

        # hack: keep track of the active page with a javascript callback
        # there is no concept of active page in playwright
        # https://github.com/microsoft/playwright/issues/2603
        self.context.expose_binding(
            "browsergym_page_activated",
            lambda source: self._activate_page_from_js(source["page"]),
        )
        self.context.add_init_script(
            r"""
    window.browsergym_page_activated();
    window.addEventListener("focus", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("focusin", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("load", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("pageshow", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("mousemove", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("mouseup", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("mousedown", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("wheel", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("keyup", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("keydown", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("input", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("touchstart", () => {window.browsergym_page_activated();}, {capture: true});
    window.addEventListener("touchend", () => {window.browsergym_page_activated();}, {capture: true});
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") {
            window.browsergym_page_activated();
        }
    }, {capture: true});
    """
        )

        # create the chat
        self.chat = Chat(
            headless=self.headless,
            chat_size=(500, max(viewport["height"], 800)),
            record_video_dir=self.record_video_dir,
        )

        # create a new page
        self.page = self.context.pages[0]  # new_page()
        recording_start_time = time.time()

        # listen for captcha solving events
        self.captcha_timeout_seconds = 30
        self.cur_captcha_events = []

        def handle_console(msg):
            if msg.text == "browserbase-solving-started":
                print("🔍 CAPTCHA solving started")
                self.cur_captcha_events.append(
                    {
                        "event": "solving-started",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
            elif msg.text == "browserbase-solving-finished":
                print("✅ CAPTCHA solving finished")
                self.cur_captcha_events.append(
                    {
                        "event": "solving-finished",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

        try:
            self.page.on("console", handle_console)
            print("✅ CAPTCHA console listener attached.")
        except Exception as e:
            print(f"❌ Could not attach CAPTCHA listener: {e}")

        # setup the task
        task_goal, task_info = self.task.setup(page=self.page)

        # process the task goal

        # no goal specified
        if task_goal is None:
            self.goal_object = []
        # convert text-only goal (legacy) to new format
        elif isinstance(task_goal, str):
            self.goal_object = [{"type": "text", "text": task_goal}]
        # new format goal with multiple texts and images (OpenAI style)
        elif isinstance(task_goal, list):
            self.goal_object = task_goal
        else:
            raise ValueError(
                f"task_goal should be of type str or list, got {task_goal.__class__}"
            )

        # initialize the chat
        self.chat.add_message(
            role="assistant",
            msg="Hi! I am your UI assistant, I can perform web tasks for you. What can I help you with?",
        )

        # send task goal (if any) to the chat
        for message in self.goal_object:
            match message["type"]:
                case "text":
                    self.chat.add_message(role="user", msg=message["text"])
                case "image_url":
                    image_src = message["image_url"]
                    if isinstance(image_src, dict):
                        image_src = image_src["url"]
                    self.chat.add_message(role="user_image", msg=image_src)
                case _:
                    raise ValueError(
                        f"Unknown message type {repr(message['type'])} in the task goal."
                    )

        self._wait_dom_loaded()

        # after the task's setup, the active page might have changed
        # perform a safety check
        self._active_page_check()

        # init start time
        self.start_time = time.time()

        # no action yet
        self.last_action = ""
        self.last_action_error = ""
        self.infeasible_message_received = False

        # if asked, wait for user message
        self._wait_for_user_message()

        # extract obs and info from environment
        obs = self._get_obs()

        info = {}
        info["task_info"] = task_info

        # TODO this is a bit hacky, find a better solution to record videos
        if self.record_video_dir:
            info["recording_start_time"] = recording_start_time
            info["recording_file"] = str(self.page.video.path())
            info["chat"] = {
                "recording_start_time": self.chat.recording_start_time,
                "recording_file": str(self.chat.page.video.path()),
            }

        return obs, info

    def step(self, action: str) -> tuple:

        self.last_action = action

        info = {}
        info["action_exec_start"] = time.time()
        info["action_exec_timeout"] = 0

        def send_message_to_user(text: str):
            if not isinstance(text, str):
                raise ValueError(f"Forbidden value: {text} is not a string")
            self.chat.add_message(role="assistant", msg=text)

        def report_infeasible_instructions(reason: str):
            if not isinstance(reason, str):
                raise ValueError(f"Forbidden value: {reason} is not a string")
            self.chat.add_message(role="infeasible", msg=reason)
            self.infeasible_message_received = True

        # try to execute the action
        logger.debug(f"Executing action")
        try:
            if self.action_mapping:
                code = self.action_mapping(action)
            else:
                code = action

            if "tab_focus" in action:
                index = get_index_from_tab_focus(action)
                if index is not None:
                    self.page = self.context.pages[index]
                    self.page.bring_to_front()
                    self.page.evaluate(
                        """\
const event = new Event('pageshow', {
    bubbles: true,  // Whether the event bubbles up through the DOM or not
    cancelable: false  // Whether the event can be canceled
});
window.dispatchEvent(event);
"""
                    )
            else:
                execute_python_code(
                    code,
                    self.page,
                    send_message_to_user=send_message_to_user,
                    report_infeasible_instructions=report_infeasible_instructions,
                )
            self.last_action_error = ""

            # Attach CAPTCHA event listener to the updated page
            if "tab_focus" in action or "new_tab" in action:

                def handle_console(msg):
                    if msg.text == "browserbase-solving-started":
                        print("🔍 CAPTCHA solving started")
                        self.cur_captcha_events.append(
                            {
                                "event": "solving-started",
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        )
                    elif msg.text == "browserbase-solving-finished":
                        print("✅ CAPTCHA solving finished")
                        self.cur_captcha_events.append(
                            {
                                "event": "solving-finished",
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        )

                try:
                    self.page.on("console", handle_console)
                    print("✅ CAPTCHA console listener RE-attached.")
                except Exception as e:
                    print(f"❌ Could not RE-attach CAPTCHA listener: {e}")

        except Exception as e:
            self.last_action_error = f"{type(e).__name__}: {e}"
            match = re.match(
                "TimeoutError: Timeout ([0-9]+)ms exceeded.",
                self.last_action_error,
            )
            if match:
                info["action_exec_timeout"] = (
                    float(match.groups()[0]) / 1000
                )  # ms to sec
        logger.debug(f"Action executed")
        info["action_exec_stop"] = time.time()

        # wait a bit (for the JavaScript callback to set the active page)
        time.sleep(0.5)  # wait for JS events to be fired (half a second)
        self.context.cookies()  # trigger all waiting Playwright callbacks on the stack (hack, see https://playwright.dev/java/docs/multithreading)

        # wait for the network to idle before extracting the observation, reward etc.
        self._wait_dom_loaded()

        # after the action is executed, the active page might have changed
        # perform a safety check
        self._active_page_check()
        logger.debug(f"Active page checked")

        # if asked, wait for user message
        self._wait_for_user_message()
        logger.debug(f"User message done")

        logger.debug(f"Initiating task validation")
        # extract reward, done, user_message, info (task-specific)
        reward, done, user_message, task_info = self._task_validate()
        info["task_info"] = task_info
        logger.debug(f"Task validation done")

        # add any user message sent by the task to the chat
        if user_message:
            self.chat.add_message(role="user", msg=user_message)

        # if captcha solving is detected, wait until the solving is complete or max timeout is reached
        if len(self.cur_captcha_events) > 0:
            start_time = time.time()
            while not any(
                event.get("event", "") == "solving-finished"
                for event in self.cur_captcha_events
            ):
                if time.time() - start_time > self.captcha_timeout_seconds:
                    print(
                        f"⏰ Timeout: CAPTCHA was not solved within {self.captcha_timeout_seconds} seconds."
                    )
                    break
                time.sleep(0.5)
        self.cur_captcha_events = []  # reset

        # extract observation (generic)
        obs = self._get_obs()
        logger.debug(f"Observation extracted")

        # new step API wants a 5-tuple (gymnasium)
        terminated = done or (
            self.terminate_on_infeasible and self.infeasible_message_received
        )  # task or agent can terminate the episode
        truncated = False

        return obs, reward, terminated, truncated, info
