import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

SPIRIT_TASK_TYPES = Literal[
    "spirit_one_way_search",
    "spirit_round_trip_search",
    "spirit_filter_nonstop",
    "spirit_sort_lowest",
    "spirit_price_cap",
    "spirit_flight_deals",
    "spirit_check_flight_status",
    "spirit_baggage_info"
]

SPIRIT_SAMPLING_CONFIG: Dict[SPIRIT_TASK_TYPES, int] = {
    "spirit_one_way_search": 10,
    "spirit_round_trip_search": 10,
    "spirit_filter_nonstop": 10,
    "spirit_sort_lowest": 10,
    "spirit_price_cap": 10,
    "spirit_flight_deals": 10,
    "spirit_check_flight_status": 10,
    "spirit_baggage_info": 10,
}

AIRPORTS = ["FLL", "DFW", "LAS", "ORD", "DEN", "MCO", "SEA", "PHX", "LAX", "ATL", "BWI", "NYC"]
INTL = ["CUN", "MEX", "PTY", "BOG"]
EASY_PAIRS = [("FLL", "ATL"), ("DFW", "LAS"), ("ORD", "DEN"), ("MCO", "SEA"), ("PHX", "LAX")]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    o, d = random.choice(EASY_PAIRS)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss popups/banners (e.g., 'Join Free Spirit', 'Subscribe to deals').",
        "Do not book or purchase anything; only search and view results.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.spirit.com' with the booking widget visible.",
        "Ensure the 'BOOK' tab is active.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, click 'Done' or equivalent on the calendar/date picker."

def _instr(steps: list[str]) -> dict:
    return get_instruction("Spirit", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus the 'From' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{origin}'.",
        f"{p}Select the autocomplete option for '{origin}' (airport).",
        f"{p}Confirm origin shows '{origin}' with correct city; press Enter if needed.",
        f"{p}Close the autocomplete/dropdown before proceeding (e.g., Tab or click outside).",
        f"{p}Focus the 'To' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{dest}'.",
        f"{p}Select the autocomplete option for '{dest}' (airport).",
        f"{p}Confirm destination shows '{dest}' with correct city; press Enter if needed.",
        f"{p}Ensure the dropdown is closed before proceeding.",
    ]

def spirit_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _book_home() + [
        "Select 'One Way' and press Enter to confirm.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set depart date to '{t['depart']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search' to view results.",
    ]
    return {"task_type":"spirit_one_way_search",**t,"steps":steps}

def spirit_round_trip_search(_: dict) -> dict:
    t = _trip_base()
    steps = _book_home() + [
        "Select 'Round Trip' and press Enter to confirm.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set dates: depart '{t['depart']}', return '{t['return']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search' to view results.",
    ]
    return {"task_type":"spirit_round_trip_search",**t,"steps":steps}

def spirit_filter_nonstop(_: dict) -> dict:
    base = spirit_round_trip_search({})
    base["task_type"]="spirit_filter_nonstop"
    base["steps"] += ["Enable the 'Nonstop' filter.","Ensure any search box/dropdown is closed before continuing."]
    return base

def spirit_sort_lowest(_: dict) -> dict:
    base = spirit_round_trip_search({})
    base["task_type"]="spirit_sort_lowest"
    base["steps"] += ["Sort by lowest price.","Ensure any search box/dropdown is closed before continuing."]
    return base

def spirit_price_cap(_: dict) -> dict:
    base = spirit_round_trip_search({})
    cap = random.choice([100, 150, 200, 250, 300, 400])
    base["task_type"]="spirit_price_cap"
    base["max_price"]=cap
    base["steps"] += [f"Use filters to find itineraries ≤ ${cap}; list the first one if any.","Ensure any search box/dropdown is closed before continuing."]
    return base

def spirit_flight_deals(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.spirit.com/en/flights'.",
        *_ui_hygiene(),
        "Report one domestic deal: destination and lowest price shown.",
    ]
    return {"task_type":"spirit_flight_deals","focus":"single domestic deal","steps":steps}

def spirit_check_flight_status(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.spirit.com/flight-status'.",
        *_ui_hygiene(),
        "Check the status for flight 100; verify departure and arrival times are shown.",
    ]
    return {"task_type":"spirit_check_flight_status","focus":"single flight status check","steps":steps}

def spirit_baggage_info(_: dict) -> dict:
    focus = random.choice(["carry-on size/weight","first checked bag fees","oversize/overweight fees"])
    steps = [
        "Go to url 'https://www.spirit.com/optional-services'.",
        *_ui_hygiene(),
        f"Find and summarize: {focus}.",
    ]
    return {"task_type":"spirit_baggage_info","focus":focus,"steps":steps}

_TASK_GENERATORS: Dict[SPIRIT_TASK_TYPES, Callable[[dict], dict]] = {
    "spirit_one_way_search": spirit_one_way_search,
    "spirit_round_trip_search": spirit_round_trip_search,
    "spirit_filter_nonstop": spirit_filter_nonstop,
    "spirit_sort_lowest": spirit_sort_lowest,
    "spirit_price_cap": spirit_price_cap,
    "spirit_flight_deals": spirit_flight_deals,
    "spirit_check_flight_status": spirit_check_flight_status,
    "spirit_baggage_info": spirit_baggage_info,
}

def generate_spirit_task(task_type: SPIRIT_TASK_TYPES, payload: dict) -> dict:
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
    items = list(SPIRIT_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_spirit_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)