import hashlib
import json
import os
import random
import re
import time
import warnings
import logging
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from concurrent.futures import as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

# Suppress browser automation warnings
logging.getLogger("playwright").setLevel(logging.ERROR)
logging.getLogger("browsergym").setLevel(logging.ERROR)

# Filter out specific browser automation warnings
class BrowserWarningFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return not any(phrase in message for phrase in [
            "Frame marking: not all elements have been visited by the intersection_observer",
            "AXTree merging: extracted AXTree does not contain frameId",
            "intersection_observer after 1000 ms"
        ])

# Apply filter to root logger
logging.getLogger().addFilter(BrowserWarningFilter())

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
from agent.node_traversal_agent import NodeTraversalAgent
from agent.utils import AgentBase
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


def hover(bid: str):
    """
    Hover over an element.

    Examples:
        hover('b8')
    """
    elem = get_elem_by_bid(page, bid, demo_mode != "off")
    add_demo_mode_effects(
        page, elem, bid, demo_mode=demo_mode, move_cursor=True, highlight_box=False
    )

    def do(force: bool):
        elem.hover(force=force, timeout=500)
    
    call_fun(do, retry_with_force)
    time.sleep(1)  # Wait 1 second after hover


CUSTOM_ACTION_SPACE = [
    click,
    hover,
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
        # Use path_id if available, otherwise use steps as unique signature
        if "path_id" in task:
            signature = task["path_id"]
        else:
            signature = "\n".join(task["steps"])
        
        if signature not in seen:
            seen.add(signature)
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
    agent: AgentBase | None = None,
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
            axtree_strs.append(last_model_inputs.get("axtree_str", ""))
            user_message_strs.append(last_model_inputs.get("user_message", None))
        else:
            axtree_strs.append(get_axtree_str(interaction.state["obs"]))
            user_message_strs.append(None)
        axtree_name = logger.log_axtree(axtree_strs[-1], step=i + 1)
        user_message_name = logger.log_user_message(
            user_message_str=user_message_strs[-1], step=i + 1
        )
        
        # Log current URL
        current_url = interaction.state["obs"].get("url", "")
        url_name = logger.log_current_url(current_url, step=i + 1)
        
        # Log HTML content if available
        html_content = interaction.state["obs"].get("html_content", "")
        html_name = logger.log_html(html_content, step=i + 1) if html_content else None
        
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
            elif action["action_output"]["action_name"] == "hover":
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
            "current_url": url_name,
            "html_content": html_name,
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
    
    # Generate verdict for NodeTraversalAgent
    if agent is not None and hasattr(agent, '__class__') and agent.__class__.__name__ == 'NodeTraversalAgent':
        verdict = determine_node_traversal_verdict(interactions, metadata, agent)
        
        # Add basic information to match the original text format
        if agent:
            verdict["progress"] = f"Completed {agent.current_step} out of {len(agent.path)} URLs"
            verdict["path"] = agent.path
            
            # Add hover candidates if any were found
            if hasattr(agent, 'hover_candidates') and agent.hover_candidates:
                verdict["hover_candidates"] = agent.hover_candidates
                
        logger.log_json(verdict, "verdict.json")
        
        # Save any expanded axtrees that were generated
        if hasattr(agent, 'expanded_axtrees') and agent.expanded_axtrees:
            os.makedirs(os.path.join(outdir, "expanded_axtrees"), exist_ok=True)
            for step, expanded_axtree_str in agent.expanded_axtrees.items():
                filename = f"expanded_axtree_{str(step).zfill(3)}.txt"
                filepath = os.path.join("expanded_axtrees", filename)
                logger.write_to_file(expanded_axtree_str, filepath)
                print(f"Saved expanded axtree for step {step} to {os.path.join(outdir, filepath)}")


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
    agent_type: str = "axtree",
):
    # Always create output directory
    os.makedirs(outdir, exist_ok=True)
    
    env = None
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
        # Save error information
        error_metadata = {
            "eps_name": eps_name,
            "error_type": "ENV_CREATION_ERROR",
            "error_message": str(e),
            "task": task,
        }
        logger = LocalEpisodeLogger(outdir)
        logger.log_json(error_metadata, "error_metadata.json")
        return eps_name

    try:
        if agent_type == "node_traversal":
            # Extract URLs from task steps for NodeTraversalAgent
            path = task.get("path", [start_url])  # Use path if provided, otherwise just start_url
            agent = NodeTraversalAgent(path=path)
        else:
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
            agent=agent,  # Pass agent for verdict determination
        )
    except Exception as e:
        print(f"Error in eval_task for {eps_name}:\n{str(e)}")
        # Save error information
        error_metadata = {
            "eps_name": eps_name,
            "error_type": "EPISODE_EXECUTION_ERROR", 
            "error_message": str(e),
            "task": task,
        }
        logger = LocalEpisodeLogger(outdir)
        logger.log_json(error_metadata, "error_metadata.json")
    finally:
        if env:
            env.close()
            
    return eps_name


