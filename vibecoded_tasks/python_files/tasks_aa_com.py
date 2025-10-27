import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

AA_TASK_TYPES = Literal[
    "aa_one_way_search",
    "aa_round_trip_search",
    "aa_filter_nonstop",
    "aa_filter_cabin",
    "aa_sort_lowest",
    "aa_offer_explore",
    "aa_travel_alerts",
    "aa_check_baggage_fees",
    "aa_flight_extras",
]

AA_SAMPLING_CONFIG: Dict[AA_TASK_TYPES, int] = {
    "aa_one_way_search": 10,
    "aa_round_trip_search": 10,
    "aa_filter_nonstop": 10,
    "aa_filter_cabin": 10,
    "aa_sort_lowest": 10,
    "aa_offer_explore": 10,
    "aa_travel_alerts": 10,
    "aa_check_baggage_fees": 10,
    "aa_flight_extras": 10,
}

AIRPORTS = ["LAX", "JFK", "ORD", "DFW", "MIA", "SEA", "PHX", "LAS", "MCO", "EWR"]
INTL = ["LHR", "CDG", "FRA", "NRT"]
EASY_PAIRS = [("LAX", "JFK"), ("DFW", "MIA"), ("PHX", "ORD"), ("LAS", "SEA")]
CABINS_EASY = ["Main Cabin", "Premium Economy", "First Class"]
WINDOWS = ["Morning", "Afternoon", "Evening"]

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
        "Dismiss popups or banners if any (e.g., cookie consent).",
        "Do not book or purchase anything; only search and view results.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.aa.com'.",
        "Ensure the booking section is visible on the homepage.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, ensure the calendar is closed."

def _instr(steps: list[str]) -> dict:
    return get_instruction("American Airlines", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus on the 'From' field.",
        f"{p}Clear the field and type '{origin}' into it.",
        f"{p}Select '{origin}' from the suggested options.",
        f"{p}Ensure it confirms '{origin}' as the selected departure city.",
        f"Close any dropdowns before proceeding.",
        f"{p}Focus on the 'To' field.",
        f"{p}Clear the field and type '{dest}' into it.",
        f"{p}Select '{dest}' from the suggested options.",
        f"{p}Ensure it confirms '{dest}' as the selected destination city.",
        f"Close any dropdowns before proceeding.",
    ]

def aa_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True, domestic=True)
    steps = _book_home() + [
        "Select 'One Way' journey type.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date as '{t['depart']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search' to view available flights.",
    ]
    return {"task_type": "aa_one_way_search", **t, "steps": steps}

def aa_round_trip_search(_: dict) -> dict:
    t = _trip_base(domestic=True)
    steps = _book_home() + [
        "Select 'Round Trip' journey type.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date as '{t['depart']}' and return date as '{t['return']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search' to view available flights.",
    ]
    return {"task_type": "aa_round_trip_search", **t, "steps": steps}

def aa_filter_nonstop(_: dict) -> dict:
    base = aa_round_trip_search({})
    base["task_type"] = "aa_filter_nonstop"
    base["steps"] += ["Enable the 'Nonstop' filter to refine the search results.", "Ensure all dropdowns are closed before proceeding."]
    return base

def aa_filter_cabin(_: dict) -> dict:
    base = aa_round_trip_search({})
    cabin = random.choice(CABINS_EASY)
    base["task_type"] = "aa_filter_cabin"
    base["target_cabin"] = cabin
    base["steps"] += [f"Filter results to show only '{cabin}'.", "Ensure all dropdowns are closed before proceeding."]
    return base

def aa_sort_lowest(_: dict) -> dict:
    base = aa_round_trip_search({})
    base["task_type"] = "aa_sort_lowest"
    base["steps"] += ["Sort the flight results by lowest price first.", "Ensure all dropdowns are closed before proceeding."]
    return base

def aa_offer_explore(_: dict) -> dict:
    steps = [
        "Go to the 'Special Offers' section on 'https://www.aa.com'.",
        *_ui_hygiene(),
        "Explore the current offers and summarize one offer you find interesting.",
    ]
    return {"task_type": "aa_offer_explore", "steps": steps}

def aa_travel_alerts(_: dict) -> dict:
    steps = [
        "Go to the 'Travel Alerts' section on 'https://www.aa.com/i18n/travel-info/travel-alerts.jsp'.",
        *_ui_hygiene(),
        "List any current travel alerts that might affect flights.",
    ]
    return {"task_type": "aa_travel_alerts", "steps": steps}

def aa_check_baggage_fees(_: dict) -> dict:
    steps = [
        "Go to the URL 'https://www.aa.com/i18n/customer-service/support/optional-service-fees.jsp'.",
        *_ui_hygiene(),
        "Locate and summarize the first checked baggage fees for domestic flights.",
    ]
    return {"task_type": "aa_check_baggage_fees", "steps": steps}

def aa_flight_extras(_: dict) -> dict:
    steps = [
        "Navigate to the 'Add-ons & Extras' page on 'https://www.aa.com/i18n/travel-info/optional-services'.",
        *_ui_hygiene(),
        "Identify and list two available flight extra services.",
    ]
    return {"task_type": "aa_flight_extras", "steps": steps}

_TASK_GENERATORS: Dict[AA_TASK_TYPES, Callable[[dict], dict]] = {
    "aa_one_way_search": aa_one_way_search,
    "aa_round_trip_search": aa_round_trip_search,
    "aa_filter_nonstop": aa_filter_nonstop,
    "aa_filter_cabin": aa_filter_cabin,
    "aa_sort_lowest": aa_sort_lowest,
    "aa_offer_explore": aa_offer_explore,
    "aa_travel_alerts": aa_travel_alerts,
    "aa_check_baggage_fees": aa_check_baggage_fees,
    "aa_flight_extras": aa_flight_extras,
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