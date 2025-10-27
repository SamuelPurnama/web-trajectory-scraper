import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

TOYOTA_TASK_TYPES = Literal[
    "toyota_search_vehicle",
    "toyota_view_offers",
    "toyota_configure_model",
    "toyota_find_dealer",
    "toyota_check_specials",
    "toyota_explore_models",
    "toyota_access_support"
]

TOYOTA_SAMPLING_CONFIG: Dict[TOYOTA_TASK_TYPES, int] = {
    "toyota_search_vehicle": 10,
    "toyota_view_offers": 10,
    "toyota_configure_model": 10,
    "toyota_find_dealer": 10,
    "toyota_check_specials": 10,
    "toyota_explore_models": 10,
    "toyota_access_support": 10
}

ZIPS = ["98101", "94103", "90012", "60601", "10001", "75001", "80202", "30303", "02108", "73102", "85004", "19107", "97204", "20001", "33130", "27601", "55401", "15222", "64106", "95814"]

TOYOTA_MODELS = [
    "Camry", "Corolla", "Prius", "RAV4", "C-HR", "Yaris", "Highlander", "4Runner", "Tacoma", "Tundra",
    "Sienna", "Avalon", "Venza", "GR Corolla", "Supra", "Sequoia", "Prius Prime", "bZ4X"
]

def _ui() -> list[str]:
    return ["Dismiss popups/cookies if shown.", "Do not submit personal info; only browse/read."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Toyota.com", steps).model_dump()

def _go_home() -> list[str]:
    return ["Go to url 'https://www.toyota.com/'.", *_ui()]

def toyota_search_vehicle(payload: dict) -> dict:
    model = payload.get("model", random.choice(TOYOTA_MODELS))
    steps = _go_home() + [
        f"Search for vehicle model '{model}' using the search bar.",
        f"Verify that search results contain '{model}'."
    ]
    return {"task_type": "toyota_search_vehicle", "model": model, "steps": steps}

def toyota_view_offers(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to the 'Deals and Incentives' section.",
        "View and record any available offers for one model."
    ]
    return {"task_type": "toyota_view_offers", "steps": steps}

def toyota_configure_model(payload: dict) -> dict:
    model = payload.get("model", random.choice(TOYOTA_MODELS))
    steps = _go_home() + [
        "Go to the 'Build & Price' section.",
        f"Select the model '{model}' to configure.",
        "Customize the model by selecting different options.",
        "Verify the final configurations summary."
    ]
    return {"task_type": "toyota_configure_model", "model": model, "steps": steps}

def toyota_find_dealer(payload: dict) -> dict:
    zipc = payload.get("zip", random.choice(ZIPS))
    steps = _go_home() + [
        "Go to the 'Find a Dealer' page.",
        f"Enter ZIP code '{zipc}'.",
        "Verify that a list of dealers is displayed for the given ZIP code."
    ]
    return {"task_type": "toyota_find_dealer", "zip": zipc, "steps": steps}

def toyota_check_specials(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to 'Local Specials'.",
        "Check for any current special promotions or offers in your region.",
        "Verify the presence of at least one special offer."
    ]
    return {"task_type": "toyota_check_specials", "steps": steps}

def toyota_explore_models(_: dict) -> dict:
    steps = _go_home() + [
        "Go to the 'Explore All Vehicles' page.",
        "Select a category of vehicles (e.g., SUVs, Sedans).",
        "Verify that the vehicles listed under this category are relevant."
    ]
    return {"task_type": "toyota_explore_models", "steps": steps}

def toyota_access_support(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to the 'Contact Us' section.",
        "Explore the FAQ or support topics.",
        "Verify that support resources are available and accessible."
    ]
    return {"task_type": "toyota_access_support", "steps": steps}

_TASK_GENERATORS: Dict[TOYOTA_TASK_TYPES, Callable[[dict], dict]] = {
    "toyota_search_vehicle": toyota_search_vehicle,
    "toyota_view_offers": toyota_view_offers,
    "toyota_configure_model": toyota_configure_model,
    "toyota_find_dealer": toyota_find_dealer,
    "toyota_check_specials": toyota_check_specials,
    "toyota_explore_models": toyota_explore_models,
    "toyota_access_support": toyota_access_support
}

def generate_toyota_task(task_type: TOYOTA_TASK_TYPES, payload: dict) -> dict:
    t = _TASK_GENERATORS[task_type](payload or {})
    t["instruction"] = _instr(t["steps"])
    return t

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(TOYOTA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_toyota_task, ttype, p))
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