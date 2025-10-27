import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

UNITED_TASK_TYPES = Literal[
    "united_one_way_search",
    "united_round_trip_search",
    "united_filter_nonstop",
    "united_filter_cabin",
    "united_sort_lowest",
    "united_price_cap",
    "united_time_window_filter",
    "united_fare_details",
]

UNITED_SAMPLING_CONFIG: Dict[UNITED_TASK_TYPES, int] = {
    "united_one_way_search": 10,
    "united_round_trip_search": 10,
    "united_filter_nonstop": 10,
    "united_filter_cabin": 10,
    "united_sort_lowest": 10,
    "united_price_cap": 10,
    "united_time_window_filter": 10,
    "united_fare_details": 10,
}

AIRPORTS = ["SEA","SFO","LAX","SAN","PHX","DEN","SLC","PDX","LAS","AUS","DFW","IAH","ORD","MSP","ATL","MCO","JFK","EWR","BOS","BWI","IAD","CLT","RDU"]
INTL = ["YVR","YYZ","CUN","SJD"]
EASY_PAIRS = [("SEA","SFO"),("LAX","SFO"),("SEA","DEN"),("PHX","DEN"),("PDX","SLC"),("AUS","DEN"),("LAX","LAS"),("JFK","BOS"),("EWR","CLT")]
CABINS_EASY = ["Economy Plus","Economy","Business"]
WINDOWS = ["Morning (5–11am)","Afternoon (12–5pm)"]

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
        "Dismiss popups or banners if they appear.",
        "Do not book, only search and view results.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.united.com' with the booking widget visible.",
        "Ensure the 'BOOK' tab is active.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, confirm selection to proceed."

def _instr(steps: list[str]) -> dict:
    return get_instruction("United", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus the 'From' field.",
        f"{p}Clear the field and type '{origin}'.",
        f"{p}Select '{origin}' from suggestions.",
        f"{p}Focus the 'To' field.",
        f"{p}Clear the field and type '{dest}'.",
        f"{p}Select '{dest}' from suggestions.",
    ]

def united_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True, domestic=True)
    steps = _book_home() + [
        "Select 'One Way' option.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date to '{t['depart']}'.",
        _calendar_done_step(),
        "Set number of travelers to 1 adult.",
        "Click 'Search' to view results.",
    ]
    return {"task_type":"united_one_way_search",**t,"steps":steps}

def united_round_trip_search(_: dict) -> dict:
    t = _trip_base(domestic=True)
    steps = _book_home() + [
        "Select 'Round Trip' option.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set dates: departure '{t['depart']}', return '{t['return']}'.",
        _calendar_done_step(),
        "Set number of travelers to 1 adult.",
        "Click 'Search' to view results.",
    ]
    return {"task_type":"united_round_trip_search",**t,"steps":steps}

def united_filter_nonstop(_: dict) -> dict:
    base = united_round_trip_search({})
    base["task_type"]="united_filter_nonstop"
    base["steps"] += ["Enable 'Nonstop' filter.", "Ensure all dropdowns are closed before proceeding."]
    return base

def united_filter_cabin(_: dict) -> dict:
    base = united_round_trip_search({})
    cabin = random.choice(CABINS_EASY)
    base["task_type"]="united_filter_cabin"
    base["target_cabin"]=cabin
    base["steps"] += [f"Select cabin class as '{cabin}'.", "Ensure all dropdowns are closed before proceeding."]
    return base

def united_sort_lowest(_: dict) -> dict:
    base = united_round_trip_search({})
    base["task_type"]="united_sort_lowest"
    base["steps"] += ["Sort results by lowest price.", "Ensure all dropdowns are closed before proceeding."]
    return base

def united_price_cap(_: dict) -> dict:
    base = united_round_trip_search({})
    cap = random.choice([200, 300, 450, 700, 1000, 1500])
    base["task_type"]="united_price_cap"
    base["max_price"]=cap
    base["steps"] += [f"Apply a price cap of ${cap}.", "Ensure all dropdowns are closed before proceeding."]
    return base

def united_time_window_filter(_: dict) -> dict:
    base = united_round_trip_search({})
    window = random.choice(WINDOWS)
    base["task_type"]="united_time_window_filter"
    base["window"]=window
    base["steps"] += [f"Filter departure times to {window}.", "Ensure all dropdowns are closed before proceeding."]
    return base

def united_fare_details(_: dict) -> dict:
    base = united_round_trip_search({})
    base["task_type"]="united_fare_details"
    base["focus"]="fare details section"
    base["steps"] += ["Open fare details for the first result.", "Do not book, only review details."]
    return base

_TASK_GENERATORS: Dict[UNITED_TASK_TYPES, Callable[[dict], dict]] = {
    "united_one_way_search": united_one_way_search,
    "united_round_trip_search": united_round_trip_search,
    "united_filter_nonstop": united_filter_nonstop,
    "united_filter_cabin": united_filter_cabin,
    "united_sort_lowest": united_sort_lowest,
    "united_price_cap": united_price_cap,
    "united_time_window_filter": united_time_window_filter,
    "united_fare_details": united_fare_details,
}

def generate_united_task(task_type: UNITED_TASK_TYPES, payload: dict) -> dict:
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
    items = list(UNITED_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_united_task, ttype, p))
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
```