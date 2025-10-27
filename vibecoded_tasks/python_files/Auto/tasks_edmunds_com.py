import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

EDMUNDS_TASK_TYPES = Literal[
    "edmunds_vehicle_search",
    "edmunds_car_value_estimate",
    "edmunds_compare_vehicles",
    "edmunds_browse_car_videos",
    "edmunds_car_reviews",
    "edmunds_find_dealers",
    "edmunds_maintenance_cost"
]

EDMUNDS_SAMPLING_CONFIG: Dict[EDMUNDS_TASK_TYPES, int] = {
    "edmunds_vehicle_search": 10,
    "edmunds_car_value_estimate": 10,
    "edmunds_compare_vehicles": 10,
    "edmunds_browse_car_videos": 10,
    "edmunds_car_reviews": 10,
    "edmunds_find_dealers": 10,
    "edmunds_maintenance_cost": 10,
}

VEHICLES = ["Tesla Model 3", "BMW 3 Series", "Toyota Camry", "Ford Mustang", "Honda Civic", "Hyundai Elantra"]
COMPARE_EXAMPLES = [("Tesla Model 3", "BMW i3"), ("Toyota Camry", "Honda Accord"), ("Ford F-150", "Chevrolet Silverado")]
ZIP_CODES = ["90001", "10001", "60601", "94103", "33101"]
BUDGETS = [15000, 20000, 30000, 40000]

def _ui() -> list[str]:
    return ["Dismiss popups/cookies if shown.", "Do not submit personal info; only browse/read."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Edmunds.com", steps).model_dump()

def _go_home() -> list[str]:
    return ["Go to url 'https://www.edmunds.com/'.", *_ui()]

def edmunds_vehicle_search(payload: dict) -> dict:
    vehicle = payload.get("vehicle", random.choice(VEHICLES))
    steps = _go_home() + [
        f"Search for '{vehicle}'.",
        "Open the first listing.",
        "Note price and key vehicle feature."
    ]
    return {"task_type": "edmunds_vehicle_search", "vehicle": vehicle, "steps": steps}

def edmunds_car_value_estimate(payload: dict) -> dict:
    vehicle = payload.get("vehicle", "2018 Toyota Camry LE")
    zip_code = payload.get("zip", random.choice(ZIP_CODES))
    steps = _go_home() + [
        "Navigate to Car Value section.",
        f"Enter vehicle: '{vehicle}'.",
        f"Enter ZIP: '{zip_code}'.",
        "Review the estimated value range."
    ]
    return {"task_type": "edmunds_car_value_estimate", "vehicle": vehicle, "zip": zip_code, "steps": steps}

def edmunds_compare_vehicles(payload: dict) -> dict:
    car_a, car_b = payload.get("car_a"), payload.get("car_b")
    if not (car_a and car_b): car_a, car_b = random.choice(COMPARE_EXAMPLES)
    steps = _go_home() + [
        "Navigate to Vehicle Comparison tool.",
        f"Select Vehicle A: '{car_a}'.",
        f"Select Vehicle B: '{car_b}'.",
        "Compare and list at least two differences."
    ]
    return {"task_type": "edmunds_compare_vehicles", "car_a": car_a, "car_b": car_b, "steps": steps}

def edmunds_browse_car_videos(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to Car Videos section.",
        "Select a video.",
        "Confirm video title matches the expected content."
    ]
    return {"task_type": "edmunds_browse_car_videos", "steps": steps}

def edmunds_car_reviews(payload: dict) -> dict:
    vehicle = payload.get("vehicle", random.choice(VEHICLES))
    steps = _go_home() + [
        f"Search for reviews of '{vehicle}'.",
        "Open the first review.",
        "Summarize the main points (pros/cons)."
    ]
    return {"task_type": "edmunds_car_reviews", "vehicle": vehicle, "steps": steps}

def edmunds_find_dealers(payload: dict) -> dict:
    zip_code = payload.get("zip", random.choice(ZIP_CODES))
    steps = _go_home() + [
        "Navigate to Find Dealers section.",
        f"Search using ZIP '{zip_code}'.",
        "List the first dealer's name and contact information."
    ]
    return {"task_type": "edmunds_find_dealers", "zip": zip_code, "steps": steps}

def edmunds_maintenance_cost(payload: dict) -> dict:
    vehicle = payload.get("vehicle", "Honda Civic")
    steps = _go_home() + [
        "Navigate to Car Maintenance Cost section.",
        f"Enter '{vehicle}' and confirm predictions.",
        "Note key services and their estimated costs."
    ]
    return {"task_type": "edmunds_maintenance_cost", "vehicle": vehicle, "steps": steps}

_TASK_GENERATORS: Dict[EDMUNDS_TASK_TYPES, Callable[[dict], dict]] = {
    "edmunds_vehicle_search": edmunds_vehicle_search,
    "edmunds_car_value_estimate": edmunds_car_value_estimate,
    "edmunds_compare_vehicles": edmunds_compare_vehicles,
    "edmunds_browse_car_videos": edmunds_browse_car_videos,
    "edmunds_car_reviews": edmunds_car_reviews,
    "edmunds_find_dealers": edmunds_find_dealers,
    "edmunds_maintenance_cost": edmunds_maintenance_cost,
}

def generate_edmunds_task(task_type: EDMUNDS_TASK_TYPES, payload: dict) -> dict:
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
    items = list(EDMUNDS_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_edmunds_task, ttype, p))
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