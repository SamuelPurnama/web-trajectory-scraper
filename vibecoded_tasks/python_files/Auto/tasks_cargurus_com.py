import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

CARGURUS_TASK_TYPES = Literal[
    "cargurus_search_sort",
    "cargurus_search_zip_sort",
    "cargurus_find_large_van",
    "cargurus_compare_two_cars",
    "cargurus_financing_info",
    "cargurus_sell_estimate_area",
    "cargurus_affordable_make_budget_year",
    "cargurus_filter_owners_min",
    "cargurus_filter_mileage_cap",
]

CARGURUS_SAMPLING_CONFIG: Dict[CARGURUS_TASK_TYPES, int] = {
    "cargurus_search_sort": 10,
    "cargurus_search_zip_sort": 10,
    "cargurus_find_large_van": 10,
    "cargurus_compare_two_cars": 10,
    "cargurus_financing_info": 10,
    "cargurus_sell_estimate_area": 10,
    "cargurus_affordable_make_budget_year": 10,
    "cargurus_filter_owners_min": 10,
    "cargurus_filter_mileage_cap": 10,
}

ZIPS = ["98101", "94103", "90012", "60601", "10001", "75001", "80202", "30303", "02108", "73102",
        "85004", "19107", "97204", "20001", "33130", "27601", "55401", "15222", "64106", "95814"]
FILTERS = [
    "price: high to low",
    "price: low to high",
    "mileage: low to high",
    "year: newest",
    "exterior: white",
    "drivetrain: AWD/4WD",
    "fuel: electric",
    "transmission: automatic",
    "body style: SUV",
    "certified pre-owned",
]
CARS = [
    "Tesla Model 3", "Tesla Model Y", "BMW i3", "BMW 3 Series", "Mercedes-Benz CLA", "Mercedes-Benz C-Class",
    "Toyota Prius", "Toyota Camry", "Toyota Corolla", "Toyota RAV4", "Toyota Highlander", "Toyota 4Runner",
    "Honda Civic", "Honda Accord", "Honda CR-V", "Subaru Outback", "Subaru Forester", "Ford F-150", "Ford Mustang",
    "Chevrolet Bolt EUV", "Chevrolet Silverado 1500", "Nissan Leaf", "Nissan Rogue", "Hyundai Ioniq 5", "Hyundai Elantra",
    "Kia Niro", "Kia Sportage", "Volkswagen Golf", "Volvo XC60", "Audi A4", "Mazda CX-5", "Porsche Macan"
]
COMPARE_EXAMPLES = [
    ("Toyota Camry 2021", "Honda Accord 2021"),
    ("Subaru Outback 2020", "Toyota RAV4 2020"),
    ("Tesla Model 3 2022", "Polestar 2 2022"),
    ("Ford F-150 2021", "Chevrolet Silverado 1500 2021"),
    ("BMW 3 Series 2020", "Audi A4 2020"),
    ("Hyundai Ioniq 5 2023", "Kia Niro 2023"),
    ("Mazda CX-5 2021", "Honda CR-V 2021"),
    ("Volvo XC60 2022", "Mercedes-Benz GLC 2022"),
]
MILEAGE_CAPS = [20000, 30000, 40000, 60000, 80000]
BUDGETS = [15000, 20000, 25000, 30000]
MAKES = ["Toyota", "Honda", "Subaru", "Hyundai", "Kia", "Ford", "Chevrolet", "Nissan", "BMW", "Mercedes-Benz"]

