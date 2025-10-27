import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

PARKERS_TASK_TYPES = Literal[
    "parkers_car_search_sort",
    "parkers_van_search",
    "parkers_compare_cars",
    "parkers_review_navigation",
    "parkers_get_car_valuation",
    "parkers_find_new_used_car",
    "parkers_navigation_assessment"
]

PARKERS_SAMPLING_CONFIG: Dict[PARKERS_TASK_TYPES, int] = {
    "parkers_car_search_sort": 10,
    "parkers_van_search": 10,
    "parkers_compare_cars": 10,
    "parkers_review_navigation": 10,
    "parkers_get_car_valuation": 10,
    "parkers_find_new_used_car": 10,
    "parkers_navigation_assessment": 10,
}

CAR_MAKES = [
    "Abarth", "AC", "Aixam", "Alfa Romeo", "Alpine", "Asia",
    "Aston Martin", "Audi", "Austin", "BAC", "Bentley", "BMW", 
    "BYD", "Cadillac", "Changan", "Chevrolet", "Citroen", "Dacia",
    "Dodge", "Fiat", "Ford", "Honda", "Hyundai", "Jaguar", "Jeep", 
    "Kia", "Land Rover", "Lexus", "Mazda", "Mercedes-Benz", "Nissan",
    "Peugeot", "Porsche", "Renault", "Skoda", "Tesla", "Toyota", 
    "Volkswagen", "Volvo"
]
CAR_MODELS = ["Sedan", "Hatchback", "SUV", "Convertible", "Van", "Truck"]

def _ui() -> list[str]:
    return ["Dismiss popups/cookies if shown.", "Do not submit personal info; only browse/read."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Parkers.co.uk", steps).model_dump()

def parkers_car_search_sort(payload: dict) -> dict:
    make = payload.get("make", random.choice(CAR_MAKES))
    model = random.choice(CAR_MODELS)
    sort = payload.get("sort", random.choice(["price low to high", "price high to low"]))
    steps = [
        "Go to url 'https://www.parkers.co.uk/cars-for-sale/'.",
        *_ui(),
        f"Select make '{make}'.",
        f"Choose model '{model}'.",
        f"Apply sort: {sort}.",
        "Verify the sorting is correct by checking the first car listing."
    ]
    return {"task_type": "parkers_car_search_sort", "make": make, "model": model, "sort": sort, "steps": steps}

def parkers_van_search(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.parkers.co.uk/vans-pickups/'.",
        *_ui(),
        "Select option to filter by 'Vans & Pickups'.",
        "Record details of the first van listed, including make, model, and price.",
        "Check if cargo capacity details are available."
    ]
    return {"task_type": "parkers_van_search", "steps": steps}

def parkers_compare_cars(payload: dict) -> dict:
    car_a, car_b = random.choices(CAR_MAKES, k=2)
    steps = [
        "Go to url 'https://www.parkers.co.uk/compare-cars/'.",
        *_ui(),
        f"Select car A: '{car_a}'.",
        f"Select car B: '{car_b}'.",
        "Run comparison and list two spec differences, e.g., horsepower, fuel consumption."
    ]
    return {"task_type": "parkers_compare_cars", "carA": car_a, "carB": car_b, "steps": steps}

def parkers_review_navigation(_: dict) -> dict:
    car_brand = random.choice(CAR_MAKES)
    steps = [
        "Go to url 'https://www.parkers.co.uk/car-reviews/'.",
        *_ui(),
        f"Search for reviews on brand '{car_brand}'.",
        "Open the first review result.",
        "Confirm details in the review, such as ratings and key highlights."
    ]
    return {"task_type": "parkers_review_navigation", "brand": car_brand, "steps": steps}

def parkers_get_car_valuation(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.parkers.co.uk/car-valuation/'.",
        *_ui(),
        "Enter car details: Make 'Toyota', Model 'Camry', Year '2018'.",
        "Complete the valuation form and retrieve the estimated price.",
        "Verify the valuation is displayed on the page."
    ]
    return {"task_type": "parkers_get_car_valuation", "steps": steps}

def parkers_find_new_used_car(payload: dict) -> dict:
    make = payload.get("make", random.choice(CAR_MAKES))
    car_type = payload.get("type", random.choice(["new", "used"]))
    steps = [
        "Go to url 'https://www.parkers.co.uk/cars-for-sale/'.",
        *_ui(),
        f"Filter by {car_type} cars.",
        f"Search for car make '{make}'.",
        "Open first car detail page and record car details such as price and mileage."
    ]
    return {"task_type": "parkers_find_new_used_car", "make": make, "type": car_type, "steps": steps}

def parkers_navigation_assessment(_: dict) -> dict:
    steps = [
        "Go to main url 'https://www.parkers.co.uk/'.",
        *_ui(),
        "Navigate to 'Vans & Pickups' section.",
        "Return back to main page.",
        "Navigate to 'Reviews' section and verify the page loads correctly."
    ]
    return {"task_type": "parkers_navigation_assessment", "steps": steps}

_TASK_GENERATORS: Dict[PARKERS_TASK_TYPES, Callable[[dict], dict]] = {
    "parkers_car_search_sort": parkers_car_search_sort,
    "parkers_van_search": parkers_van_search,
    "parkers_compare_cars": parkers_compare_cars,
    "parkers_review_navigation": parkers_review_navigation,
    "parkers_get_car_valuation": parkers_get_car_valuation,
    "parkers_find_new_used_car": parkers_find_new_used_car,
    "parkers_navigation_assessment": parkers_navigation_assessment,
}

def generate_parkers_task(task_type: PARKERS_TASK_TYPES, payload: dict) -> dict:
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
    items = list(PARKERS_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_parkers_task, ttype, p))
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