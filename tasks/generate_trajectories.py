import hashlib
import json
import os
import random
import warnings
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from concurrent.futures import as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

import fasthtml.common as ft
import fire
import gymnasium as gym
import pandas as pd
from beartype.roar import BeartypeDecorHintPep585DeprecationWarning
from browsergym.core.action.functions import (
    dblclick,
    go_back,
    goto,
    keyboard_press,
    keyboard_type,
    mouse_click,
    mouse_dblclick,
    new_tab,
    noop,
    scroll,
    send_msg_to_user,
    tab_focus,
)
from browsergym.core.action.functions import demo_mode, page, retry_with_force
from browsergym.core.action.highlevel import HighLevelActionSet
from browsergym.core.action.utils import add_demo_mode_effects, call_fun, get_elem_by_bid
from PIL import Image

import utils.browser_utils.browserbase_openended_task
from agent.actions import get_node_properties
from agent.axtree_agent import AxtreeAgent, get_axtree_str
from tasks.action_space import SyntheticDataBaseActionOutput
from tasks.proxy_utils import sample_browser_context
from tasks.system_message import SYSTEM_MESSAGE
from utils.eval_utils.episode import Episode, Interaction
from utils.eval_utils.episode_logger import LocalEpisodeLogger
from utils.vis_utils.html import create_page, create_table, save_html

warnings.filterwarnings(
    "ignore", category=BeartypeDecorHintPep585DeprecationWarning
)


def click(
    bid: str,
    button: Literal["left", "middle", "right"] = "left",
    modifiers: list[Literal["Alt", "Control", "ControlOrMeta", "Meta", "Shift"]] = [],
):
    """
    Click an element.

    Examples:
        click('a51')
        click('b22', button="right")
        click('48', button="middle", modifiers=["Shift"])
    """
    elem = get_elem_by_bid(page, bid, demo_mode != "off")
    add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=True)

    def do(force: bool):
        elem.click(button=button, modifiers=modifiers, force=force, timeout=2000)

    call_fun(do, retry_with_force)


CUSTOM_ACTION_SPACE = [
    click,
    scroll,
    keyboard_type,
    keyboard_press,
    dblclick,
    goto,
    send_msg_to_user,
    go_back,
    tab_focus,
    new_tab,
]
CUSTOM_ACTION_MAPPING = HighLevelActionSet(
    subsets=["custom", "coord"], custom_actions=CUSTOM_ACTION_SPACE
).to_python_code


def generate_unique_id(input_string, length=6):
    # Use SHA-256 and truncate the hash to the desired length
    hash_object = hashlib.sha256(input_string.encode())
    return hash_object.hexdigest()[:length]


def deduplicate_tasks(tasks):
    seen = set()
    deduped = []
    for task in tasks:
        steps_str = "\n".join(task["steps"])  # use steps as unique signature
        if steps_str not in seen:
            seen.add(steps_str)
            deduped.append(task)
    return deduped


