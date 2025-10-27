import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

KLM_TASK_TYPES = Literal[
    "klm_one_way_search",
    "klm_round_trip_search",
    "klm_filter_nonstop",
    "klm_filter_cabin",
    "klm_sort_lowest",
    "klm_price_cap",
    "klm_time_window_filter",
    "klm_fare_details",
    "klm_subscribe_newsletter",
]

KLM_SAMPLING_CONFIG: Dict[KLM_TASK_TYPES, int] = {
    "klm_one_way_search": 10,
    "klm_round_trip_search": 10,
    "klm_filter_nonstop": 10,
    "klm_filter_cabin": 10,
    "klm_sort_lowest": 10,
    "klm_price_cap": 10,
    "klm_time_window_filter": 10,
    "klm_fare_details": 10,
    "klm_subscribe_newsletter": 10,
}

AIRPORTS = ["JFK", "LAX", "AMS", "CDG", "FRA", "SIN", "SYD", "DXB", "HND", "GRU"]
EASY_PAIRS = [("JFK", "LAX"), ("AMS", "CDG"), ("SYD", "SIN"), ("DXB", "FRA"), ("HND", "GRU")]
CABINS = ["Economy", "Business", "First Class"]
WINDOWS = ["Morning", "Afternoon", "Evening"]
BAGS = ["carry-on size/weight", "first checked bag fees", "oversize/overweight fees"]
SUBSCRIBE_TOPICS = ["travel ideas", "network updates", "product information", "attractive fares"]

def _rand_date(start_days=10, end_days=30) -> str:
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
        "Dismiss popups or banners like 'Accept cookies'.",
        "Do not book or purchase anything; only search and view results.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.klm.com' with visible booking options.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After selecting dates, close the calendar/date picker."

def _instr(steps: list[str]) -> dict:
    return get_instruction("KLM", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus on the 'From' field.",
        f"{p}Clear/reset the field, type '{origin}', and select matching option.",
        f"{p}Confirm origin as '{origin}'.",
        f"{p}Focus on the 'To' field.",
        f"{p}Clear/reset the field, type '{dest}', and select matching option.",
        f"{p}Confirm destination as '{dest}'.",
    ]

def klm_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _book_home() + [
        "Select 'One Way'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date to '{t['depart']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search' to show results.",
    ]
    return {"task_type": "klm_one_way_search", **t, "steps": steps}

def klm_round_trip_search(_: dict) -> dict:
    t = _trip_base()
    steps = _book_home() + [
        "Select 'Round Trip'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set dates: depart '{t['depart']}', return '{t['return']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search' to show results.",
    ]
    return {"task_type": "klm_round_trip_search", **t, "steps": steps}

def klm_filter_nonstop(_: dict) -> dict:
    base = klm_round_trip_search({})
    base["task_type"] = "klm_filter_nonstop"
    base["steps"] += ["Enable the 'Nonstop' filter."]
    return base

def klm_filter_cabin(_: dict) -> dict:
    base = klm_round_trip_search({})
    cabin = random.choice(CABINS)
    base["task_type"] = "klm_filter_cabin"
    base["target_cabin"] = cabin
    base["steps"] += [f"Select cabin type '{cabin}'."]
    return base

def klm_sort_lowest(_: dict) -> dict:
    base = klm_round_trip_search({})
    base["task_type"] = "klm_sort_lowest"
    base["steps"] += ["Sort results by lowest price."]
    return base

def klm_price_cap(_: dict) -> dict:
    base = klm_round_trip_search({})
    cap_price = random.choice([200, 300, 400, 500, 600])
    base["task_type"] = "klm_price_cap"
    base["max_price"] = cap_price
    base["steps"] += [
        f"Apply price filter to show itineraries under ${cap_price}.",
    ]
    return base

def klm_time_window_filter(_: dict) -> dict:
    base = klm_round_trip_search({})
    time_window = random.choice(WINDOWS)
    base["task_type"] = "klm_time_window_filter"
    base["window"] = time_window
    base["steps"] += [
        f"Set departure time window to {time_window}.",
    ]
    return base

def klm_fare_details(_: dict) -> dict:
    base = klm_round_trip_search({})
    base["task_type"] = "klm_fare_details"
    base["focus"] = "fare rules panel"
    base["steps"] += [
        "View fare details on first result to confirm a fare rules panel is available."
    ]
    return base

def klm_subscribe_newsletter(_: dict) -> dict:
    topic = random.choice(SUBSCRIBE_TOPICS)
    steps = [
        "Go to url 'https://www.klm.com/subscription/subscribe'.",
        *_ui_hygiene(),
        f"Subscribe to newsletter on '{topic}' by entering valid email and confirming subscription.",
    ]
    return {"task_type": "klm_subscribe_newsletter", "focus": topic, "steps": steps}

_TASK_GENERATORS: Dict[KLM_TASK_TYPES, Callable[[dict], dict]] = {
    "klm_one_way_search": klm_one_way_search,
    "klm_round_trip_search": klm_round_trip_search,
    "klm_filter_nonstop": klm_filter_nonstop,
    "klm_filter_cabin": klm_filter_cabin,
    "klm_sort_lowest": klm_sort_lowest,
    "klm_price_cap": klm_price_cap,
    "klm_time_window_filter": klm_time_window_filter,
    "klm_fare_details": klm_fare_details,
    "klm_subscribe_newsletter": klm_subscribe_newsletter,
}

def generate_klm_task(task_type: KLM_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = _instr(task["steps"])
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 10, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(KLM_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_klm_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try:
                out.append(fut.result(timeout=timeout))
            except Exception as e:
                print(e)
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)