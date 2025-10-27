import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

HA_TASK_TYPES = Literal[
    "ha_one_way_search",
    "ha_round_trip_search",
    "ha_filter_nonstop",
    "ha_sort_lowest",
    "ha_baggage_info",
    "ha_join_rewards",
    "ha_explore_destinations",
]

HA_SAMPLING_CONFIG: Dict[HA_TASK_TYPES, int] = {
    "ha_one_way_search": 10,
    "ha_round_trip_search": 10,
    "ha_filter_nonstop": 10,
    "ha_sort_lowest": 10,
    "ha_baggage_info": 10,
    "ha_join_rewards": 10,
    "ha_explore_destinations": 10,
}

AIRPORTS = ["HNL", "OGG", "KOA", "LIH", "ITO", "JHM"]
INTL = ["LAX", "SFO", "SEA", "JFK", "ORD"]
EASY_PAIRS = [("HNL", "OGG"), ("KOA", "HNL"), ("LIH", "ITO"), ("JHM", "OGG")]
WINDOWS = ["Morning (5–11am)", "Afternoon (12–5pm)"]
BAGS = ["carry-on size/weight", "first checked bag fees", "oversize/overweight fees"]

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
        "Dismiss popups/banners (e.g., 'Accept cookies').",
        "Do not book or purchase anything; only search and view results.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.hawaiianairlines.com' with the booking widget visible.",
        "Ensure the booking widget is active.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, click 'Done' on the calendar/date picker."

def _instr(steps: list[str]) -> dict:
    return get_instruction("Hawaiian Airlines", steps).model_dump()

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

def ha_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True, domestic=True)
    steps = _book_home() + [
        "Select 'One Way' and press Enter to confirm.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set depart date to '{t['depart']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search Flights' to view results.",
    ]
    return {"task_type": "ha_one_way_search", **t, "steps": steps}

def ha_round_trip_search(_: dict) -> dict:
    t = _trip_base(domestic=True)
    steps = _book_home() + [
        "Select 'Round Trip' and press Enter to confirm.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set dates: depart '{t['depart']}', return '{t['return']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search Flights' to view results.",
    ]
    return {"task_type": "ha_round_trip_search", **t, "steps": steps}

def ha_filter_nonstop(_: dict) -> dict:
    base = ha_round_trip_search({})
    base["task_type"] = "ha_filter_nonstop"
    base["steps"] += ["Enable the 'Nonstop' filter.", "Ensure any search box/dropdown is closed before continuing."]
    return base

def ha_sort_lowest(_: dict) -> dict:
    base = ha_round_trip_search({})
    base["task_type"] = "ha_sort_lowest"
    base["steps"] += ["Sort by lowest price.", "Ensure any search box/dropdown is closed before continuing."]
    return base

def ha_baggage_info(_: dict) -> dict:
    focus = random.choice(BAGS)
    steps = [
        "Go to url 'https://www.hawaiianairlines.com/legal/domestic-special-baggage'.",
        *_ui_hygiene(),
        f"Find and summarize: {focus}.",
    ]
    return {"task_type": "ha_baggage_info", "focus": focus, "steps": steps}

def ha_join_rewards(_: dict) -> dict:
    verify = random.choice(["name/email fields", "password requirements", "terms and conditions checkbox"])
    steps = [
        "Go to url 'https://www.hawaiianairlines.com/hawaiianmiles/join'.",
        *_ui_hygiene(),
        f"Verify the presence of {verify}.",
    ]
    return {"task_type": "ha_join_rewards", "verify": verify, "steps": steps}

def ha_explore_destinations(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.hawaiianairlines.com/destinations'.",
        *_ui_hygiene(),
        "Choose a destination and note the first visible blurb or offer.",
    ]
    return {"task_type": "ha_explore_destinations", "steps": steps}

_TASK_GENERATORS: Dict[HA_TASK_TYPES, Callable[[dict], dict]] = {
    "ha_one_way_search": ha_one_way_search,
    "ha_round_trip_search": ha_round_trip_search,
    "ha_filter_nonstop": ha_filter_nonstop,
    "ha_sort_lowest": ha_sort_lowest,
    "ha_baggage_info": ha_baggage_info,
    "ha_join_rewards": ha_join_rewards,
    "ha_explore_destinations": ha_explore_destinations,
}

def generate_ha_task(task_type: HA_TASK_TYPES, payload: dict) -> dict:
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
    items = list(HA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_ha_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)