def log_episode(
    interactions: list[Interaction],
    metadata: dict[str, Any],
    system_message: str,
    outdir: str,
    steps: list[str],
    instructions: dict[str, str],
    task_type: str,
):
    logger = LocalEpisodeLogger(outdir)
    trajectory = {}
    logger.log_system_message(system_message)
    logger.log_json(metadata, "metadata.json")
    axtree_strs = []
    user_message_strs = []
    errors = []
    for i, interaction in enumerate(interactions):
        screenshot = Image.fromarray(interaction.state["obs"]["screenshot"])
        screenshot_name = logger.log_screenshot(screenshot, step=i + 1)
        _ = logger.log_extra_element_properties(
            interaction.state["obs"]["extra_element_properties"], step=i + 1
        )
        last_model_inputs = interaction.state.get("agent_inputs", None)
        other_obs: dict[str, Any] | None = None
        if last_model_inputs is not None:
            other_obs = {
                k: v
                for k, v in last_model_inputs.items()
                if k not in {"axtree_str", "system_message", "user_message"}
            }
            axtree_strs.append(last_model_inputs["axtree_str"])
            user_message_strs.append(last_model_inputs["user_message"])
        else:
            axtree_strs.append(get_axtree_str(interaction.state["obs"]))
            user_message_strs.append(None)
        axtree_name = logger.log_axtree(axtree_strs[-1], step=i + 1)
        user_message_name = logger.log_user_message(
            user_message_str=user_message_strs[-1], step=i + 1
        )
        if interaction is not None and interaction.action is not None:
            action = {
                k: interaction.action[k]
                for k in ["action_str", "action_description"]
            }
            action["action_output"] = interaction.action[
                "action_output"
            ].model_dump()
            action["action_output"]["action_name"] = interaction.action[
                "action_output"
            ].action.name
            if action["action_output"]["action_name"] == "click":
                bid = action["action_output"]["action"]["bid"]
                action["action_output"]["action"]["bbox"] = (
                    interaction.state["obs"]["extra_element_properties"]
                    .get(bid, {})
                    .get("bbox", None)
                )
                action["action_output"]["action"]["node_properties"] = (
                    get_node_properties(
                        bid, interaction.state["obs"]["axtree_object"]
                    )
                )
        else:
            action = {
                "action_str": None,
                "action_name": None,
                "action_description": None,
                "action_output": {
                    "thought": None,
                    "action": None,
                },
            }

        trajectory[i + 1] = {
            "screenshot": screenshot_name,
            "axtree": axtree_name,
            "user_message": user_message_name,
            "other_obs": other_obs,
            "action": action,
            "error": interaction.error,
            "action_timestamp": interaction.action_timestamp,
        }

    logger.log_json(trajectory, "trajectory.json")

    elements = [
        ft.Div(
            ft.H1(f"{metadata['eps_name']} ({task_type})"),
            ft.H2("Instructions"),
            create_table(
                columns=["level", "instruction"],
                rows=[
                    *[
                        dict(level=ft.I(k), instruction=v)
                        for k, v in instructions.items()
                    ],
                    dict(
                        level=ft.I("steps"),
                        instruction=ft.Ul(*[ft.Li(step) for step in steps]),
                    ),
                ],
            ),
        ),
        ft.H2("Trajectory"),
    ]
    for k, traj_step in trajectory.items():
        action = traj_step["action"]
        action_timestamp = datetime.fromtimestamp(
            traj_step["action_timestamp"]
        ).strftime("%Y-%m-%d | %H:%M:%S.%f")
        elements.extend(
            [
                ft.Div(
                    ft.Card(
                        ft.Div(
                            ft.Div(
                                ft.Img(src=f"images/{traj_step['screenshot']}"),
                                cls="col-xs-6",
                            ),
                            ft.Br(),
                            ft.Div(
                                ft.H6("Thought"),
                                ft.P(action["action_output"]["thought"]),
                                ft.H6("Action"),
                                ft.P(action["action_str"]),
                                ft.H6("Action Description"),
                                ft.P(action["action_description"]),
                                cls="col-xs-6",
                            ),
                            cls="row",
                        ),
                        header=ft.Div(
                            f"Step {k}",
                            ft.Code(action_timestamp, style="float: right;"),
                        ),
                        footer=ft.Div(
                            ft.Details(
                                ft.Summary("System Message"),
                                ft.Pre(ft.Code(system_message)),
                            ),
                            ft.Details(
                                ft.Summary("User Message"),
                                ft.Pre(ft.Code(user_message_strs[k - 1])),
                            ),
                            ft.Details(
                                ft.Summary("LLM Output"),
                                ft.Pre(
                                    ft.Code(
                                        json.dumps(
                                            action["action_output"], indent=2
                                        )
                                    )
                                ),
                            ),
                        ),
                    ),
                ),
            ]
        )

    logger.write_to_file(ft.to_xml(create_page(elements)), "trajectory.html")


