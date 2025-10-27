import json, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

CARVANA_TASK_TYPES = Literal[
    "carvana_search_sort",
    "carvana_search_zip_sort",
    "carvana_compare_two_cars",
    "carvana_financing_info",
    "carvana_sell_estimate_area",
    "carvana_affordable_make_budget_year",
    "carvana_filter_owners_min",
    "carvana_filter_mileage_cap",
    "carvana_view_listing_details",
    "carvana_view_new_suvs",
]

CARVANA_SAMPLING_CONFIG: Dict[CARVANA_TASK_TYPES, int] = {
    "carvana_search_sort": 10,
    "carvana_search_zip_sort": 10,
    "carvana_compare_two_cars": 10,
    "carvana_financing_info": 10,
    "carvana_sell_estimate_area": 10,
    "carvana_affordable_make_budget_year": 10,
    "carvana_filter_owners_min": 10,
    "carvana_filter_mileage_cap": 10,
    "carvana_view_listing_details": 10,
    "carvana_view_new_suvs": 10,
}

ZIPS = ["98101", "94103", "90012", "60601", "10001", "75001", "80202", "30303", "02108", "73102", "85004", "19107", "97204", "20001", "33130", "27601", "55401", "15222", "64106", "95814"]
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
    return get_instruction("Carvana.com", steps).model_dump()

def _go_home() -> list[str]:
    return ["Go to url 'https://www.carvana.com/'.", *_ui()]

def carvana_search_sort(payload: dict) -> dict:
    car = payload.get("car", random.choice(CARS))
    sort = payload.get("sort", random.choice(FILTERS))
    steps = _go_home() + [
        f"Search for car '{car}'.",
        f"Apply sort/filter: {sort}.",
        "Open the first result and note price and mileage."
    ]
    return {"task_type": "carvana_search_sort", "car": car, "sort": sort, "steps": steps}

def carvana_search_zip_sort(payload: dict) -> dict:
    car = payload.get("car", random.choice(CARS))
    zipc = payload.get("zip", random.choice(ZIPS))
    sort = payload.get("sort", random.choice(FILTERS))
    steps = _go_home() + [
        f"Search for car '{car}'.",
        f"Set ZIP to '{zipc}'.",
        f"Apply sort/filter: {sort}.",
        "Open the first result and note price and mileage."
    ]
    return {"task_type": "carvana_search_zip_sort", "car": car, "zip": zipc, "sort": sort, "steps": steps}

def carvana_compare_two_cars(payload: dict) -> dict:
    a = payload.get("carA")
    b = payload.get("carB")
    if not (a and b): a, b = random.choice(COMPARE_EXAMPLES)
    steps = _go_home() + [
        "Use the Compare feature.",
        f"Add car A: '{a}'.",
        f"Add car B: '{b}'.",
        "Compare and list at least two differences such as price and features."
    ]
    return {"task_type": "carvana_compare_two_cars", "carA": a, "carB": b, "steps": steps}

def carvana_financing_info(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.carvana.com/financing'.",
        *_ui(),
        "Browse the available financing options.",
        "Note down a unique feature of Carvana's financing program."
    ]
    return {"task_type": "carvana_financing_info", "steps": steps}

def carvana_sell_estimate_area(payload: dict) -> dict:
    car = payload.get("car", "2018 Toyota Camry LE")
    area = payload.get("area", random.choice(ZIPS))
    steps = [
        "Go to url 'https://www.carvana.com/sell-my-car'.",
        *_ui(),
        f"Enter the details of '{car}' for valuation.",
        f"Use ZIP code '{area}' when prompted.",
        "Note the estimated value range shown."
    ]
    return {"task_type": "carvana_sell_estimate_area", "car": car, "area": area, "steps": steps}

def carvana_affordable_make_budget_year(payload: dict) -> dict:
    make = payload.get("make", "Toyota")
    budget = int(payload.get("budget", 20000))
    year_min = int(payload.get("year_min", 2020))
    steps = _go_home() + [
        "Visit the 'Search Cars' section.",
        f"Filter for Make='{make}', Year min={year_min}, and Max Price=${budget}.",
        "Record the first car's model, year, and price details."
    ]
    return {
        "task_type": "carvana_affordable_make_budget_year",
        "make": make,
        "budget": budget,
        "year_min": year_min,
        "steps": steps
    }

def carvana_filter_owners_min(payload: dict) -> dict:
    owners = int(payload.get("min_owners", 1))
    steps = _go_home() + [
        "Search for any car model.",
        "Open filter options and set to 'One owner' only.",
        "Apply filter and open first result, confirming owner history."
    ]
    return {"task_type": "carvana_filter_owners_min", "min_owners": owners, "steps": steps}

def carvana_filter_mileage_cap(payload: dict) -> dict:
    cap = int(payload.get("max_mileage", random.choice(MILEAGE_CAPS)))
    steps = _go_home() + [
        "Search for any car within a given area.",
        "Set filters to limit mileage to below the cap.",
        "Select first result and verify mileage is within cap."
    ]
    return {"task_type": "carvana_filter_mileage_cap", "max_mileage": cap, "steps": steps}

def carvana_view_listing_details(payload: dict) -> dict:
    car = payload.get("car", "Honda Civic")
    steps = _go_home() + [
        f"Find listing for '{car}'.",
        "View the first result’s details, ensuring to record price, mileage, and listing date."
    ]
    return {"task_type": "carvana_view_listing_details", "car": car, "steps": steps}

def carvana_view_new_suvs(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to 'SUVs'.",
        "Select the 'new arrivals' filter.",
        "Note details of two newly listed SUVs, including prices and year."
    ]
    return {"task_type": "carvana_view_new_suvs", "steps": steps}

_TASK_GENERATORS: Dict[CARVANA_TASK_TYPES, Callable[[dict], dict]] = {
    "carvana_search_sort": carvana_search_sort,
    "carvana_search_zip_sort": carvana_search_zip_sort,
    "carvana_compare_two_cars": carvana_compare_two_cars,
    "carvana_financing_info": carvana_financing_info,
    "carvana_sell_estimate_area": carvana_sell_estimate_area,
    "carvana_affordable_make_budget_year": carvana_affordable_make_budget_year,
    "carvana_filter_owners_min": carvana_filter_owners_min,
    "carvana_filter_mileage_cap": carvana_filter_mileage_cap,
    "carvana_view_listing_details": carvana_view_listing_details,
    "carvana_view_new_suvs": carvana_view_new_suvs,
}

def generate_carvana_task(task_type: CARVANA_TASK_TYPES, payload: dict) -> dict:
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
    items = list(CARVANA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_carvana_task, ttype, p))
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