import hashlib
import json
import os
import random
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from concurrent.futures import as_completed
from typing import Any

import fire
from playwright.async_api import async_playwright
from browserbase import Browserbase
import asyncio

from logger import PlaywrightLogger
from deterministic_agent import DeterministicAgent

API, PROJ = os.environ["BROWSERBASE_API_KEY"], os.environ["BROWSERBASE_PROJECT_ID"]
BROWSERGYM_ID_ATTRIBUTE = "bid"

# VIEWPORT CONFIGURATION - Easily adjustable ratios
VIEWPORT_CONFIGS = [
    {"width": 1920, "height": 1080, "name": "Standard Full HD (Desktop)", "ratio": 0.2},
    {"width": 1366, "height": 768, "name": "Widescreen Laptop", "ratio": 0.3},
    {"width": 1536, "height": 864, "name": "High-Resolution Laptop", "ratio": 0.3},
    {"width": 1280, "height": 720, "name": "Small Desktop Monitor", "ratio": 0.1},
    {"width": 1024, "height": 768, "name": "Minimum Supported Desktop Viewport", "ratio": 0.1},
]

def sample_viewport():
    """Sample a viewport based on the configured ratios."""
    cumulative_weights = []
    total = 0
    for config in VIEWPORT_CONFIGS:
        total += config["ratio"]
        cumulative_weights.append(total)
    
    # normalize just in case they dont add up to 1 but they should for ease of mind. 
    cumulative_weights = [w / total for w in cumulative_weights]
    
    rand = random.random()
    for i, weight in enumerate(cumulative_weights):
        if rand <= weight:
            return VIEWPORT_CONFIGS[i]
    
    # Fallback
    return VIEWPORT_CONFIGS[0]


def generate_unique_id(input_string, length=6):
    hash_object = hashlib.sha256(input_string.encode())
    return hash_object.hexdigest()[:length]


def deduplicate_tasks(tasks):
    seen = set()
    deduped = []
    for task in tasks:
        task_str = json.dumps(task, sort_keys=True)
        if task_str not in seen:
            seen.add(task_str)
            deduped.append(task)
    return deduped


