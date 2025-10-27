import json, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

AUTOZONE_TASK_TYPES = Literal[
    "autozone_part_search",
    "autozone_check_store_locator",
    "autozone_apply_deals",
    "autozone_explore_diy_guides",
    "autozone_view_parts_by_make",
    "autozone_redeem_rewards",
    "autozone_view_clearance",
]

AUTOZONE_SAMPLING_CONFIG: Dict[AUTOZONE_TASK_TYPES, int] = {
    "autozone_part_search": 10,
    "autozone_check_store_locator": 10,
    "autozone_apply_deals": 10,
    "autozone_explore_diy_guides": 10,
    "autozone_view_parts_by_make": 10,
    "autozone_redeem_rewards": 10,
    "autozone_view_clearance": 10,
}

ZIPCODES = ["98101", "94103", "90012", "60601", "10001", "75001", "80202", "30303", "02108", "73102"]
MAKES = ["Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "BMW", "Mercedes-Benz", "Audi", "Mazda"]
PARTS = ["brake rotors", "oil filters", "batteries", "spark plugs", "wipers", "alternators", "gaskets"]
GUIDES = ["battery replacement", "oil change", "brake pad replacement", "spark plug replacement"]

def _ui() -> list[str]:
    return ["Dismiss popups/cookies if shown.", "Do not enter personal info; only browse/read."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("AutoZone", steps).model_dump()

def _go_home() -> list[str]:
    return ["Open autozone.com.", *_ui()]

def autozone_part_search(payload: dict) -> dict:
    part = payload.get("part", random.choice(PARTS))
    steps = _go_home() + [f"Search for part '{part}'.", "Open the first result and note the price and availability."]
    return {"task_type": "autozone_part_search", "part": part, "steps": steps}

def autozone_check_store_locator(payload: dict) -> dict:
    zipcode = payload.get("zip", random.choice(ZIPCODES))
    steps = _go_home() + ["Open the store locator.", f"Enter ZIP code '{zipcode}'.", "List the first three stores displayed."]
    return {"task_type": "autozone_check_store_locator", "zip": zipcode, "steps": steps}

def autozone_apply_deals(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to the deals page.",
        "Select the first deal and read the terms.",
        "Check if the deal applies to any in-store purchase."
    ]
    return {"task_type": "autozone_apply_deals", "steps": steps}

def autozone_explore_diy_guides(payload: dict) -> dict:
    guide = payload.get("guide", random.choice(GUIDES))
    steps = _go_home() + [
        "Navigate to the DIY guides.",
        f"Choose guide for '{guide}'.",
        "Read through the procedure and list necessary tools."
    ]
    return {"task_type": "autozone_explore_diy_guides", "guide": guide, "steps": steps}

def autozone_view_parts_by_make(payload: dict) -> dict:
    make = payload.get("make", random.choice(MAKES))
    steps = _go_home() + [
        "Navigate to parts by vehicle make.",
        f"Select '{make}'.",
        "Open a category and note the types of parts available."
    ]
    return {"task_type": "autozone_view_parts_by_make", "make": make, "steps": steps}

def autozone_redeem_rewards(_: dict) -> dict:
    steps = _go_home() + [
        "Open the AutoZone Rewards section.",
        "Check how to redeem rewards points.",
        "View available rewards and note any that require points."
    ]
    return {"task_type": "autozone_redeem_rewards", "steps": steps}

def autozone_view_clearance(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to the clearance section.",
        "List the first three items on clearance.",
        "Note the available discounts."
    ]
    return {"task_type": "autozone_view_clearance", "steps": steps}

_TASK_GENERATORS: Dict[AUTOZONE_TASK_TYPES, Callable[[dict], dict]] = {
    "autozone_part_search": autozone_part_search,
    "autozone_check_store_locator": autozone_check_store_locator,
    "autozone_apply_deals": autozone_apply_deals,
    "autozone_explore_diy_guides": autozone_explore_diy_guides,
    "autozone_view_parts_by_make": autozone_view_parts_by_make,
    "autozone_redeem_rewards": autozone_redeem_rewards,
    "autozone_view_clearance": autozone_view_clearance,
}

def generate_autozone_task(task_type: AUTOZONE_TASK_TYPES, payload: dict) -> dict:
    t = _TASK_GENERATORS[task_type](payload or {})
    t["meta"] = {"site": "autozone.com"}
    t["instruction"] = _instr(t["steps"])
    return t

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list):
        payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(AUTOZONE_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_autozone_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try:
                out.append(fut.result(timeout=timeout))
            except Exception:
                pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)