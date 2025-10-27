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
]

LUFTHANSA_SAMPLING_CONFIG: Dict[LUFTHANSA_TASK_TYPES, int] = {
    "lufthansa_one_way_search": 10,
    "lufthansa_round_trip_search": 10,
    "lufthansa_filter_nonstop": 10,
    "lufthansa_filter_cabin": 10,
    "lufthansa_sort_lowest": 10,
    "lufthansa_price_cap": 10,
    "lufthansa_time_window_filter": 10,
}

AIRPORT_CODES = ["JFK", "LHR", "CDG", "FRA", "MUC", "SFO", "LAX", "ORD", "HND", "NRT"]
CABIN_CLASSES = ["Economy", "Premium Economy", "Business", "First Class"]
WINDOWS = ["Morning (5–11am)", "Afternoon (12–5pm)", "Evening (6–11pm)"]

def _random_date(start_days=10, end_days=90) -> str:
    date = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return date.strftime("%Y-%m-%d")

def _create_trip(oneway=False):
    origin, destination = random.sample(AIRPORT_CODES, 2)
    departure_date = _random_date()
    return_date = None if oneway else (dt.datetime.strptime(departure_date, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 21))).strftime("%Y-%m-%d")
    return {"from": origin, "to": destination, "depart": departure_date, "return": return_date}

def _ui_clean() -> list[str]:
    return [
        "Close any pop-up messages or banners.",
        "Do not proceed with any real bookings or payments; only simulate interactions.",
    ]

def _search_home() -> list[str]:
    return [
        "Navigate to the Lufthansa homepage with flight search available.",
        "Ensure the 'BOOK' tab is active with flight options visible.",
        *_ui_clean(),
    ]

def lufthansa_one_way_search(_: dict) -> dict:
    trip = _create_trip(oneway=True)
    steps = _search_home() + [
        "Select 'One Way'.",
        f"Enter '{trip['from']}' as the origin airport.",
        f"Enter '{trip['to']}' as the destination airport.",
        f"Select a departure date of '{trip['depart']}'.",
        "Set passengers to 1 adult.",
        "Click 'Search' to view results.",
    ]
    return {"task_type": "lufthansa_one_way_search", **trip, "steps": steps}

def lufthansa_round_trip_search(_: dict) -> dict:
    trip = _create_trip()
    steps = _search_home() + [
        "Select 'Round Trip'.",
        f"Enter '{trip['from']}' as the origin airport.",
        f"Enter '{trip['to']}' as the destination airport.",
        f"Select dates: Depart on '{trip['depart']}', Return on '{trip['return']}'.",
        "Set passengers to 1 adult.",
        "Click 'Search' to view results.",
    ]
    return {"task_type": "lufthansa_round_trip_search", **trip, "steps": steps}

def lufthansa_filter_nonstop(_: dict) -> dict:
    base = lufthansa_round_trip_search({})
    base["task_type"] = "lufthansa_filter_nonstop"
    base["steps"] += ["Enable 'Nonstop flights only' filter.", "Verify only nonstop flights are displayed."]
    return base

def lufthansa_filter_cabin(_: dict) -> dict:
    base = lufthansa_round_trip_search({})
    cabin = random.choice(CABIN_CLASSES)
    base["task_type"] = "lufthansa_filter_cabin"
    base["target_cabin"] = cabin
    base["steps"] += [f"Select '{cabin}' as travel class.", "Verify flights displayed match the selected cabin class."]
    return base

def lufthansa_sort_lowest(_: dict) -> dict:
    base = lufthansa_round_trip_search({})
    base["task_type"] = "lufthansa_sort_lowest"
    base["steps"] += ["Sort results by 'Lowest Price'.", "Confirm the order of flights is from the lowest to highest price."]
    return base

def lufthansa_price_cap(_: dict) -> dict:
    base = lufthansa_round_trip_search({})
    cap = random.choice([200, 350, 500, 750, 1000])
    base["task_type"] = "lufthansa_price_cap"
    base["max_price"] = cap
    base["steps"] += [f"Apply a price cap of up to ${cap}.", "Ensure all displayed options are below the set price cap."]
    return base

def lufthansa_time_window_filter(_: dict) -> dict:
    base = lufthansa_round_trip_search({})
    time_window = random.choice(WINDOWS)
    base["task_type"] = "lufthansa_time_window_filter"
    base["window"] = time_window
    base["steps"] += [f"Filter departure time by '{time_window}'.", "Verify that flights fall within the selected time window."]
    return base

_TASK_GENERATORS: Dict[LUFTHANSA_TASK_TYPES, Callable[[dict], dict]] = {
    "lufthansa_one_way_search": lufthansa_one_way_search,
    "lufthansa_round_trip_search": lufthansa_round_trip_search,
    "lufthansa_filter_nonstop": lufthansa_filter_nonstop,
    "lufthansa_filter_cabin": lufthansa_filter_cabin,
    "lufthansa_sort_lowest": lufthansa_sort_lowest,
    "lufthansa_price_cap": lufthansa_price_cap,
    "lufthansa_time_window_filter": lufthansa_time_window_filter,
}

def generate_task(task_type: LUFTHANSA_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = get_instruction("Lufthansa", task["steps"]).model_dump()
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as file:
            payloads = json.load(file)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(LUFTHANSA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for ttype, count in items:
            for _ in range(count):
                payload = payloads[_ % max(1, len(payloads))] if payloads else {}
                futures.append(executor.submit(generate_task, ttype, payload))
        for future in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(future.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as file:
        json.dump(out, file, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)