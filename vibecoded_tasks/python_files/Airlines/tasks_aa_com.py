import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

AA_TASK_TYPES = Literal[
    "aa_one_way_search",
    "aa_round_trip_search",
    "aa_filter_nonstop",
    "aa_flight_status_check",
    "aa_check_baggage_fees",
    "aa_find_offers",
    "aa_use_travel_credit",
    "aa_enable_javascript_support",
    "aa_explore_ski_resorts",
]

AA_SAMPLING_CONFIG: Dict[AA_TASK_TYPES, int] = {
    "aa_one_way_search": 10,
    "aa_round_trip_search": 10,
    "aa_filter_nonstop": 10,
    "aa_flight_status_check": 10,
    "aa_check_baggage_fees": 10,
    "aa_find_offers": 10,
    "aa_use_travel_credit": 10,
    "aa_enable_javascript_support": 10,
    "aa_explore_ski_resorts": 10,
}

AIRPORTS = ["LAX", "JFK", "MIA", "DFW", "ORD", "ATL", "PHX", "SEA", "DEN", "LAS"]
EASY_PAIRS = [("LAX", "JFK"), ("MIA", "DFW"), ("ORD", "ATL"), ("PHX", "SEA"), ("DEN", "LAS")]
BAGS = ["carry-on size/weight", "first checked bag fees", "oversize/overweight fees"]

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
        "Dismiss any pop-ups or notifications.",
        "Do not book or purchase anything; only search and view results.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.aa.com' ensuring the booking module is prominently displayed.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, ensure they are correctly displayed before proceeding."

def _instr(steps: list[str]) -> dict:
    return get_instruction("AA", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Select the 'From' field.",
        f"{p}Clear any existing input.",
        f"{p}Type '{origin}'.",
        f"{p}Select '{origin}' from the auto-suggest list.",
        f"{p}Ensure '{origin}' is selected.",
        f"{p}Select the 'To' field.",
        f"{p}Clear any existing input.",
        f"{p}Type '{dest}'.",
        f"{p}Select '{dest}' from the auto-suggest list.",
        f"{p}Ensure '{dest}' is selected."
    ]

def aa_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _book_home() + [
        "Select 'One Way'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date to '{t['depart']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search' to view results."
    ]
    return {"task_type":"aa_one_way_search",**t,"steps":steps}

def aa_round_trip_search(_: dict) -> dict:
    t = _trip_base()
    steps = _book_home() + [
        "Select 'Round Trip'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set dates: depart on '{t['depart']}', return on '{t['return']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search' to view results."
    ]
    return {"task_type":"aa_round_trip_search",**t,"steps":steps}

def aa_filter_nonstop(_: dict) -> dict:
    base = aa_round_trip_search({})
    base["task_type"] = "aa_filter_nonstop"
    base["steps"] += ["Apply 'Nonstop' filter.", "Ensure the filter is active and results are updated."]
    return base

def aa_flight_status_check(_: dict) -> dict:
    steps = [
        "Visit 'https://www.aa.com#aa-hp-flightStatus'.",
        "Enter a valid flight number.",
        "Click 'Check status'.",
        "Verify flight status is displayed."
    ]
    return {"task_type": "aa_flight_status_check", "steps": steps}

def aa_check_baggage_fees(_: dict) -> dict:
    focus = random.choice(BAGS)
    steps = [
        "Visit 'https://www.aa.com/i18n/customer-service/support/optional-service-fees.jsp'.",
        *_ui_hygiene(),
        f"Locate and interpret information about {focus}.",
    ]
    return {"task_type": "aa_check_baggage_fees", "focus": focus, "steps": steps}

def aa_find_offers(_: dict) -> dict:
    steps = [
        "Visit 'https://www.aa.com/i18n/aadvantage-program/earn-miles/offers-promotions.html'.",
        *_ui_hygiene(),
        "Note down the first promotional offer listed."
    ]
    return {"task_type": "aa_find_offers", "steps": steps}

def aa_use_travel_credit(_: dict) -> dict:
    steps = [
        "Visit 'https://www.aa.com/i18n/customer-service/payment-options/travel-credit.jsp'.",
        *_ui_hygiene(),
        "Review the guidance on using travel credit."
    ]
    return {"task_type": "aa_use_travel_credit", "steps": steps}

def aa_enable_javascript_support(_: dict) -> dict:
    steps = [
        "Visit 'https://www.aa.com/i18n/customer-service/support/browser-compatibility.jsp#settings'.",
        *_ui_hygiene(),
        "Locate the section on enabling JavaScript.",
        "Note the instructions provided."
    ]
    return {"task_type": "aa_enable_javascript_support", "steps": steps}

def aa_explore_ski_resorts(_: dict) -> dict:
    steps = [
        "Go to 'https://www.aa.com/en-us/ski-resorts'.",
        *_ui_hygiene(),
        "Browse available ski resort packages and take note of one appealing option."
    ]
    return {"task_type": "aa_explore_ski_resorts", "steps": steps}

_TASK_GENERATORS: Dict[AA_TASK_TYPES, Callable[[dict], dict]] = {
    "aa_one_way_search": aa_one_way_search,
    "aa_round_trip_search": aa_round_trip_search,
    "aa_filter_nonstop": aa_filter_nonstop,
    "aa_flight_status_check": aa_flight_status_check,
    "aa_check_baggage_fees": aa_check_baggage_fees,
    "aa_find_offers": aa_find_offers,
    "aa_use_travel_credit": aa_use_travel_credit,
    "aa_enable_javascript_support": aa_enable_javascript_support,
    "aa_explore_ski_resorts": aa_explore_ski_resorts,
}

def generate_aa_task(task_type: AA_TASK_TYPES, payload: dict) -> dict:
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
    items = list(AA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_aa_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)