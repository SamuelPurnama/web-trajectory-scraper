import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

AUTOTRADER_TASK_TYPES = Literal[
    "autotrader_search_sort",
    "autotrader_filter_owners_min",
    "autotrader_compare_two_cars",
    "autotrader_view_listing_details",
    "autotrader_contact_support",
    "autotrader_search_certified_preowned",
    "autotrader_search_zip"
]

AUTOTRADER_SAMPLING_CONFIG: Dict[AUTOTRADER_TASK_TYPES, int] = {
    "autotrader_search_sort": 10,
    "autotrader_filter_owners_min": 10,
    "autotrader_compare_two_cars": 10,
    "autotrader_view_listing_details": 10,
    "autotrader_contact_support": 10,
    "autotrader_search_certified_preowned": 10,
    "autotrader_search_zip": 10
}

ZIPS = ["98101","94103","90012","60601","10001","75001","80202","30303","02108","73102","85004","19107","97204","20001","33130","27601","55401","15222","64106","95814"]
FILTERS = [
    "price: high to low",
    "price: low to high",
    "mileage: low to high",
    "year: newest",
    "exterior: white",
    "exterior: black",
    "body style: SUV",
    "certified pre-owned"
]
CARS = [
    "Tesla Model 3","Tesla Model Y","BMW i3","BMW 3 Series","Mercedes-Benz CLA","Mercedes-Benz C-Class",
    "Toyota Prius","Toyota Camry","Toyota Corolla","Toyota RAV4","Toyota Highlander","Toyota 4Runner",
    "Honda Civic","Honda Accord","Honda CR-V","Subaru Outback","Subaru Forester","Ford F-150","Ford Mustang",
    "Chevrolet Bolt EUV","Chevrolet Silverado 1500","Nissan Leaf","Nissan Rogue","Hyundai Ioniq 5","Hyundai Elantra",
    "Kia Niro","Kia Sportage","Volkswagen Golf","Volvo XC60","Audi A4","Mazda CX-5","Porsche Macan"
]
COMPARE_EXAMPLES = [
    ("Toyota Camry 2021","Honda Accord 2021"),
    ("Subaru Outback 2020","Toyota RAV4 2020"),
    ("Tesla Model 3 2022","BMW i3 2022"),
    ("Ford F-150 2021","Chevrolet Silverado 1500 2021"),
    ("BMW 3 Series 2020","Audi A4 2020"),
]

MILEAGE_CAPS = [20000,30000,40000,60000,80000]
MAKES = ["Toyota","Honda","Subaru","Hyundai","Kia","Ford","Chevrolet","Nissan","BMW","Mercedes-Benz"]

def _ui() -> list[str]:
    return ["Dismiss popups/cookies if shown.","Do not submit personal info; only browse/read."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Autotrader.com", steps).model_dump()

def _go_home() -> list[str]:
    return ["Go to url 'https://www.autotrader.com/'.", *_ui()]

def autotrader_search_sort(payload: dict) -> dict:
    car = payload.get("car", random.choice(CARS))
    sort = payload.get("sort", random.choice(FILTERS))
    steps = _go_home() + [
        f"Search for car '{car}'.",
        f"Apply sort/filter: {sort}.",
        "Open the first result and note price and mileage."
    ]
    return {"task_type":"autotrader_search_sort","car":car,"sort":sort,"steps":steps}

def autotrader_filter_owners_min(payload: dict) -> dict:
    owners = int(payload.get("min_owners", 1))
    steps = _go_home() + [
        "Run a general search.",
        "Open filters.",
        f"Enable '{owners}-Owner' filter.",
        "Apply filters and open first result; confirm owner count in history."
    ]
    return {"task_type":"autotrader_filter_owners_min","min_owners":owners,"steps":steps}

def autotrader_compare_two_cars(payload: dict) -> dict:
    a, b = payload.get("carA"), payload.get("carB")
    if not (a and b): a, b = random.choice(COMPARE_EXAMPLES)
    steps = _go_home() + [
        "Open the 'Compare' tool.",
        f"Add vehicle A: '{a}'.",
        f"Add vehicle B: '{b}'.",
        "Run compare and list two differences (e.g., horsepower, MPG)."
    ]
    return {"task_type":"autotrader_compare_two_cars","carA":a,"carB":b,"steps":steps}

def autotrader_view_listing_details(payload: dict) -> dict:
    car = payload.get("car","Honda Civic")
    steps = _go_home() + [
        f"Search for '{car}'.",
        "Open the first result.",
        "Record trim, mileage, price, dealer name, and any accident-history badge."
    ]
    return {"task_type":"autotrader_view_listing_details","car":car,"steps":steps}

def autotrader_contact_support(_: dict) -> dict:
    steps = _go_home() + [
        "Navigate to 'contact our support team'.",
        "Verify you are on the support page by checking for a support text.",
    ]
    return {"task_type":"autotrader_contact_support","steps":steps}

def autotrader_search_certified_preowned(payload: dict) -> dict:
    car = payload.get("car", random.choice(CARS))
    steps = _go_home() + [
        "Open filters and select 'Certified Pre-Owned'.",
        f"Search for '{car}'.",
        "Open the first result and check for certification details."
    ]
    return {"task_type":"autotrader_search_certified_preowned","car":car,"steps":steps}

def autotrader_search_zip(payload: dict) -> dict:
    zipc = payload.get("zip", random.choice(ZIPS))
    car = payload.get("car", random.choice(CARS))
    steps = _go_home() + [
        f"Set search ZIP to '{zipc}'.",
        f"Search for car '{car}'.",
        "Open first result and verify it's near given ZIP."
    ]
    return {"task_type":"autotrader_search_zip","zip":zipc,"car":car,"steps":steps}

_TASK_GENERATORS: Dict[AUTOTRADER_TASK_TYPES, Callable[[dict], dict]] = {
    "autotrader_search_sort": autotrader_search_sort,
    "autotrader_filter_owners_min": autotrader_filter_owners_min,
    "autotrader_compare_two_cars": autotrader_compare_two_cars,
    "autotrader_view_listing_details": autotrader_view_listing_details,
    "autotrader_contact_support": autotrader_contact_support,
    "autotrader_search_certified_preowned": autotrader_search_certified_preowned,
    "autotrader_search_zip": autotrader_search_zip,
}

def generate_autotrader_task(task_type: AUTOTRADER_TASK_TYPES, payload: dict) -> dict:
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
    items = list(AUTOTRADER_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_autotrader_task, ttype, p))
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