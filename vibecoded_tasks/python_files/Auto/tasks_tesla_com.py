import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

TESLA_TASK_TYPES = Literal[
    "tesla_model_purchase_flow",
    "tesla_support_navigation",
    "tesla_test_drive_booking",
    "tesla_compare_models",
    "tesla_view_solar_options",
    "tesla_check_charging_stations",
    "tesla_find_collision_centers",
]

TESLA_SAMPLING_CONFIG: Dict[TESLA_TASK_TYPES, int] = {
    "tesla_model_purchase_flow": 10,
    "tesla_support_navigation": 10,
    "tesla_test_drive_booking": 10,
    "tesla_compare_models": 10,
    "tesla_view_solar_options": 10,
    "tesla_check_charging_stations": 10,
    "tesla_find_collision_centers": 10,
}

MODELS = ["Model S", "Model 3", "Model X", "Model Y"]
CITIES = ["San Francisco", "Los Angeles", "New York", "Chicago", "Miami", "Dallas"]
SOLAR_PRODUCTS = ["Solar Panels", "Solar Roof", "Powerwall"]

def _ui() -> list[str]:
    return [
        "Dismiss popups/cookies if shown.",
        "Do not submit personal info; only browse/read.",
        "Avoid clicking links that require navigation away from the current page.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Tesla.com", steps).model_dump()

def _go_home() -> list[str]:
    return ["Go to url 'https://www.tesla.com/'.", *_ui()]

def tesla_model_purchase_flow(payload: dict) -> dict:
    model = payload.get("model", random.choice(MODELS))
    steps = _go_home() + [
        f"Select and open the Tesla '{model}' page.",
        "Click on the 'Order Now' button.",
        "Configure the car with default options available.",
        "Confirm the summary details at the end of the configuration wizard."
    ]
    return {"task_type": "tesla_model_purchase_flow", "model": model, "steps": steps}

def tesla_support_navigation(_: dict) -> dict:
    steps = _go_home() + [
        "Click on 'Support' in the navigation menu.",
        "Explore 'Vehicle Support'.",
        "Read about 'Battery Range Tips' and note one tip provided."
    ]
    return {"task_type": "tesla_support_navigation", "steps": steps}

def tesla_test_drive_booking(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = _go_home() + [
        "Navigate to the 'Demo Drive' section.",
        f"Choose a location near '{city}' for the test drive.",
        "Select a model available for test drives.",
        "Fill in the details for the demo drive request form.",
        "Verify the confirmation information without submitting."
    ]
    return {"task_type": "tesla_test_drive_booking", "city": city, "steps": steps}

def tesla_compare_models(payload: dict) -> dict:
    model1 = payload.get("model1", random.choice(MODELS))
    model2 = payload.get("model2", random.choice([m for m in MODELS if m != model1]))
    steps = _go_home() + [
        "Open the 'Compare' page.",
        f"Add '{model1}' to the comparison list.",
        f"Add '{model2}' to the comparison list.",
        "Compare their specifications and list key differences like range and price."
    ]
    return {"task_type": "tesla_compare_models", "model1": model1, "model2": model2, "steps": steps}

def tesla_view_solar_options(_: dict) -> dict:
    product = random.choice(SOLAR_PRODUCTS)
    steps = _go_home() + [
        "Navigate to the 'Energy' section.",
        f"Click on the '{product}' option.",
        "Review the benefits and options available.",
        "Note any financial incentives available for this product."
    ]
    return {"task_type": "tesla_view_solar_options", "product": product, "steps": steps}

def tesla_check_charging_stations(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = _go_home() + [
        "Navigate to the 'Find Us' page.",
        f"Search for charging stations around '{city}'.",
        "List three charging stations found in this city."
    ]
    return {"task_type": "tesla_check_charging_stations", "city": city, "steps": steps}

def tesla_find_collision_centers(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = _go_home() + [
        "Go to the 'Support' section.",
        "Find the 'Collision Support' link and click it.",
        f"Locate a certified collision repair center near '{city}'.",
        "List the address and contact information for the first center found."
    ]
    return {"task_type": "tesla_find_collision_centers", "city": city, "steps": steps}

_TASK_GENERATORS: Dict[TESLA_TASK_TYPES, Callable[[dict], dict]] = {
    "tesla_model_purchase_flow": tesla_model_purchase_flow,
    "tesla_support_navigation": tesla_support_navigation,
    "tesla_test_drive_booking": tesla_test_drive_booking,
    "tesla_compare_models": tesla_compare_models,
    "tesla_view_solar_options": tesla_view_solar_options,
    "tesla_check_charging_stations": tesla_check_charging_stations,
    "tesla_find_collision_centers": tesla_find_collision_centers,
}

def generate_tesla_task(task_type: TESLA_TASK_TYPES, payload: dict) -> dict:
    t = _TASK_GENERATORS[task_type](payload or {})
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
    items = list(TESLA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_tesla_task, ttype, p))
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