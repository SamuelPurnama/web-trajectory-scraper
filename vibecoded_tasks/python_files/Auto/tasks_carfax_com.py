import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

CARFAX_TASK_TYPES = Literal[
    "carfax_search_vehicle",
    "carfax_view_history_report",
    "carfax_service_shop_search",
    "carfax_check_used_car_value",
    "carfax_research_vehicle",
    "carfax_get_cash_offer",
    "carfax_estimate_car_value",
    "carfax_check_recall",
    "carfax_partner_with_carfax",
]

CARFAX_SAMPLING_CONFIG: Dict[CARFAX_TASK_TYPES, int] = {
    "carfax_search_vehicle": 10,
    "carfax_view_history_report": 10,
    "carfax_service_shop_search": 10,
    "carfax_check_used_car_value": 10,
    "carfax_research_vehicle": 10,
    "carfax_get_cash_offer": 10,
    "carfax_estimate_car_value": 10,
    "carfax_check_recall": 10,
    "carfax_partner_with_carfax": 10,
}

ZIPS = [
    "98101", "94103", "90012", "60601", "10001", "75001", "80202", "30303",
    "02108", "73102", "85004", "19107", "97204", "20001", "33130", "27601",
    "55401", "15222", "64106", "95814"
]

VEHICLE_URLS = [
    "https://www.carfax.com/Used-Chevrolet_m6",
    "https://www.carfax.com/New-Toyota_m33",
    "https://www.carfax.com/Used-Jeep-Grand-Cherokee_w373",
    "https://www.carfax.com/New-Ford-F-150_w236",
    "https://www.carfax.com/Used-Tesla-Model-Y_w9761"
]

VEHICLE_MODELS = [
    "Chevrolet Malibu", "Toyota Camry", "Jeep Grand Cherokee",
    "Ford F-150", "Tesla Model Y"
]

FILTERS = [
    "price: high to low", "price: low to high", "mileage: low to high",
    "year: newest", "body style: SUV", "fuel: electric"
]

def _ui() -> list[str]:
    return ["Dismiss popups/cookies if shown.", "Do not submit personal info; only browse/read."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Carfax", steps).model_dump()

def _go_home() -> list[str]:
    return ["Go to url 'https://www.carfax.com'.", *_ui()]

def carfax_search_vehicle(payload: dict) -> dict:
    model = payload.get("model", random.choice(VEHICLE_MODELS))
    steps = _go_home() + [
        f"Search for vehicle '{model}'.",
        f"Apply sort/filter: {random.choice(FILTERS)}.",
        f"Open the first result from the search."
    ]
    return {"task_type": "carfax_search_vehicle", "model": model, "steps": steps}

def carfax_view_history_report(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.carfax.com/vehicle-history-reports/'.",
        *_ui(),
        "Choose a random vehicle report demo.",
        "View and note the available history details."
    ]
    return {"task_type": "carfax_view_history_report", "steps": steps}

def carfax_service_shop_search(payload: dict) -> dict:
    zip_code = payload.get("zip", random.choice(ZIPS))
    steps = _go_home() + [
        "Navigate to 'Find a Service Shop'.",
        f"Enter ZIP code '{zip_code}' and search.",
        "Open first shop detail and record shop name and services."
    ]
    return {"task_type": "carfax_service_shop_search", "zip": zip_code, "steps": steps}

def carfax_check_used_car_value(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to 'Used Car Values'.",
        "Enter details for a 2015 Honda Civic.",
        "Note the estimated value range provided for the vehicle."
    ]
    return {"task_type": "carfax_check_used_car_value", "steps": steps}

def carfax_research_vehicle(payload: dict) -> dict:
    vehicle_url = payload.get("url", random.choice(VEHICLE_URLS))
    steps = _go_home() + [
        f"Visit the car research page '{vehicle_url}'.",
        "Read through the vehicle details provided.",
        "Note key features such as performance and safety ratings."
    ]
    return {"task_type": "carfax_research_vehicle", "url": vehicle_url, "steps": steps}

def carfax_get_cash_offer(payload: dict) -> dict:
    car = payload.get("car", "2018 Ford Mustang GT")
    steps = [
        "Go to 'Get Cash Offers'.",
        *_ui(),
        f"Proceed with a cash offer valuation for '{car}'.",
        "Record the first cash offer range displayed."
    ]
    return {"task_type": "carfax_get_cash_offer", "car": car, "steps": steps}

def carfax_estimate_car_value(payload: dict) -> dict:
    car = payload.get("car", "2018 Toyota Corolla")
    area = payload.get("area", random.choice(ZIPS))
    steps = _go_home() + [
        "Navigate to 'Used Car Values'.",
        f"Search for estimated value of '{car}'.",
        f"Enter ZIP code '{area}' to refine results.",
        "Record the estimated value range displayed."
    ]
    return {"task_type": "carfax_estimate_car_value", "car": car, "area": area, "steps": steps}

def carfax_check_recall(payload: dict) -> dict:
    model = payload.get("model", "Ford F-150" )
    steps = _go_home() + [
        "Click on 'Recalls'.",
        f"Search for recalls applicable for '{model}'.",
        "Note any recalls or important notices listed."
    ]
    return {"task_type": "carfax_check_recall", "model": model, "steps": steps}

def carfax_partner_with_carfax(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to 'Partner with CARFAX'.",
        "Read through the partnership opportunities available.",
        "Note any requirements or benefits listed for partners."
    ]
    return {"task_type": "carfax_partner_with_carfax", "steps": steps}

_TASK_GENERATORS: Dict[CARFAX_TASK_TYPES, Callable[[dict], dict]] = {
    "carfax_search_vehicle": carfax_search_vehicle,
    "carfax_view_history_report": carfax_view_history_report,
    "carfax_service_shop_search": carfax_service_shop_search,
    "carfax_check_used_car_value": carfax_check_used_car_value,
    "carfax_research_vehicle": carfax_research_vehicle,
    "carfax_get_cash_offer": carfax_get_cash_offer,
    "carfax_estimate_car_value": carfax_estimate_car_value,
    "carfax_check_recall": carfax_check_recall,
    "carfax_partner_with_carfax": carfax_partner_with_carfax,
}

def generate_carfax_task(task_type: CARFAX_TASK_TYPES, payload: dict) -> dict:
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
    items = list(CARFAX_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_carfax_task, ttype, p))
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