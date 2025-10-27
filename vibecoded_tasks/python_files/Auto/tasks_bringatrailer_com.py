import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

BAT_TASK_TYPES = Literal[
    "bat_search_auction",
    "bat_filter_no_reserve",
    "bat_explore_results",
    "bat_submit_vehicle_flow",
    "bat_faq_navigation",
    "bat_locate_premium_listing",
    "bat_list_categories",
]

BAT_SAMPLING_CONFIG: Dict[BAT_TASK_TYPES, int] = {
    "bat_search_auction": 10,
    "bat_filter_no_reserve": 10,
    "bat_explore_results": 10,
    "bat_submit_vehicle_flow": 10,
    "bat_faq_navigation": 10,
    "bat_locate_premium_listing": 10,
    "bat_list_categories": 10,
}

CATEGORY_FILTERS = [
    "Convertibles", "Electric Vehicles", "Hot Rods", "Military Vehicles", 
    "Motorcycles", "Race Cars", "Station Wagons"
]

def _ui() -> list[str]:
    return ["Dismiss popups/cookies if shown.", "Do not submit personal info; only browse/read."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Bring a Trailer", steps).model_dump()

def _go_home() -> list[str]:
    return ["Go to url 'https://bringatrailer.com/'.", *_ui()]

def bat_search_auction(payload: dict) -> dict:
    keyword = payload.get("keyword", "Porsche")
    steps = _go_home() + [
        f"Use the search function to find '{keyword}' auctions.",
        "Select the first result from the list.",
        "Record the auction's current bid and remaining time."
    ]
    return {"task_type":"bat_search_auction","keyword":keyword,"steps":steps}

def bat_filter_no_reserve(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to 'No Reserve' auctions from the main menu.",
        "Select and open one listing.",
        "Verify that the listing indicates 'No Reserve' in its details."
    ]
    return {"task_type":"bat_filter_no_reserve","steps":steps}

def bat_explore_results(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to the 'Results' page from the main menu.",
        "Choose an auction result and note the final sale price.",
        "Check the auction result has a 'SOLD' status."
    ]
    return {"task_type":"bat_explore_results","steps":steps}

def bat_submit_vehicle_flow(_: dict) -> dict:
    steps = _go_home() + [
        "Go to 'Submit a Vehicle' page.",
        "Read the requirements for submission.",
        "Verify that there are no upfront fee requirements mentioned."
    ]
    return {"task_type":"bat_submit_vehicle_flow","steps":steps}

def bat_faq_navigation(_: dict) -> dict:
    steps = _go_home() + [
        "Click on 'Frequently Asked Questions' from the menu.",
        "Find and read a section on bidding process.",
        "Verify that the FAQ includes details on bid submission."
    ]
    return {"task_type":"bat_faq_navigation","steps":steps}

def bat_locate_premium_listing(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to the 'Premium' section via the main menu.",
        "Choose a premium listing and note the features highlighted.",
        "Check for any 'Premium Listing' badge or label within details."
    ]
    return {"task_type":"bat_locate_premium_listing","steps":steps}

def bat_list_categories(_: dict) -> dict:
    category = random.choice(CATEGORY_FILTERS)
    steps = _go_home() + [
        f"Select '{category}' in Categories from the main menu.",
        "Open the first result in this category.",
        "List three details about the vehicle in this category listing."
    ]
    return {"task_type":"bat_list_categories","category":category,"steps":steps}

_TASK_GENERATORS: Dict[BAT_TASK_TYPES, Callable[[dict], dict]] = {
    "bat_search_auction": bat_search_auction,
    "bat_filter_no_reserve": bat_filter_no_reserve,
    "bat_explore_results": bat_explore_results,
    "bat_submit_vehicle_flow": bat_submit_vehicle_flow,
    "bat_faq_navigation": bat_faq_navigation,
    "bat_locate_premium_listing": bat_locate_premium_listing,
    "bat_list_categories": bat_list_categories,
}

def generate_bat_task(task_type: BAT_TASK_TYPES, payload: dict) -> dict:
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
    items = list(BAT_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_bat_task, ttype, p))
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