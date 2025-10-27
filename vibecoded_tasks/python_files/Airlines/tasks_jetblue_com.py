import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

JETBLUE_TASK_TYPES = Literal[
    "jetblue_one_way_search",
    "jetblue_round_trip_search",
    "jetblue_filter_nonstop",
    "jetblue_filter_cabin",
    "jetblue_sort_lowest",
    "jetblue_price_cap",
    "jetblue_time_window_filter",
    "jetblue_fare_details",
    "jetblue_baggage_info",
]

JETBLUE_SAMPLING_CONFIG: Dict[JETBLUE_TASK_TYPES, int] = {
    "jetblue_one_way_search": 10,
    "jetblue_round_trip_search": 10,
    "jetblue_filter_nonstop": 10,
    "jetblue_filter_cabin": 10,
    "jetblue_sort_lowest": 10,
    "jetblue_price_cap": 10,
    "jetblue_time_window_filter": 10,
    "jetblue_fare_details": 10,
    "jetblue_baggage_info": 10,
}

AIRPORTS = ["JFK", "LAX", "BOS", "MCO", "FLL", "SEA", "LAS", "LAX", "ORD", "ATL"]
INTL = ["CUN", "LHR", "YYZ"]
EASY_PAIRS = [("JFK", "BOS"), ("LAX", "LAS"), ("ORD", "ATL")]
CABINS_EASY = ["Blue", "Blue Plus", "Mint"]
WINDOWS = ["Morning", "Afternoon", "Evening"]
BAGS = ["carry-on policies", "first checked bag fees", "overweight fees"]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False, domestic=True):
    if domestic and random.random() < 0.8 and EASY_PAIRS:
        o, d = random.choice(EASY_PAIRS)
    else:
        pool = AIRPORTS if domestic else (AIRPORTS + INTL)
        o, d = random.sample(pool, 2)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or notices.",
        "Do not proceed to payment or enter personal information; only browse and search.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.jetblue.com/' with the booking widget visible.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "Confirm the dates selection."

def _instr(steps: list[str]) -> dict:
    return get_instruction("JetBlue", steps).model_dump()

def _from_to_steps(origin: str, dest: str) -> list[str]:
    return [
        "Focus the 'From' field.",
        f"Clear/reset the field and type '{origin}'.",
        f"Select '{origin}' from the autocomplete suggestions.",
        "Focus the 'To' field.",
        f"Clear/reset the field and type '{dest}'.",
        f"Select '{dest}' from the autocomplete suggestions.",
    ]

def jetblue_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True, domestic=True)
    steps = _book_home() + [
        "Select 'One Way' option.",
        *_from_to_steps(t['from'], t['to']),
        f"Set the departure date to '{t['depart']}'.",
        _calendar_done_step(),
        "Ensure that '1 passenger' is selected.",
        "Click 'Find Flights' to view the results.",
    ]
    return {"task_type": "jetblue_one_way_search", **t, "steps": steps}

def jetblue_round_trip_search(_: dict) -> dict:
    t = _trip_base(domestic=True)
    steps = _book_home() + [
        "Select 'Round Trip' option.",
        *_from_to_steps(t['from'], t['to']),
        f"Set the departure date to '{t['depart']}' and return date to '{t['return']}'.",
        _calendar_done_step(),
        "Ensure that '1 passenger' is selected.",
        "Click 'Find Flights' to view the results.",
    ]
    return {"task_type": "jetblue_round_trip_search", **t, "steps": steps}

def jetblue_filter_nonstop(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    base["task_type"] = "jetblue_filter_nonstop"
    base["steps"] += [
        "After searching, enable the 'Nonstop' filter.",
    ]
    return base

def jetblue_filter_cabin(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    cabin = random.choice(CABINS_EASY)
    base["task_type"] = "jetblue_filter_cabin"
    base["target_cabin"] = cabin
    base["steps"] += [f"Filter results to only show the '{cabin}' cabin class."]
    return base

def jetblue_sort_lowest(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    base["task_type"] = "jetblue_sort_lowest"
    base["steps"] += ["Sort the flight results by lowest price."]
    return base

def jetblue_price_cap(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    cap = random.choice([150, 250, 400, 600])
    base["task_type"] = "jetblue_price_cap"
    base["max_price"] = cap
    base["steps"] += [f"Apply filters to limit results to flights costing no more than ${cap}."]
    return base

def jetblue_time_window_filter(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    win = random.choice(WINDOWS)
    base["task_type"] = "jetblue_time_window_filter"
    base["window"] = win
    base["steps"] += [f"Filter results to show flights departing in the '{win}' window."]
    return base

def jetblue_fare_details(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    base["task_type"] = "jetblue_fare_details"
    base["focus"] = "fare details"
    base["steps"] += [
        "Select a flight and view its fare details.",
        "Verify the presence of a fare rules panel.",
    ]
    return base

def jetblue_baggage_info(_: dict) -> dict:
    focus = random.choice(BAGS)
    steps = [
        "Go to url 'https://www.jetblue.com/at-the-airport/baggage-information'.",
        *_ui_hygiene(),
        f"Find and summarize information related to: {focus}.",
    ]
    return {"task_type": "jetblue_baggage_info", "focus": focus, "steps": steps}

_TASK_GENERATORS: Dict[JETBLUE_TASK_TYPES, Callable[[dict], dict]] = {
    "jetblue_one_way_search": jetblue_one_way_search,
    "jetblue_round_trip_search": jetblue_round_trip_search,
    "jetblue_filter_nonstop": jetblue_filter_nonstop,
    "jetblue_filter_cabin": jetblue_filter_cabin,
    "jetblue_sort_lowest": jetblue_sort_lowest,
    "jetblue_price_cap": jetblue_price_cap,
    "jetblue_time_window_filter": jetblue_time_window_filter,
    "jetblue_fare_details": jetblue_fare_details,
    "jetblue_baggage_info": jetblue_baggage_info,
}

def generate_jetblue_task(task_type: JETBLUE_TASK_TYPES, payload: dict) -> dict:
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
    items = list(JETBLUE_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_jetblue_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)