import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

LUFTHANSA_TASK_TYPES = Literal[
    "lufthansa_one_way_search",
    "lufthansa_round_trip_search",
    "lufthansa_filter_nonstop",
    "lufthansa_filter_cabin",
    "lufthansa_sort_lowest",
    "lufthansa_price_cap",
    "lufthansa_time_window_filter",
    "lufthansa_fare_details",
]

LUFTHANSA_SAMPLING_CONFIG: Dict[LUFTHANSA_TASK_TYPES, int] = {
    "lufthansa_one_way_search": 10,
    "lufthansa_round_trip_search": 10,
    "lufthansa_filter_nonstop": 10,
    "lufthansa_filter_cabin": 10,
    "lufthansa_sort_lowest": 10,
    "lufthansa_price_cap": 10,
    "lufthansa_time_window_filter": 10,
    "lufthansa_fare_details": 10,
}

AIRPORTS = ["JFK", "MUC", "FRA", "LAX", "CDG", "LHR", "BOS", "ORD"]
CABINS = ["Economy", "Premium Economy", "Business"]
TIME_WINDOWS = ["Morning", "Afternoon", "Evening"]
PRICE_CAPS = [100, 200, 300, 400, 500]

def _rand_date(start_days=10, end_days=90) -> str:
    return (dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))).strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    from_airport, to_airport = random.sample(AIRPORTS, 2)
    depart_date = _rand_date()
    return_date = None if oneway else _rand_date(start_days=11)
    return {
        "from": from_airport,
        "to": to_airport,
        "depart": depart_date,
        "return": return_date,
    }

def _ui_hygiene() -> list[str]:
    return [
        "Ignore all informational popups and banners.",
        "Perform actions but avoid payments or personal data entry.",
    ]

def _book_home() -> list[str]:
    return [
        "Visit 'https://www.lufthansa.com'.",
        "Ensure the flight booking section is visible.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "Once dates are selected, close the calendar interface."

def _from_to_steps(origin: str, dest: str) -> list[str]:
    return [
        f"Focus on the 'From' field and enter '{origin}'.",
        f"Select '{origin}' from the suggestions.",
        f"Focus on the 'To' field and enter '{dest}'.",
        f"Select '{dest}' from the suggestions.",
    ]

def lufthansa_one_way_search(_: dict) -> dict:
    trip = _trip_base(oneway=True)
    steps = _book_home() + [
        "Choose 'One Way'.",
        *_from_to_steps(trip["from"], trip["to"]),
        f"Set departure date to '{trip['depart']}'.",
        _calendar_done_step(),
        "Confirm the search with 1 adult passenger.",
        "Click 'Search' to view flights.",
    ]
    return {"task_type": "lufthansa_one_way_search", **trip, "steps": steps}

def lufthansa_round_trip_search(_: dict) -> dict:
    trip = _trip_base()
    steps = _book_home() + [
        "Choose 'Round Trip'.",
        *_from_to_steps(trip["from"], trip["to"]),
        f"Select departure date '{trip['depart']}' and return date '{trip['return']}'.",
        _calendar_done_step(),
        "Confirm search for 1 adult passenger.",
        "Click 'Search' to view flights.",
    ]
    return {"task_type": "lufthansa_round_trip_search", **trip, "steps": steps}

def lufthansa_filter_nonstop(_: dict) -> dict:
    base = lufthansa_round_trip_search({})
    base["task_type"] = "lufthansa_filter_nonstop"
    base["steps"] += ["Apply the filter for nonstop flights.", "Verify results show nonstop flights only."]
    return base

def lufthansa_filter_cabin(_: dict) -> dict:
    base = lufthansa_round_trip_search({})
    cabin = random.choice(CABINS)
    base["task_type"] = "lufthansa_filter_cabin"
    base["cabin"] = cabin
    base["steps"] += [f"Filter results to show only '{cabin}' class seats."]
    return base

def lufthansa_sort_lowest(_: dict) -> dict:
    base = lufthansa_round_trip_search({})
    base["task_type"] = "lufthansa_sort_lowest"
    base["steps"] += ["Sort results by lowest price."]
    return base

def lufthansa_price_cap(_: dict) -> dict:
    base = lufthansa_round_trip_search({})
    cap = random.choice(PRICE_CAPS)
    base["task_type"] = "lufthansa_price_cap"
    base["max_price"] = cap
    base["steps"] += [f"Apply the price cap to {cap} EUR.", "List the first available itinerary under this cap."]
    return base

def lufthansa_time_window_filter(_: dict) -> dict:
    base = lufthansa_round_trip_search({})
    window = random.choice(TIME_WINDOWS)
    base["task_type"] = "lufthansa_time_window_filter"
    base["window"] = window
    base["steps"] += [f"Filter outbound flights to the '{window}' time window."]
    return base

def lufthansa_fare_details(_: dict) -> dict:
    base = lufthansa_round_trip_search({})
    base["task_type"] = "lufthansa_fare_details"
    base["steps"] += ["Select an itinerary to view its fare details.", "Review the fare rules and conditions."]
    return base

_TASK_GENERATORS: Dict[LUFTHANSA_TASK_TYPES, Callable[[dict], dict]] = {
    "lufthansa_one_way_search": lufthansa_one_way_search,
    "lufthansa_round_trip_search": lufthansa_round_trip_search,
    "lufthansa_filter_nonstop": lufthansa_filter_nonstop,
    "lufthansa_filter_cabin": lufthansa_filter_cabin,
    "lufthansa_sort_lowest": lufthansa_sort_lowest,
    "lufthansa_price_cap": lufthansa_price_cap,
    "lufthansa_time_window_filter": lufthansa_time_window_filter,
    "lufthansa_fare_details": lufthansa_fare_details,
}

def generate_lufthansa_task(task_type: LUFTHANSA_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = get_instruction("Lufthansa", task["steps"]).model_dump()
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    random.seed(seed)
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list):
        payloads = []
    
    futures, out = [], []
    items = list(LUFTHANSA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % len(payloads)] if payloads else {}
                futures.append(ex.submit(generate_lufthansa_task, ttype, p))
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