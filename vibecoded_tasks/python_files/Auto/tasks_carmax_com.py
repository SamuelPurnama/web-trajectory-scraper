import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

CARMAX_TASK_TYPES = Literal[
    "carmax_search_by_make",
    "carmax_filter_by_budget",
    "carmax_view_finance_options",
    "carmax_read_car_review",
    "carmax_locate_nearest_store",
    "carmax_value_trade_in",
    "carmax_browse_electric_vehicles",
]

CARMAX_SAMPLING_CONFIG: Dict[CARMAX_TASK_TYPES, int] = {
    "carmax_search_by_make": 10,
    "carmax_filter_by_budget": 10,
    "carmax_view_finance_options": 10,
    "carmax_read_car_review": 10,
    "carmax_locate_nearest_store": 10,
    "carmax_value_trade_in": 10,
    "carmax_browse_electric_vehicles": 10,
}

MAKES = ["Toyota", "Honda", "Ford", "Chevrolet", "Nissan"]
BUDGETS = [10000, 15000, 20000, 25000, 30000]
REVIEWS = [
    "honda/civic",
    "chevrolet/tahoe",
    "ford/escape",
    "toyota/camry",
    "nissan/rogue",
]
STORES = ["Austin, TX", "Los Angeles, CA", "Houston, TX", "Chicago, IL", "Miami, FL"]
VEHICLE_YEARS = ["2004", "2010", "2013", "2015", "2019"]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners that appear.",
        "Do not interact with elements unrelated to the task.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("CarMax", steps).model_dump()

def carmax_search_by_make(_: dict) -> dict:
    make = random.choice(MAKES)
    steps = [
        "Go to url 'https://www.carmax.com'.",
        *_ui_hygiene(),
        f"Locate and click on the 'Shop' menu.",
        f"Select '{make}' from the list of makes.",
        "Confirm the page displays listings for the selected make.",
    ]
    return {"task_type": "carmax_search_by_make", "make": make, "steps": steps}

def carmax_filter_by_budget(_: dict) -> dict:
    budget = random.choice(BUDGETS)
    steps = [
        "Go to url 'https://www.carmax.com/cars'.",
        *_ui_hygiene(),
        f"Click on the filter for budget and set it to under ${budget}.",
        "Ensure the results display cars within the specified budget.",
    ]
    return {"task_type": "carmax_filter_by_budget", "budget": budget, "steps": steps}

def carmax_view_finance_options(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.carmax.com/car-financing'.",
        *_ui_hygiene(),
        "Locate and select 'Get pre-qualified'.",
        "Confirm the page displays financing options.",
    ]
    return {"task_type": "carmax_view_finance_options", "steps": steps}

def carmax_read_car_review(_: dict) -> dict:
    review = random.choice(REVIEWS)
    steps = [
        f"Go to url 'https://www.carmax.com/research/{review}'.",
        *_ui_hygiene(),
        "Read the review content.",
        "Verify the page displays a review for the correct vehicle model.",
    ]
    return {"task_type": "carmax_read_car_review", "review": review, "steps": steps}

def carmax_locate_nearest_store(_: dict) -> dict:
    store = random.choice(STORES)
    steps = [
        "Go to url 'https://www.carmax.com/stores'.",
        *_ui_hygiene(),
        f"Search for the nearest store in '{store}'.",
        "Ensure the map or list shows the nearest store location.",
    ]
    return {"task_type": "carmax_locate_nearest_store", "store": store, "steps": steps}

def carmax_value_trade_in(_: dict) -> dict:
    vehicle_year = random.choice(VEHICLE_YEARS)
    steps = [
        "Go to url 'https://www.carmax.com/sell-my-car'.",
        *_ui_hygiene(),
        "Click on 'Get Your Offer' button.",
        f"Enter the year '{vehicle_year}' for the vehicle.",
        "Confirm the page prompts for further vehicle details.",
    ]
    return {"task_type": "carmax_value_trade_in", "vehicle_year": vehicle_year, "steps": steps}

def carmax_browse_electric_vehicles(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.carmax.com/cars/electric-vehicles'.",
        *_ui_hygiene(),
        "Browse the list of available electric vehicles.",
        "Verify the list contains electric vehicle options.",
    ]
    return {"task_type": "carmax_browse_electric_vehicles", "steps": steps}

_TASK_GENERATORS: Dict[CARMAX_TASK_TYPES, Callable[[dict], dict]] = {
    "carmax_search_by_make": carmax_search_by_make,
    "carmax_filter_by_budget": carmax_filter_by_budget,
    "carmax_view_finance_options": carmax_view_finance_options,
    "carmax_read_car_review": carmax_read_car_review,
    "carmax_locate_nearest_store": carmax_locate_nearest_store,
    "carmax_value_trade_in": carmax_value_trade_in,
    "carmax_browse_electric_vehicles": carmax_browse_electric_vehicles,
}

def generate_carmax_task(task_type: CARMAX_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = _instr(task["steps"])
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(CARMAX_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_carmax_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)