import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

VIRGIN_TASK_TYPES = Literal[
    "virgin_one_way_search",
    "virgin_round_trip_search",
    "virgin_filter_nonstop",
    "virgin_filter_cabin",
    "virgin_fare_details",
    "virgin_flight_deals",
    "virgin_flying_club_info",
    "virgin_baggage_info",
    "virgin_customer_service_info",
    "virgin_help_center_topic",
]

VIRGIN_SAMPLING_CONFIG: Dict[VIRGIN_TASK_TYPES, int] = {
    "virgin_one_way_search": 10,
    "virgin_round_trip_search": 10,
    "virgin_filter_nonstop": 10,
    "virgin_filter_cabin": 10,
    "virgin_fare_details": 10,
    "virgin_flight_deals": 10,
    "virgin_flying_club_info": 10,
    "virgin_baggage_info": 10,
    "virgin_customer_service_info": 10,
    "virgin_help_center_topic": 10,
}

AIRPORTS = ["JFK", "LAX", "LHR", "ATL", "ORD", "DFW", "MIA", "SFO", "SEA", "BOS"]
CABINS = ["Economy", "Premium Economy", "Upper Class"]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    o, d = random.sample(AIRPORTS, 2)
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any pop-ups or banners (e.g., cookies message).",
        "Do not book or purchase anything; only search and view results."
    ]

def _book_home() -> list[str]:
    return [
        "Navigate to 'https://www.virginatlantic.com' with the flight booking widget visible.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, confirm by clicking 'Done' on the calendar/date picker."

def _instr(steps: list[str]) -> dict:
    return get_instruction("Virgin Atlantic", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Select the 'From' field and enter '{origin}'.",
        f"{p}Select '{origin}' from the suggestions.",
        f"{p}Select the 'To' field and enter '{dest}'.",
        f"{p}Select '{dest}' from the suggestions.",
    ]

def virgin_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _book_home() + [
        "Select 'One Way'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date to '{t['depart']}'.",
        _calendar_done_step(),
        "Search flights.",
    ]
    return {"task_type": "virgin_one_way_search", **t, "steps": steps}

def virgin_round_trip_search(_: dict) -> dict:
    t = _trip_base()
    steps = _book_home() + [
        "Select 'Round Trip'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure and return dates to '{t['depart']}' and '{t['return']}' respectively.",
        _calendar_done_step(),
        "Search flights.",
    ]
    return {"task_type": "virgin_round_trip_search", **t, "steps": steps}

def virgin_filter_nonstop(_: dict) -> dict:
    base = virgin_round_trip_search({})
    base["task_type"] = "virgin_filter_nonstop"
    base["steps"] += ["Enable the 'Nonstop' filter.", "View and confirm the filtered results."]
    return base

def virgin_filter_cabin(_: dict) -> dict:
    base = virgin_round_trip_search({})
    cabin = random.choice(CABINS)
    base["task_type"] = "virgin_filter_cabin"
    base["target_cabin"] = cabin
    base["steps"] += [f"Filter results by the cabin: '{cabin}'.", "View and confirm the filtered results."]
    return base

def virgin_fare_details(_: dict) -> dict:
    base = virgin_round_trip_search({})
    base["task_type"] = "virgin_fare_details"
    base["focus"] = "fare details"
    base["steps"] += ["Select a flight and view fare details.", "Confirm visibility of relevant fare details.", "Do not book the flight."]
    return base

def virgin_flight_deals(_: dict) -> dict:
    steps = [
        "Go to the deals page at 'https://flights.virginatlantic.com/en-gb/'.",
        *_ui_hygiene(),
        "Record the first deal's destination and transit price.",
    ]
    return {"task_type": "virgin_flight_deals", "focus": "first deal", "steps": steps}

def virgin_flying_club_info(_: dict) -> dict:
    steps = [
        "Go to the Flying Club page at 'https://flywith.virginatlantic.com/global/en/flying-club.html'.",
        *_ui_hygiene(),
        "Understand how to join the Flying Club and list two benefits.",
    ]
    return {"task_type": "virgin_flying_club_info", "focus": "membership benefits", "steps": steps}

def virgin_baggage_info(_: dict) -> dict:
    steps = [
        "Go to 'https://help.virginatlantic.com/us/en/baggage.html'.",
        *_ui_hygiene(),
        "Retrieve and summarize rules regarding carry-on and checked baggage.",
    ]
    return {"task_type": "virgin_baggage_info", "focus": "baggage rules", "steps": steps}

def virgin_customer_service_info(_: dict) -> dict:
    steps = [
        "Go to Virgin Atlantic's Customer Service at 'https://help.virginatlantic.com/us/en/policies/conditions-of-carriage.html'.",
        *_ui_hygiene(),
        "Identify the contact details for customer support.",
    ]
    return {"task_type": "virgin_customer_service_info", "focus": "customer support", "steps": steps}

def virgin_help_center_topic(_: dict) -> dict:
    steps = [
        "Access the Help Center via 'https://www.virginatlantic.com/help'.",
        *_ui_hygiene(),
        "Navigate to the 'Baggage' section and note two key guidelines.",
    ]
    return {"task_type": "virgin_help_center_topic", "topic": "Baggage", "steps": steps}

_TASK_GENERATORS: Dict[VIRGIN_TASK_TYPES, Callable[[dict], dict]] = {
    "virgin_one_way_search": virgin_one_way_search,
    "virgin_round_trip_search": virgin_round_trip_search,
    "virgin_filter_nonstop": virgin_filter_nonstop,
    "virgin_filter_cabin": virgin_filter_cabin,
    "virgin_fare_details": virgin_fare_details,
    "virgin_flight_deals": virgin_flight_deals,
    "virgin_flying_club_info": virgin_flying_club_info,
    "virgin_baggage_info": virgin_baggage_info,
    "virgin_customer_service_info": virgin_customer_service_info,
    "virgin_help_center_topic": virgin_help_center_topic,
}

def generate_virgin_task(task_type: VIRGIN_TASK_TYPES, payload: dict) -> dict:
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
    items = list(VIRGIN_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_virgin_task, ttype, p))
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