async def eval_task(
    eps_name: str,
    task: dict[str, Any],
    outdir: str,
):
    playwright = await async_playwright().start()

    try:
        playwright.selectors.set_test_id_attribute(BROWSERGYM_ID_ATTRIBUTE)

        # Sample viewport configuration
        viewport_config = sample_viewport()
        # print(f"[{eps_name}] Using viewport: {viewport_config['width']}x{viewport_config['height']} ({viewport_config['name']})")

        session = Browserbase(api_key=API).sessions.create(
            project_id=PROJ,
            proxies=[
                {
                "type": "browserbase",
                "geolocation": {
                    "city": "NEW_YORK",
                    "state": "NY",
                    "country": "US"
                    }
                }
            ],
            browser_settings={
                "advanced_stealth": True,
                "solve_captchas": True,
                "fingerprint": {
                    "screen": {
                        "maxWidth": viewport_config["width"],
                        "maxHeight": viewport_config["height"],
                        "minWidth": viewport_config["width"],
                        "minHeight": viewport_config["height"],
                    },
                },
                "viewport": {
                    "width": viewport_config["width"],
                    "height": viewport_config["height"],
                },
            },
        )

        browser = await playwright.chromium.connect_over_cdp(session.connect_url)
        page = browser.contexts[0].pages[0]
        
        # Explicitly set the viewport size to ensure it's properly applied
        await page.set_viewport_size({
            "width": viewport_config["width"], 
            "height": viewport_config["height"]
        })

        # This is the initial, random page the browser loads before the agent takes over.
        random_start_url = random.choice([
            "https://www.google.com/",
            "https://bing.com",
            "https://wikipedia.org",
            "https://arxiv.org",
        ])

        path = task.get("path", [])

        logger_instance = PlaywrightLogger(outdir, page=page, browser=browser)
        # The agent's true start_url is the first item in its path.
        agent = DeterministicAgent(path[0], path, logger_instance, eps_name=eps_name, debug=task.get('debug', False))

        captcha_info = {"started": False, "finished": False}

        def handle_console(msg):
            if msg.text == "browserbase-solving-started":
                # print(f"[{eps_name}] Captcha Solving In Progress on {random_start_url}")
                captcha_info["started"] = True
            elif msg.text == "browserbase-solving-finished":
                # print(f"[{eps_name}] Captcha Solving Completed on {random_start_url}")
                captcha_info["finished"] = True

        page.on("console", handle_console)

        await page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
        await page.evaluate("""() => {
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        }""")

        # most valuable first for loading
        # for wait_condition in ("networkidle", "load", "domcontentloaded"):
        for wait_condition in ("domcontentloaded", "load", "networkidle"):
            try:
                await page.goto(random_start_url, wait_until=wait_condition, timeout=45000)
                break
            except Exception:
                continue

        # Wait for captcha if it was detected but hasn't finished
        if captcha_info["started"] and not captcha_info["finished"]:
            # print(f"[{eps_name}] Waiting for CAPTCHA to be solved on {random_start_url}...")
            await page.wait_for_timeout(60000)

        # Main agent loop
        current_step = 0
        error_message = None
        while current_step < agent.max_steps:
            obs = await agent.logger.get_obs(step=current_step)

            # Predict action first
            action = await agent.predict_action(obs, page)
            
            # Enrich tab_focus action before recording
            if action.get("action") == "tab_focus":
                agent.logger.tab_focus_count += 1
                action["tab_id"] = agent.logger.tab_focus_count
                # The new page is the last one in the list
                page_index = len(browser.contexts[0].pages) - 1
                action["page_index"] = page_index

            agent.logger.record_interaction(current_step, obs, action)

            # Now, write the log files
            await agent.logger.write_log_files(obs, current_step)
            
            try:
                # Finally, execute the action
                if action["action"] == "exit":
                    # print(f"[{eps_name}] Agent decided to exit: {action.get('thought')}")
                    break
                elif action["action"] == "goto":
                    navigated = False
                    for wait_condition in ("networkidle", "load", "domcontentloaded"):
                        try:
                            await page.goto(action["url"], wait_until=wait_condition, timeout=45000)
                            navigated = True
                            break
                        except Exception:
                            continue
                    if not navigated:
                        raise Exception(f"Page.goto: Timeout 45000ms exceeded trying to navigate to {action['url']}")
                    
                    agent.did_goto = True
                elif action["action"] == "click":
                    await agent.click_element(page, action["bid"])
                elif action["action"] == "tab_focus":
                    # The new page is the last one in the list
                    new_page = browser.contexts[0].pages[action["page_index"]]
                    await new_page.bring_to_front()
                    
                    # Set viewport for the new tab
                    await new_page.set_viewport_size({
                        "width": viewport_config["width"],
                        "height": viewport_config["height"]
                    })
                    
                    # Close the old page
                    # await page.close()
                    
                    # Update the main page variable and the logger's page
                    page = new_page
                    agent.logger.page = page
                    # print(f"[{eps_name}] Switched to new tab with URL: {page.url}")
                elif action["action"] == "hover":
                    if "x" in action and "y" in action:
                        await agent.hover_element(page, x=action["x"], y=action["y"])
                    else:
                        await agent.hover_element(page, bid=action["bid"])
                elif action["action"] == "scroll":
                    await agent.scroll_page(page, action["direction"])
                elif action["action"] == "noop":
                    pass # Do nothing, just proceed to the next step
    
                current_step = agent.current_step
            except Exception as e:
                error_message = str(e)
                # print(f"[{eps_name}] An error occurred during agent action: {error_message}")
                agent.logger.record_interaction(current_step, obs, action, error=error_message)
                # Save verdict on error
                if hasattr(agent, '_save_verdict'):
                    agent._save_verdict(error_message)
                else:
                    # Fallback: write minimal verdict
                    verdict = {
                        "total_urls": len(agent.path) if hasattr(agent, 'path') else 0,
                        "urls_visited_successfully": getattr(agent, 'current_path_index', 0) + 1,
                        "status": "FAILURE",
                        "reason": error_message,
                        "progress": 0.0,
                        "path": getattr(agent, 'path', []),
                    }
                    outdir = getattr(agent.logger, 'outdir', '.') if hasattr(agent, 'logger') else '.'
                    with open(os.path.join(outdir, 'verdict.json'), 'w') as f:
                        json.dump(verdict, f, indent=2)
                break

        # Log viewport info in metadata
        metadata_extra = {
            "viewport": {
                "width": viewport_config["width"],
                "height": viewport_config["height"],
                "name": viewport_config["name"]
            }
        }
        
        # Finalize logging
        agent.logger.log_trajectory_json()
        agent.logger.log_metadata({**task, **metadata_extra}, eps_name=eps_name)
        agent.logger.log_trajectory_html(eps_name, task)

        await browser.close()
        await playwright.stop()

        return eps_name

    except Exception as e:
        # print(f"Error in eval_task for {eps_name}: {str(e)}")
        if 'browser' in locals() and browser.is_connected():
            await browser.close()
        if 'playwright' in locals():
            await playwright.stop()
        return eps_name


def run_async_eval_task(*args, **kwargs):
    # In eval_task, det_agent is removed. So it needs to be removed here.
    kwargs.pop('det_agent', None)
    return asyncio.run(eval_task(*args, **kwargs))


def main(
    tasks_json: str,
    output_dir: str,
    num_jobs: int,
    job_id: int,
    num_workers: int,
    seed: int = 42,
    debug: bool = False,
):
    with open(tasks_json, "r") as f:
        data = json.load(f)

    # Adapt to the new nested JSON structure - preserve the original keys
    tasks = []
    if "paths" in data:
        for key, value in data["paths"].items():
            # Add the original key to the task data
            value["original_key"] = key
            tasks.append(value)

    if debug:
        for task in tasks:
            task['debug'] = True

    print(f"Loaded {len(tasks)} total tasks.")

    random.seed(seed)
    # No need to shuffle if we're running specific tests
    # random.shuffle(tasks)

    selected_idx_and_tasks = [
        (i, task) for i, task in enumerate(tasks) if i % num_jobs == job_id
    ]

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        future_to_eps_name = dict()

        for i, task in selected_idx_and_tasks:
            # Use the descriptive name and original key from the JSON for the directory
            task_name = task.get("name", "task")
            original_key = task.get("original_key", str(i))
            eps_name = f"task_{task_name}_{original_key}"

            if os.path.exists(os.path.join(output_dir, eps_name, "screenshot_000.png")):
                print(f"Task {eps_name} already exists, skipping...")
                continue

            future = executor.submit(
                run_async_eval_task,
                eps_name=eps_name,
                task=task,
                outdir=os.path.join(output_dir, eps_name),
            )
            futures.append(future)
            future_to_eps_name[future] = eps_name
            # print(f"Enqueued {eps_name}")

        for future in as_completed(futures):
            eps_name = future_to_eps_name[future]
            try:
                _ = future.result(timeout=300)
            except Exception:
                if not future.done():
                    future.cancel()


if __name__ == "__main__":
    fire.Fire(main)