def _ui() -> list[str]:
    return ["Dismiss popups/cookies if shown.", "Do not submit personal info; only browse/read."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("CarGurus.com", steps).model_dump()

def _go_home() -> list[str]:
    return ["Go to url 'https://www.cargurus.com/'.", *_ui()]

def cargurus_search_sort(payload: dict) -> dict:
    car = payload.get("car", random.choice(CARS))
    sort = payload.get("sort", random.choice(FILTERS))
    steps = _go_home() + [
        f"Search for car '{car}'.",
        f"Apply sort/filter: {sort}.",
        "Open the first result and note price and mileage."
    ]
    return {"task_type": "cargurus_search_sort", "car": car, "sort": sort, "steps": steps}

def cargurus_search_zip_sort(payload: dict) -> dict:
    car = payload.get("car", random.choice(CARS))
    zipc = payload.get("zip", random.choice(ZIPS))
    sort = payload.get("sort", random.choice(FILTERS))
    steps = _go_home() + [
        f"Search for car '{car}'.",
        f"Set location ZIP to '{zipc}'.",
        f"Apply sort/filter: {sort}.",
        "Open the first result and note price and mileage."
    ]
    return {"task_type": "cargurus_search_zip_sort", "car": car, "zip": zipc, "sort": sort, "steps": steps}

def cargurus_find_large_van(_: dict) -> dict:
    steps = _go_home() + [
        "Open filters and choose Body Style 'Van' (Full-size if available).",
        "Apply filters.",
        "Open a result and record passenger/cargo capacity and price."
    ]
    return {"task_type": "cargurus_find_large_van", "steps": steps}

def cargurus_compare_two_cars(payload: dict) -> dict:
    a = payload.get("carA")
    b = payload.get("carB")
    if not (a and b): a, b = random.choice(COMPARE_EXAMPLES)
    steps = _go_home() + [
        "Open the 'Compare' tool.",
        f"Add vehicle A: '{a}'.",
        f"Add vehicle B: '{b}'.",
        "Run comparison and list two differences (e.g., horsepower, MPG, cargo)."
    ]
    return {"task_type": "cargurus_compare_two_cars", "carA": a, "carB": b, "steps": steps}

def cargurus_financing_info(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.cargurus.com/finance'.",
        *_ui(),
        "Navigate to the 'Auto Loan Calculator'.",
        "Enter details: price $25,000; down $3,000; APR 6%; term 60 months.",
        "Record the estimated monthly payment."
    ]
    return {"task_type": "cargurus_financing_info", "steps": steps}

def cargurus_sell_estimate_area(payload: dict) -> dict:
    car = payload.get("car", "2018 Toyota Camry LE")
    area = payload.get("area", random.choice(ZIPS))
    steps = [
        "Go to url 'https://www.cargurus.com/sell-car/'.",
        *_ui(),
        f"Use the valuation tool for '{car}'.",
        f"Provide ZIP '{area}' when requested.",
        "Capture the initial estimated value range displayed."
    ]
    return {"task_type": "cargurus_sell_estimate_area", "car": car, "area": area, "steps": steps}

def cargurus_affordable_make_budget_year(payload: dict) -> dict:
    make = payload.get("make", "Toyota")
    budget = int(payload.get("budget", random.choice(BUDGETS)))
    year_min = int(payload.get("year_min", 2020))
    steps = _go_home() + [
        f"Set Make='{make}'.",
        "Access filters section.",
        f"Set minimum Year to {year_min}.",
        f"Set Maximum Price to ${budget}.",
        "Apply filters.",
        "Open the first listing and note model, year, and price."
    ]
    return {"task_type": "cargurus_affordable_make_budget_year", "make": make, "budget": budget, "year_min": year_min, "steps": steps}

def cargurus_filter_owners_min(payload: dict) -> dict:
    owners = int(payload.get("min_owners", 1))
    steps = _go_home() + [
        "Perform a general search in any ZIP code.",
        "Apply filters.",
        f"Select '{owners}-Owner' (or One owner) filter.",
        "Apply filters; open first result to verify owner history."
    ]
    return {"task_type": "cargurus_filter_owners_min", "min_owners": owners, "steps": steps}

def cargurus_filter_mileage_cap(payload: dict) -> dict:
    cap = int(payload.get("max_mileage", random.choice(MILEAGE_CAPS)))
    steps = _go_home() + [
        "Perform a general search for any car model.",
        "Open the filters menu.",
        f"Set a maximum mileage of ≤ {cap}.",
        "Apply filters and verify that the first result matches the criteria."
    ]
    return {"task_type": "cargurus_filter_mileage_cap", "max_mileage": cap, "steps": steps}

_TASK_GENERATORS: Dict[CARGURUS_TASK_TYPES, Callable[[dict], dict]] = {
    "cargurus_search_sort": cargurus_search_sort,
    "cargurus_search_zip_sort": cargurus_search_zip_sort,
    "cargurus_find_large_van": cargurus_find_large_van,
    "cargurus_compare_two_cars": cargurus_compare_two_cars,
    "cargurus_financing_info": cargurus_financing_info,
    "cargurus_sell_estimate_area": cargurus_sell_estimate_area,
    "cargurus_affordable_make_budget_year": cargurus_affordable_make_budget_year,
    "cargurus_filter_owners_min": cargurus_filter_owners_min,
    "cargurus_filter_mileage_cap": cargurus_filter_mileage_cap,
}

def generate_cargurus_task(task_type: CARGURUS_TASK_TYPES, payload: dict) -> dict:
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
    items = list(CARGURUS_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_cargurus_task, ttype, p))
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