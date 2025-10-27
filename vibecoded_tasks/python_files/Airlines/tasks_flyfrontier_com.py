import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

FRONTIER_TASK_TYPES = Literal[
    "frontier_book_vacation_package",
    "frontier_find_flight_deals",
    "frontier_check_flight_status",
    "frontier_view_bag_options",
    "frontier_manage_trip",
    "frontier_miles_faq",
    "frontier_find_where_we_fly",
    "frontier_insurance_info",
]

FRONTIER_SAMPLING_CONFIG: Dict[FRONTIER_TASK_TYPES, int] = {
    "frontier_book_vacation_package": 10,
    "frontier_find_flight_deals": 10,
    "frontier_check_flight_status": 10,
    "frontier_view_bag_options": 10,
    "frontier_manage_trip": 10,
    "frontier_miles_faq": 10,
    "frontier_find_where_we_fly": 10,
    "frontier_insurance_info": 10,
}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any initial pop-ups or banners.",
        "Ensure all form fields are reset to defaults before starting.",
    ]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def frontier_book_vacation_package(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flyfrontier.com/' and ensure the homepage is loaded.",
        *_ui_hygiene(),
        "Navigate to the 'Vacations' section.",
        "Initiate a vacation package search without specifying details.",
        "Simulate going through the process up to review stage without booking.",
    ]
    return {"task_type": "frontier_book_vacation_package", "steps": steps}

def frontier_find_flight_deals(_: dict) -> dict:
    steps = [
        "Go to url 'https://flights.flyfrontier.com/en/flight-deals'.",
        *_ui_hygiene(),
        "Browse the flight deals listed.",
        "Select any deal and verify its details.",
    ]
    return {"task_type": "frontier_find_flight_deals", "steps": steps}

def frontier_check_flight_status(_: dict) -> dict:
    flight_number = f"F9{random.randint(100, 999)}"
    date = _rand_date()
    steps = [
        "Go to url 'https://www.flyfrontier.com/flightStatus'.",
        *_ui_hygiene(),
        f"Enter the flight number '{flight_number}'.",
        f"Select any date (e.g., '{date}') and search.",
        "Verify if the flight information is retrieved successfully.",
    ]
    return {"task_type": "frontier_check_flight_status", "flight_number": flight_number, "date": date, "steps": steps}

def frontier_view_bag_options(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flyfrontier.com/travel/travel-info/bag-options/'.",
        *_ui_hygiene(),
        "Read and summarize the section on carry-on size/weight.",
        "Ensure the information is accurately listed on the homepage.",
    ]
    return {"task_type": "frontier_view_bag_options", "steps": steps}

def frontier_manage_trip(_: dict) -> dict:
    booking_code = f"ABC{random.randint(1000, 9999)}"
    last_name = "Smith"
    steps = [
        "Go to url 'https://www.flyfrontier.com/travel/my-trips/manage-trip/'.",
        *_ui_hygiene(),
        f"Use a fictional booking code '{booking_code}' and last name '{last_name}' to attempt retrieval.",
        "Verify appropriate error handling for invalid data.",
    ]
    return {"task_type": "frontier_manage_trip", "booking_code": booking_code, "last_name": last_name, "steps": steps}

def frontier_miles_faq(_: dict) -> dict:
    steps = [
        "Go to url 'https://faq.flyfrontier.com/help/frontiermiles'.",
        *_ui_hygiene(),
        "Navigate through the FAQ and find information about earning 'FRONTIER Miles'.",
    ]
    return {"task_type": "frontier_miles_faq", "steps": steps}

def frontier_find_where_we_fly(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flyfrontier.com/travel/my-trips/route-map/'.",
        *_ui_hygiene(),
        "Explore the interactive route map feature to identify any destination.",
    ]
    return {"task_type": "frontier_find_where_we_fly", "steps": steps}

def frontier_insurance_info(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.travelguard.com/frontierairlines/'.",
        *_ui_hygiene(),
        "Look for information on travel insurance options available.",
        "Summarize the key benefits.",
    ]
    return {"task_type": "frontier_insurance_info", "steps": steps}

_TASK_GENERATORS: Dict[FRONTIER_TASK_TYPES, Callable[[dict], dict]] = {
    "frontier_book_vacation_package": frontier_book_vacation_package,
    "frontier_find_flight_deals": frontier_find_flight_deals,
    "frontier_check_flight_status": frontier_check_flight_status,
    "frontier_view_bag_options": frontier_view_bag_options,
    "frontier_manage_trip": frontier_manage_trip,
    "frontier_miles_faq": frontier_miles_faq,
    "frontier_find_where_we_fly": frontier_find_where_we_fly,
    "frontier_insurance_info": frontier_insurance_info,
}

def generate_frontier_task(task_type: FRONTIER_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = get_instruction("Frontier", task["steps"]).model_dump()
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(FRONTIER_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_frontier_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)