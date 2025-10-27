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
}

AIRPORTS = ["JFK", "LAX", "BOS", "MCO", "FLL", "SFO", "ORD", "SEA", "LAS", "BWI"]
INTL = ["CUN", "SJD"]
EASY_PAIRS = [("JFK", "BOS"), ("LAX", "SEA"), ("BWI", "JFK"), ("SFO", "LAS")]
CABINS_EASY = ["Blue", "Blue Plus", "Blue Extra"]
WINDOWS = ["Morning", "Afternoon", "Evening"]
PRICE_CAPS = [100, 200, 300, 400, 500]

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
        "Dismiss popups/banners (e.g., 'I understand', 'Join TrueBlue for free', 'Shop with points').",
        "Do not book or purchase anything; only search and view results.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.jetblue.com' with the booking widget visible.",
        "Ensure the 'BOOK' tab is active.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, close the calendar/date picker."

def _instr(steps: list[str]) -> dict:
    return get_instruction("JetBlue", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus the 'From' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{origin}'.",
        f"{p}Select the autocomplete option for '{origin}'.",
        f"{p}Confirm origin shows '{origin}' with correct city.",
        f"{p}Focus the 'To' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{dest}'.",
        f"{p}Select the autocomplete option for '{dest}'.",
        f"{p}Confirm destination shows '{dest}' with correct city.",
    ]

def jetblue_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True, domestic=True)
    steps = _book_home() + [
        "Select 'One Way' option.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date to '{t['depart']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Find It' to view results.",
    ]
    return {"task_type":"jetblue_one_way_search",**t,"steps":steps}

def jetblue_round_trip_search(_: dict) -> dict:
    t = _trip_base(domestic=True)
    steps = _book_home() + [
        "Select 'Round Trip' option.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set dates: depart '{t['depart']}', return '{t['return']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Find It' to view results.",
    ]
    return {"task_type":"jetblue_round_trip_search",**t,"steps":steps}

def jetblue_filter_nonstop(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    base["task_type"]="jetblue_filter_nonstop"
    base["steps"] += [
        "Apply the 'Nonstop' filter.",
        "Ensure any search box/dropdown is closed before continuing.",
    ]
    return base

def jetblue_filter_cabin(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    cabin = random.choice(CABINS_EASY)
    base["task_type"]="jetblue_filter_cabin"
    base["target_cabin"]=cabin
    base["steps"] += [
        f"Filter/select cabin to '{cabin}'.",
        "Ensure any search box/dropdown is closed before continuing.",
    ]
    return base

def jetblue_sort_lowest(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    base["task_type"]="jetblue_sort_lowest"
    base["steps"] += [
        "Sort results by lowest price.",
        "Ensure any search box/dropdown is closed before continuing.",
    ]
    return base

def jetblue_price_cap(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    cap = random.choice(PRICE_CAPS)
    base["task_type"]="jetblue_price_cap"
    base["max_price"]=cap
    base["steps"] += [
        f"Use filters to find itineraries ≤ ${cap}; list the first one if any.",
        "Ensure any search box/dropdown is closed before continuing.",
    ]
    return base

def jetblue_time_window_filter(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    win = random.choice(WINDOWS)
    base["task_type"]="jetblue_time_window_filter"
    base["window"]=win
    base["steps"] += [
        f"Filter outbound departure time to '{win}'.",
        "Ensure any search box/dropdown is closed before continuing.",
    ]
    return base

def jetblue_fare_details(_: dict) -> dict:
    base = jetblue_round_trip_search({})
    base["task_type"]="jetblue_fare_details"
    base["focus"]="fare details panel"
    base["steps"] += [
        "Open fare details on the first result and confirm a fare rules panel appears.",
        "Do not book; only view details.",
    ]
    return base

_TASK_GENERATORS: Dict[JETBLUE_TASK_TYPES, Callable[[dict], dict]] = {
    "jetblue_one_way_search": jetblue_one_way_search,
    "jetblue_round_trip_search": jetblue_round_trip_search,
    "jetblue_filter_nonstop": jetblue_filter_nonstop,
    "jetblue_filter_cabin": jetblue_filter_cabin,
    "jetblue_sort_lowest": jetblue_sort_lowest,
    "jetblue_price_cap": jetblue_price_cap,
    "jetblue_time_window_filter": jetblue_time_window_filter,
    "jetblue_fare_details": jetblue_fare_details,
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
    if not isinstance(payloads, list):
        payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(JETBLUE_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for task_type, count in items:
            for _ in range(count):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_jetblue_task, task_type, p))
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