def determine_node_traversal_verdict(
    interactions: list[Interaction],
    metadata: dict[str, Any],
    agent: NodeTraversalAgent
) -> dict[str, str]:
    """Determine verdict for NodeTraversalAgent trajectory."""
    
    def create_verdict(status: str, reason: str, details: str, infeasible_reason: str = None) -> dict[str, str]:
        """Helper to create verdict dictionary."""
        total_urls = len(agent.path)
        urls_visited = agent.current_step
        if total_urls > 1:
            percentage_completion = (urls_visited - 1) / (total_urls - 1)
        else:
            percentage_completion = 1.0 if urls_visited >= 1 else 0.0
        
        verdict = {
            "total_urls": total_urls,
            "urls_visited_successfully": urls_visited,
            "percentage_completion": round(percentage_completion, 3),
            "status": status,
            "reason": reason,
            "details": details
        }
        if infeasible_reason:
            verdict["infeasible_reason"] = infeasible_reason
        return verdict
    
    def extract_infeasible_reason(action: dict) -> str:
        """Extract infeasible reason from action."""
        if not action:
            return ""
        
        # Try action_output first
        if action.get("action_output"):
            action_output = action["action_output"]
            thought = getattr(action_output, 'thought', '')
            if hasattr(action_output, 'action') and hasattr(action_output.action, 'infeasibility_reason'):
                infeasible_reason = action_output.action.infeasibility_reason
                return thought or infeasible_reason
        
        # Fallback to action_str
        action_str = action.get("action_str", "")
        if action_str.startswith("report_infeasible("):
            match = re.search(r'report_infeasible\(reason=["\']([^"\']+)["\']', action_str)
            if match:
                return match.group(1)
        
        return ""
    
    def get_action_name(action: dict) -> str:
        """Get action name from action dictionary."""
        if action and action.get("action_output"):
            action_output = action["action_output"]
            if hasattr(action_output, 'action') and hasattr(action_output.action, 'name'):
                return action_output.action.name
        return ""
    
    # Check for interaction errors
    for interaction in interactions:
        if interaction.error:
            error_type = next(iter(interaction.error.keys()))
            error_msg = interaction.error[error_type]
            return create_verdict("FAILURE", error_type, f"Error in {error_type.lower().replace('_', ' ')}: {error_msg}")
    
    # Get last action
    last_action = interactions[-1].action if interactions else None
    action_name = get_action_name(last_action)
    
    # Handle different action types
    if action_name == "report_infeasible":
        reason = extract_infeasible_reason(last_action)
        if "click failed after all retry attempts" in reason:
            return create_verdict("FAILURE", "CLICK_FAILED", f"Agent could not click target link: {reason}", reason)
        elif "requires hovering before it can be accessed" in reason:
            return create_verdict("FAILURE", "HOVER_REQUIRED", f"Target URL is hidden behind hover elements: {reason}", reason)
        else:
            return create_verdict("FAILURE", "INFEASIBLE_REPORTED", f"Agent reported task as infeasible: {reason}", reason)
    
    elif action_name == "send_msg_to_user":
        if last_action and last_action.get("action_output"):
            action_output = last_action["action_output"]
            if hasattr(action_output.action, 'msg') and action_output.action.msg == "[EXIT]":
                if agent.current_step >= len(agent.path):
                    return create_verdict("SUCCESS", "COMPLETED", f"Successfully navigated through all {len(agent.path)} URLs in the path")
                else:
                    return create_verdict("FAILURE", "EARLY_EXIT", f"Agent exited early after step {agent.current_step} out of {len(agent.path)} total steps")
    
    # Handle other cases
    if len(interactions) >= 20:
        return create_verdict("FAILURE", "MAX_STEPS_REACHED", f"Episode terminated after reaching maximum steps ({len(interactions)})")
    
    return create_verdict("FAILURE", "UNKNOWN", f"Episode ended unexpectedly with {len(interactions)} interactions")


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
    agent_type: str = "axtree",
):
    with open(tasks_json, "r") as f:
        data = json.load(f)

    # Handle new format: {"paths": {"6": {"path": [...], "length": 4}}}
    if "paths" in data:
        tasks = []
        for path_id, path_data in data["paths"].items():
            task = {
                "path_id": path_id,
                "path": path_data["path"],
                "name": path_data.get("name", "unknown"),  # Extract name field
                "task_type": "navigation",
                "steps": [f"Navigate through path {path_id}"],
                "instruction": {"goal": f"Navigate through path {path_id}"}
            }
            tasks.append(task)
    else:
        # Fallback to old format
        tasks = data

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
            # Use path_id if available, otherwise generate unique ID
            if "path_id" in task:
                # Use name field as prefix if available, otherwise use task_prefix
                name_prefix = task.get("name", task_prefix)
                eps_name = f"{name_prefix}_{task['path_id']}"
            else:
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
                agent_type=agent_type,
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

