import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

CARS_TASK_TYPES = Literal[
    "cars_search",
    "cars_filter_electric",
    "cars_filter_suv",
    "cars_compare_cars",
    "cars_calculate_loan",
    "cars_check_dealer",
    "cars_read_latest_news"
]

CARS_SAMPLING_CONFIG: Dict[CARS_TASK_TYPES, int] = {
    "cars_search": 10,
    "cars_filter_electric": 10,
    "cars_filter_suv": 10,
    "cars_compare_cars": 10,
    "cars_calculate_loan": 10,
    "cars_check_dealer": 10,
    "cars_read_latest_news": 10,
}

CAR_MODELS = ["Tesla Model 3", "Ford F-150", "Toyota Camry", "BMW 3 Series", "Honda Accord"]
CITY_CODES = ["Chicago", "Houston", "Los Angeles", "Phoenix", "Atlanta"]
MAX_PRICE = [20000, 30000, 40000, 50000, 60000]

def _rand_date(start_days=1, end_days=30) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or notifications (e.g., cookies consent, newsletter sign-ups).",
        "Do not fill any forms or input personal details; only navigate and view results.",
    ]

def _site_home() -> list[str]:
    return [
        "Go to url 'https://www.cars.com'.",
        "Ensure the homepage is loaded.",
        *_ui_hygiene(),
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Cars", steps).model_dump()

def cars_search(_: dict) -> dict:
    model = random.choice(CAR_MODELS)
    steps = _site_home() + [
        "Locate the search bar on the homepage.",
        f"Type '{model}' in the search bar and initiate the search.",
        "Confirm that the search results display listings related to the car model.",
    ]
    return {"task_type": "cars_search", "car_model": model, "steps": steps}

def cars_filter_electric(_: dict) -> dict:
    steps = _site_home() + [
        "Navigate to the 'New Cars' section.",
        "Select the filter for 'Electric Vehicles'.",
        "Ensure the results only display electric cars.",
    ]
    return {"task_type": "cars_filter_electric", "steps": steps}

def cars_filter_suv(_: dict) -> dict:
    steps = _site_home() + [
        "Navigate to the 'Cars for Sale' section.",
        "Apply the filter for 'SUV' under car types.",
        "Verify that results are filtered to display only SUVs.",
    ]
    return {"task_type": "cars_filter_suv", "steps": steps}

def cars_compare_cars(_: dict) -> dict:
    first_car, second_car = random.sample(CAR_MODELS, 2)
    steps = _site_home() + [
        "Navigate to the 'Compare Cars' section.",
        f"Select '{first_car}' and '{second_car}' for comparison.",
        "Review the displayed comparison criteria to assess differences.",
    ]
    return {"task_type": "cars_compare_cars", "first_car": first_car, "second_car": second_car, "steps": steps}

def cars_calculate_loan(_: dict) -> dict:
    price_cap = random.choice(MAX_PRICE)
    steps = _site_home() + [
        "Navigate to the 'Financing' section.",
        "Access the 'Car Loan Calculator'.",
        f"Set the car price to {price_cap} and calculate the estimated loan payments.",
        "Review the estimated monthly payment displayed.",
    ]
    return {"task_type": "cars_calculate_loan", "price_cap": price_cap, "steps": steps}

def cars_check_dealer(_: dict) -> dict:
    city = random.choice(CITY_CODES)
    steps = _site_home() + [
        "Go to the 'Find a Dealer' section.",
        f"Input '{city}' in the location search field to find dealers.",
        "Verify the list of dealers updated according to the specified city.",
    ]
    return {"task_type": "cars_check_dealer", "city": city, "steps": steps}

def cars_read_latest_news(_: dict) -> dict:
    steps = _site_home() + [
        "Navigate to the 'News & Videos' section.",
        "Select an article from the latest news.",
        "Ensure the article content is fully loaded and readable.",
    ]
    return {"task_type": "cars_read_latest_news", "steps": steps}

_TASK_GENERATORS: Dict[CARS_TASK_TYPES, Callable[[dict], dict]] = {
    "cars_search": cars_search,
    "cars_filter_electric": cars_filter_electric,
    "cars_filter_suv": cars_filter_suv,
    "cars_compare_cars": cars_compare_cars,
    "cars_calculate_loan": cars_calculate_loan,
    "cars_check_dealer": cars_check_dealer,
    "cars_read_latest_news": cars_read_latest_news,
}

def generate_cars_task(task_type: CARS_TASK_TYPES, payload: dict) -> dict:
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
    items = list(CARS_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_cars_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception as e: print(e)
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)