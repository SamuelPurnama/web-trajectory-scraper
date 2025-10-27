import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

ALASKA_TASK_TYPES = Literal[
    "alaska_one_way_search",
    "alaska_round_trip_search",
    "alaska_filter_nonstop",
    "alaska_filter_cabin",
    "alaska_sort_lowest",
    "alaska_price_cap",
    "alaska_time_window_filter",
]

ALASKA_SAMPLING_CONFIG: Dict[ALASKA_TASK_TYPES, int] = {
    "alaska_one_way_search": 10,
    "alaska_round_trip_search": 10,
    "alaska_filter_nonstop": 10,
    "alaska_filter_cabin": 10,
    "alaska_sort_lowest": 10,
    "alaska_price_cap": 10,
    "alaska_time_window_filter": 10,
}

AIRPORTS = ["SEA","SFO","LAX","SAN","PHX","DEN","SLC","PDX","LAS","AUS","DFW","IAH","ORD","MSP","ATL","MCO","JFK","EWR","BOS","BWI","IAD","CLT","RDU"]
INTL = ["YVR","YYZ","CUN","SJD"]
EASY_PAIRS = [("SEA","SFO"),("LAX","SFO"),("SEA","DEN"),("PHX","DEN"),("PDX","SLC"),("AUS","DEN"),("LAX","LAS"),("JFK","BOS"),("EWR","CLT")]
CABINS_EASY = ["Main Cabin","Premium Class","First Class"]
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
        "Dismiss any popups or banners (e.g., 'Join our mailing list', 'Special offers').",
        "Do not proceed to payment or booking confirmation; only search and view results.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.alaskaair.com' with the booking widget visible.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, click 'Done' on the calendar/date picker."

def _instr(steps: list[str]) -> dict:
    return get_instruction("Alaska", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Choose the 'From' field.",
        f"{p}Clear the field if needed.",
        f"{p}Type '{origin}', and select the correct option from the list.",
        f"{p}Ensure '{origin}' is correctly displayed in the 'From' field.",
        f"{p}Close any dropdown menu before continuing.",
        f"{p}Select the 'To' field.",
        f"{p}Clear the field if needed.",
        f"{p}Type '{dest}', and select the correct option from the suggestions.",
        f"{p}Ensure '{dest}' is correctly displayed in the 'To' field.",
        f"{p}Close any dropdown menu before proceeding.",
    ]

def alaska_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True, domestic=True)
    steps = _book_home() + [
        "Select 'One Way' as the trip type.",
        *_from_to_steps(t["from"], t["to"]),
        f"Select departure date as '{t['depart']}'.",
        _calendar_done_step(),
        "Set the number of travelers to 1 adult.",
        "Press 'Search' to browse flight options.",
    ]
    return {"task_type":"alaska_one_way_search",**t,"steps":steps}

def alaska_round_trip_search(_: dict) -> dict:
    t = _trip_base(domestic=True)
    steps = _book_home() + [
        "Select 'Round Trip' for your travel.",
        *_from_to_steps(t["from"], t["to"]),
        f"For departure, choose '{t['depart']}', and for return, select '{t['return']}'.",
        _calendar_done_step(),
        "Set travelers as 1 adult.",
        "Click 'Search' to see available flights.",
    ]
    return {"task_type":"alaska_round_trip_search",**t,"steps":steps}

def alaska_filter_nonstop(_: dict) -> dict:
    base = alaska_round_trip_search({})
    base["task_type"]="alaska_filter_nonstop"
    base["steps"] += ["Apply the 'Nonstop' filter.", "Ensure no filter menus are open before proceeding."]
    return base

def alaska_filter_cabin(_: dict) -> dict:
    base = alaska_round_trip_search({})
    cabin = random.choice(CABINS_EASY)
    base["task_type"]="alaska_filter_cabin"
    base["target_cabin"]=cabin
    base["steps"] += [f"Choose '{cabin}' under cabin preferences.", "Ensure to close any open filter menus."]
    return base

def alaska_sort_lowest(_: dict) -> dict:
    base = alaska_round_trip_search({})
    base["task_type"]="alaska_sort_lowest"
    base["steps"] += ["Sort the results by price, starting with the lowest.", "Make sure all filters are correctly applied."]
    return base

def alaska_price_cap(_: dict) -> dict:
    base = alaska_round_trip_search({})
    cap = random.choice([100, 200, 300, 500, 700, 1000])
    base["task_type"]="alaska_price_cap"
    base["max_price"]=cap
    base["steps"] += [f"Filter results to show options priced at or below ${cap}.", "Ensure to close any filter dropdowns before proceeding."]
    return base

def alaska_time_window_filter(_: dict) -> dict:
    base = alaska_round_trip_search({})
    win = random.choice(WINDOWS)
    base["task_type"]="alaska_time_window_filter"
    base["window"]=win
    base["steps"] += [f"Set departure time to the {win}.", "Ensure all settings are applied properly before reviewing results."]
    return base

_TASK_GENERATORS: Dict[ALASKA_TASK_TYPES, Callable[[dict], dict]] = {
    "alaska_one_way_search": alaska_one_way_search,
    "alaska_round_trip_search": alaska_round_trip_search,
    "alaska_filter_nonstop": alaska_filter_nonstop,
    "alaska_filter_cabin": alaska_filter_cabin,
    "alaska_sort_lowest": alaska_sort_lowest,
    "alaska_price_cap": alaska_price_cap,
    "alaska_time_window_filter": alaska_time_window_filter,
}

def generate_alaska_task(task_type: ALASKA_TASK_TYPES, payload: dict) -> dict:
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
    items = list(ALASKA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_alaska_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)