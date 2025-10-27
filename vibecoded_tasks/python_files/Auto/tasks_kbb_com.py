import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

KBB_TASK_TYPES = Literal[
    "kbb_search_vehicle",
    "kbb_estimate_car_value",
    "kbb_find_dealer",
    "kbb_comparison_tool",
    "kbb_vehicle_history_check",
    "kbb_new_car_quote",
    "kbb_browse_top_cars",
]

KBB_SAMPLING_CONFIG: Dict[KBB_TASK_TYPES, int] = {
    "kbb_search_vehicle": 10,
    "kbb_estimate_car_value": 10,
    "kbb_find_dealer": 10,
    "kbb_comparison_tool": 10,
    "kbb_vehicle_history_check": 10,
    "kbb_new_car_quote": 10,
    "kbb_browse_top_cars": 10,
}

CITIES = ["Seattle, WA", "San Francisco, CA", "Los Angeles, CA", "Chicago, IL", "New York, NY", "Dallas, TX"]
VEHICLE_TYPES = ["SUV", "Truck", "Sedan", "Coupe", "Convertible"]
MAKES = ["Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "BMW"]
ZIP_CODES = ["98101", "94103", "90012", "60601", "10001", "75001"]

def _ui() -> list[str]:
    return ["Dismiss popups/cookies if shown.", "Do not submit personal info; only browse/read."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("KBB.com", steps).model_dump()

def _go_home() -> list[str]:
    return ["Go to url 'https://www.kbb.com/'.", *_ui()]

def kbb_search_vehicle(payload: dict) -> dict:
    vehicle_type = payload.get("vehicle_type", random.choice(VEHICLE_TYPES))
    make = payload.get("make", random.choice(MAKES))
    steps = _go_home() + [
        f"Navigate to 'Cars for Sale'.",
        f"Filter results by Vehicle Type '{vehicle_type}' and Make '{make}'.",
        "Open the first vehicle listing and record the price and mileage."
    ]
    return {"task_type": "kbb_search_vehicle", "vehicle_type": vehicle_type, "make": make, "steps": steps}

def kbb_estimate_car_value(payload: dict) -> dict:
    model = payload.get("model", "Toyota Camry")
    year = payload.get("year", 2020)
    steps = [
        "Go to url 'https://www.kbb.com/whats-my-car-worth/'.",
        *_ui(),
        f"Enter vehicle model '{model}' and year '{year}'.",
        "Submit the form and note the estimated value range displayed."
    ]
    return {"task_type": "kbb_estimate_car_value", "model": model, "year": year, "steps": steps}

def kbb_find_dealer(payload: dict) -> dict:
    city = payload.get("city", random.choice(CITIES))
    steps = _go_home() + [
        "Navigate to 'Find Local Dealers'.",
        f"Search for dealers in city '{city}'.",
        "Select the first dealer and confirm address and contact details are displayed."
    ]
    return {"task_type": "kbb_find_dealer", "city": city, "steps": steps}

def kbb_comparison_tool(payload: dict) -> dict:
    a = payload.get("carA", "Toyota Camry")
    b = payload.get("carB", "Honda Accord")
    steps = _go_home() + [
        "Navigate to 'Compare Cars'.",
        f"Enter '{a}' as Car A and '{b}' as Car B.",
        "Perform the comparison and list two spec differences."
    ]
    return {"task_type": "kbb_comparison_tool", "carA": a, "carB": b, "steps": steps}

def kbb_vehicle_history_check(payload: dict) -> dict:
    vin = payload.get("vin", "sampleVIN123456789")
    steps = [
        "Go to url 'https://www.kbb.com/vehicle-history-report/'.",
        *_ui(),
        f"Enter the VIN '{vin}' and submit.",
        "Verify that the vehicle history report summary is displayed."
    ]
    return {"task_type": "kbb_vehicle_history_check", "vin": vin, "steps": steps}

def kbb_new_car_quote(payload: dict) -> dict:
    make = payload.get("make", random.choice(MAKES))
    steps = _go_home() + [
        "Navigate to 'Free Dealer Price Quote'.",
        f"Request a quote for make '{make}'.",
        "Ensure a confirmation or error message is displayed."
    ]
    return {"task_type": "kbb_new_car_quote", "make": make, "steps": steps}

def kbb_browse_top_cars(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to 'Best Cars'.",
        "Browse through the top car categories.",
        "Open a top car listing and verify the specifications listed."
    ]
    return {"task_type": "kbb_browse_top_cars", "steps": steps}

_TASK_GENERATORS: Dict[KBB_TASK_TYPES, Callable[[dict], dict]] = {
    "kbb_search_vehicle": kbb_search_vehicle,
    "kbb_estimate_car_value": kbb_estimate_car_value,
    "kbb_find_dealer": kbb_find_dealer,
    "kbb_comparison_tool": kbb_comparison_tool,
    "kbb_vehicle_history_check": kbb_vehicle_history_check,
    "kbb_new_car_quote": kbb_new_car_quote,
    "kbb_browse_top_cars": kbb_browse_top_cars,
}

def generate_kbb_task(task_type: KBB_TASK_TYPES, payload: dict) -> dict:
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
    items = list(KBB_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_kbb_task, ttype, p))
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