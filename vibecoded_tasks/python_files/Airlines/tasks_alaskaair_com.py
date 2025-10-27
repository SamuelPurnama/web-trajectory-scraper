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
    "alaska_sort_lowest",
    "alaska_checkin_info",
    "alaska_baggage_info",
    "alaska_mobile_app_info",
]

ALASKA_SAMPLING_CONFIG: Dict[ALASKA_TASK_TYPES, int] = {
    "alaska_one_way_search": 10,
    "alaska_round_trip_search": 10,
    "alaska_filter_nonstop": 10,
    "alaska_sort_lowest": 10,
    "alaska_checkin_info": 10,
    "alaska_baggage_info": 10,
    "alaska_mobile_app_info": 10,
}

AIRPORTS = ["SEA", "SFO", "LAX", "SAN"]
CABINS_EASY = ["Main Cabin", "Premium"]
BAGS_INFO = ["carry-on fee", "first checked bag fee"]
CHECKIN_FOCI = ["check-in options", "boarding pass retrieval", "luggage drop-off"]
MOBILE_INFO = ["book flights", "view itinerary", "check flight status"]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    o, d = random.choice(AIRPORTS), random.choice(AIRPORTS)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners.",
        "Do not make any purchases; only simulate search actions.",
    ]

def _book_home() -> list[str]:
    return [
        "Navigate to 'https://www.alaskaair.com' with the booking interface visible.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "Click 'Done' after selecting dates."

def _instr(steps: list[str]) -> dict:
    return get_instruction("Alaska", steps).model_dump()

def _from_to_steps(origin: str, dest: str) -> list[str]:
    return [
        f"Select the 'From' field and enter '{origin}', then confirm.",
        f"Select the 'To' field and enter '{dest}', then confirm.",
    ]

def alaska_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _book_home() + [
        "Select 'One Way'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set the departure date to '{t['depart']}'.",
        _calendar_done_step(),
        "Set number of travelers to 1 adult.",
        "Click 'Search' to view available flights.",
    ]
    return {"task_type": "alaska_one_way_search", **t, "steps": steps}

def alaska_round_trip_search(_: dict) -> dict:
    t = _trip_base()
    steps = _book_home() + [
        "Select 'Round Trip'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date to '{t['depart']}' and return date to '{t['return']}'.",
        _calendar_done_step(),
        "Set number of travelers to 1 adult.",
        "Click 'Search' to view available flights.",
    ]
    return {"task_type": "alaska_round_trip_search", **t, "steps": steps}

def alaska_filter_nonstop(_: dict) -> dict:
    base = alaska_round_trip_search({})
    base["task_type"] = "alaska_filter_nonstop"
    base["steps"] += ["Enable the 'Nonstop' filter.", "Ensure no open dropdowns remain before proceeding."]
    return base

def alaska_sort_lowest(_: dict) -> dict:
    base = alaska_round_trip_search({})
    base["task_type"] = "alaska_sort_lowest"
    base["steps"] += ["Sort results by lowest price.", "Ensure no open dropdowns remain before proceeding."]
    return base

def alaska_checkin_info(_: dict) -> dict:
    focus = random.choice(CHECKIN_FOCI)
    steps = [
        "Visit 'https://www.alaskaair.com'.",
        *_ui_hygiene(),
        f"Locate information regarding {focus}.",
    ]
    return {"task_type": "alaska_checkin_info", "focus": focus, "steps": steps}

def alaska_baggage_info(_: dict) -> dict:
    focus = random.choice(BAGS_INFO)
    steps = [
        "Navigate to 'https://www.alaskaair.com/content/travel-info/baggage'.",
        *_ui_hygiene(),
        f"Find and summarize details on: {focus}.",
    ]
    return {"task_type": "alaska_baggage_info", "focus": focus, "steps": steps}

def alaska_mobile_app_info(_: dict) -> dict:
    focus = random.choice(MOBILE_INFO)
    steps = [
        "Visit 'https://www.alaskaair.com/content/travel-info/mobile-app'.",
        *_ui_hygiene(),
        f"Confirm the app supports {focus}.",
    ]
    return {"task_type": "alaska_mobile_app_info", "focus": focus, "steps": steps}

_TASK_GENERATORS: Dict[ALASKA_TASK_TYPES, Callable[[dict], dict]] = {
    "alaska_one_way_search": alaska_one_way_search,
    "alaska_round_trip_search": alaska_round_trip_search,
    "alaska_filter_nonstop": alaska_filter_nonstop,
    "alaska_sort_lowest": alaska_sort_lowest,
    "alaska_checkin_info": alaska_checkin_info,
    "alaska_baggage_info": alaska_baggage_info,
    "alaska_mobile_app_info": alaska_mobile_app_info,
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