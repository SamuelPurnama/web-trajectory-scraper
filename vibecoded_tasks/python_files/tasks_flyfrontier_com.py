import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

FRONTIER_TASK_TYPES = Literal[
    "frontier_one_way_search",
    "frontier_round_trip_search",
    "frontier_filter_nonstop",
    "frontier_filter_cabin",
    "frontier_sort_lowest",
    "frontier_price_cap",
    "frontier_flight_deals",
    "frontier_maintenance_info"
]

FRONTIER_SAMPLING_CONFIG: Dict[FRONTIER_TASK_TYPES, int] = {
    "frontier_one_way_search": 10,
    "frontier_round_trip_search": 10,
    "frontier_filter_nonstop": 10,
    "frontier_filter_cabin": 10,
    "frontier_sort_lowest": 10,
    "frontier_price_cap": 10,
    "frontier_flight_deals": 10,
    "frontier_maintenance_info": 10
}

AIRPORTS = ["DEN","DFW","ORD","PHX","LAS","ATL","LAX","SEA","MCO","BWI","SFO","PHL"]
INTL = ["CUN","SJD","PUJ"]
EASY_PAIRS = [("DEN","PHX"),("LAX","LAS"),("DFW","DEN"),("ORD","ATL"),("SEA","SFO")]
WINDOWS = ["Morning (5–11am)","Afternoon (12–5pm)"]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    if random.random() < 0.8:
        o, d = random.choice(EASY_PAIRS)
    else:
        pool = AIRPORTS + INTL
        o, d = random.sample(pool, 2)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners.",
        "Ensure you only search and view results, do not book or purchase anything.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://flyfrontier.com'.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, click 'Done' if applicable."

def _instr(steps: list[str]) -> dict:
    return get_instruction("Frontier", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus on the 'From' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{origin}'.",
        f"{p}Select the autocomplete option for '{origin}' (airport).",
        f"{p}Confirm origin shows '{origin}'; press Enter if needed.",
        f"{p}Focus on the 'To' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{dest}'.",
        f"{p}Select the autocomplete option for '{dest}' (airport).",
        f"{p}Confirm destination shows '{dest}'; press Enter if needed.",
    ]

def frontier_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _book_home() + [
        "Select 'One Way'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set depart date to '{t['depart']}'.",
        _calendar_done_step(),
        "Ensure that travelers are set to 1 adult.",
        "Click 'Find Flights' to view results.",
    ]
    return {"task_type":"frontier_one_way_search",**t,"steps":steps}

def frontier_round_trip_search(_: dict) -> dict:
    t = _trip_base()
    steps = _book_home() + [
        "Select 'Round Trip'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set dates: depart '{t['depart']}', return '{t['return']}'.",
        _calendar_done_step(),
        "Ensure that travelers are set to 1 adult.",
        "Click 'Find Flights' to view results.",
    ]
    return {"task_type":"frontier_round_trip_search",**t,"steps":steps}

def frontier_filter_nonstop(_: dict) -> dict:
    base = frontier_round_trip_search({})
    base["task_type"]="frontier_filter_nonstop"
    base["steps"] += ["Enable the 'Nonstop' filter."]
    return base

def frontier_filter_cabin(_: dict) -> dict:
    base = frontier_round_trip_search({})
    base["task_type"]="frontier_filter_cabin"
    base["steps"] += ["Select the 'Economy' cabin option."]
    return base

def frontier_sort_lowest(_: dict) -> dict:
    base = frontier_round_trip_search({})
    base["task_type"]="frontier_sort_lowest"
    base["steps"] += ["Sort the results by lowest price."]
    return base

def frontier_price_cap(_: dict) -> dict:
    base = frontier_round_trip_search({})
    cap = random.choice([100, 200, 300, 400, 500])
    base["task_type"]="frontier_price_cap"
    base["max_price"]=cap
    base["steps"] += [f"Set a price cap of ${cap} and view available flights."]
    return base

def frontier_flight_deals(_: dict) -> dict:
    steps = [
        "Go to url 'https://flights.flyfrontier.com/en/flight-deals'.",
        *_ui_hygiene(),
        "Select a destination deal and note the details shown.",
    ]
    return {"task_type":"frontier_flight_deals","focus":"domestic deal","steps":steps}

def frontier_maintenance_info(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flyfrontier.com/optional-services/'.",
        *_ui_hygiene(),
        "Find and summarize the new baggage fee policy.",
    ]
    return {"task_type":"frontier_maintenance_info","focus":"baggage policy","steps":steps}

_TASK_GENERATORS: Dict[FRONTIER_TASK_TYPES, Callable[[dict], dict]] = {
    "frontier_one_way_search": frontier_one_way_search,
    "frontier_round_trip_search": frontier_round_trip_search,
    "frontier_filter_nonstop": frontier_filter_nonstop,
    "frontier_filter_cabin": frontier_filter_cabin,
    "frontier_sort_lowest": frontier_sort_lowest,
    "frontier_price_cap": frontier_price_cap,
    "frontier_flight_deals": frontier_flight_deals,
    "frontier_maintenance_info": frontier_maintenance_info,
}

def generate_frontier_task(task_type: FRONTIER_TASK_TYPES, payload: dict) -> dict:
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