def eval_task(
    eps_name: str,
    steps: list[str],
    instructions: dict[str, str],
    task_type: str,
    start_url: str,
    task: dict[str, Any],
    outdir: str,
    max_steps: int = 20,
    step_timeout_in_s: float = 30,
):
    try:
        env = gym.make(
            "browsergym/browserbase_openended",
            task_kwargs={"start_url": start_url, "goal": "\n".join(steps)},
            # pw_context_kwargs=sample_browser_context("linux"),
            # headless=True,
            action_mapping=CUSTOM_ACTION_MAPPING,
            timeout=int(step_timeout_in_s * 1000),
        )
    except Exception as e:
        print(f"Error in env creation: {str(e)}")
        return eps_name

    try:
        agent = AxtreeAgent(
            llm_response_format=SyntheticDataBaseActionOutput,
            system_message=SYSTEM_MESSAGE,
        )

        episode = Episode(
            env=env,
            agent=agent,
            eps_name=eps_name,
        )
        interactions, metadata = episode.run_episode(max_steps=max_steps)
        metadata["task"] = task
        log_episode(
            interactions=interactions,
            metadata=metadata,
            system_message=SYSTEM_MESSAGE,
            outdir=outdir,
            steps=steps,
            instructions=instructions,
            task_type=task_type,
        )
    except Exception as e:
        print(f"Error in eval_task for {eps_name}:\n{str(e)}")

    env.close()
    return eps_name


def main(
    task_prefix: str,
    tasks_json: str,
    output_dir: str,
    num_jobs: int,
    job_id: int,
    num_workers: int,
    traj_timeout_in_s: float | None = 300,
    step_timeout_in_s: float = 30,
    seed: int = 42,
    max_steps: int = 20,
):
    with open(tasks_json, "r") as f:
        tasks = json.load(f)

    print(f"Loaded {len(tasks)} total tasks for task {task_prefix}.")
    tasks = deduplicate_tasks(tasks)
    print(f"Loaded {len(tasks)} *unique* tasks for task {task_prefix}.")

    random.seed(seed)
    random.shuffle(tasks)

    selected_idx_and_tasks = [
        (i, task) for i, task in enumerate(tasks) if i % num_jobs == job_id
    ]

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        future_to_eps_name = dict()
        for i, task in selected_idx_and_tasks:
            task_type = task["task_type"]
            uid = generate_unique_id("\n".join(task["steps"]))
            eps_name = f"{task_prefix}_{task_type}_{uid}"
            if os.path.exists(
                os.path.join(output_dir, eps_name, "trajectory.html")
            ):
                print(f"Task {eps_name} already exists, skipping...")
                continue

            future = executor.submit(
                eval_task,
                eps_name=eps_name,
                steps=task["steps"],
                instructions=task["instruction"],
                task_type=task["task_type"],
                start_url=random.choice(
                    [
                        "https://www.google.com/",
                        "https://bing.com",
                        "https://wikipedia.org",
                        "https://arxiv.org",
                    ]
                ),
                task=task,
                outdir=os.path.join(output_dir, eps_name),
                max_steps=max_steps,
                step_timeout_in_s=step_timeout_in_s,
            )
            futures.append(future)
            future_to_eps_name[future] = eps_name
            print(f"Enqueued {eps_name}")

        if traj_timeout_in_s is None:
            traj_timeout_in_s = step_timeout_in_s * max_steps

        for future in as_completed(futures):
            eps_name = future_to_eps_name[future]
            try:
                _ = future.result(timeout=traj_timeout_in_s)
                print(f"Done {eps_name}")
            except FutureTimeoutError:
                print(f"Task {eps_name} timed out")
            except Exception as e:
                print(f"Exception in task {eps_name}:\n{str(e)}")
            finally:
                if not future.done():
                    future.cancel()


if __name__ == "__main__":
    fire.Fire(main)
