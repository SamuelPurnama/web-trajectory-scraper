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
    "spirit_filter_bag_options",
    "spirit_sort_lowest",
    "spirit_price_cap",
    "spirit_view_fares",
    "spirit_flight_status",
    "spirit_contact_us",
]

SPIRIT_SAMPLING_CONFIG: Dict[SPIRIT_TASK_TYPES, int] = {
    "spirit_one_way_search": 10,
    "spirit_round_trip_search": 10,
    "spirit_filter_nonstop": 10,
    "spirit_filter_bag_options": 10,
    "spirit_sort_lowest": 10,
    "spirit_price_cap": 10,
    "spirit_view_fares": 10,
    "spirit_flight_status": 10,
    "spirit_contact_us": 10,
}

AIRPORTS = ["BOS", "MIA", "LAX", "ORD", "JFK", "LAS", "DFW", "DEN", "ATL", "MCO"]
int_purch = [("LAX", "MIA"), ("BOS", "JFK"), ("LAS", "DFW"), ("ORD", "ATL")]
BAG_OPTIONS = ["carry-on bag", "checked bag", "oversize bag"]
PRICE_CAPS = [50, 100, 150, 200]
DEPARTURE_WINDOWS = ["Morning (5am–11am)", "Afternoon (12pm–5pm)"]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_details(oneway=False):
    if random.random() < 0.8 and int_purch:
        frm, to = random.choice(int_purch)
    else:
        frm, to = random.sample(AIRPORTS, 2)
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": frm, "to": to, "depart": dep, "return": ret, "adults": 1}

def _ui_cleanups() -> list[str]:
    return [
        "Close or dismiss any pop-ups or modals that appear.",
        "Do not proceed with any purchase actions.",
    ]

def _spirit_home() -> list[str]:
    return [
        "Navigate to 'https://www.spirit.com' with the flight booking interface accessible.",
        *_ui_cleanups(),
    ]

def _confirm_step() -> str:
    return "After inputting travel details, confirm selection by pressing Enter or clicking the relevant button."

def _instr(steps: list[str]) -> dict:
    return get_instruction("Spirit", steps).model_dump()

def _flight_details_steps(frm: str, to: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Click on the 'From' field.",
        f"{p}Clear default input, if present.",
        f"{p}Input '{frm}' as origin airport.",
        f"{p}Confirm selection for '{frm}' from the suggestion.",
        f"{p}Ensure dropdown closes.",
        f"{p}Proceed to 'To' field.",
        f"{p}Clear any existing entry.",
        f"{p}Input '{to}' as destination.",
        f"{p}Select the correct '{to}' airport suggestion.",
        f"{p}Verify the dropdown closure.",
    ]

def spirit_one_way_search(_: dict) -> dict:
    t = _trip_details(oneway=True)
    steps = _spirit_home() + [
        "Select 'One Way' option.",
        *_flight_details_steps(t["from"], t["to"]),
        f"Input departure date as '{t['depart']}'.",
        _confirm_step(),
        "Set number of travelers to 1 adult.",
        "Click 'Search' to proceed.",
    ]
    return {"task_type": "spirit_one_way_search", **t, "steps": steps}

def spirit_round_trip_search(_: dict) -> dict:
    t = _trip_details()
    steps = _spirit_home() + [
        "Select 'Round Trip' flight option.",
        *_flight_details_steps(t["from"], t["to"]),
        f"Input dates: Departure on '{t['depart']}' and return on '{t['return']}'.",
        _confirm_step(),
        "Set number of travelers to 1 adult.",
        "Proceed by clicking 'Search'.",
    ]
    return {"task_type": "spirit_round_trip_search", **t, "steps": steps}

def spirit_filter_nonstop(_: dict) -> dict:
    base = spirit_round_trip_search({})
    base["task_type"] = "spirit_filter_nonstop"
    base["steps"] += [
        "Select the 'Nonstop only' flights filter.",
        "Continue exploring with the applied filter.",
    ]
    return base

def spirit_filter_bag_options(_: dict) -> dict:
    base = spirit_round_trip_search({})
    bag = random.choice(BAG_OPTIONS)
    base["task_type"] = "spirit_filter_bag_options"
    base["steps"] += [
        f"Apply '{bag}' filter from the baggage options.",
        "Reevaluate options with the applied filter.",
    ]
    return base

def spirit_sort_lowest(_: dict) -> dict:
    base = spirit_round_trip_search({})
    base["task_type"] = "spirit_sort_lowest"
    base["steps"] += [
        "Sort flights by lowest airfare.",
        "Verify the sorting reflects in results.",
    ]
    return base

def spirit_price_cap(_: dict) -> dict:
    cap = random.choice(PRICE_CAPS)
    base = spirit_round_trip_search({})
    base["task_type"] = "spirit_price_cap"
    base["price_limit"] = cap
    base["steps"] += [
        f"Search for flights under ${cap}.",
        "Note exact details if matching results are found.",
    ]
    return base

def spirit_view_fares(_: dict) -> dict:
    base = spirit_round_trip_search({})
    base["task_type"] = "spirit_view_fares"
    base["steps"] += [
        "Open fare details for the top flight result.",
        "Ensure fare breakdowns and fees are visible.",
    ]
    return base

def spirit_flight_status(_: dict) -> dict:
    flight_num = random.choice(["NK100", "NK200", "NK300"])
    steps = [
        "Navigate to 'https://www.spirit.com/flight-status'.",
        *_ui_cleanups(),
        f"Input flight number '{flight_num}' and date near '{_rand_date()}'.",
        "Submit request and observe results.",
    ]
    return {"task_type": "spirit_flight_status", "flight_number": flight_num, "steps": steps}

def spirit_contact_us(_: dict) -> dict:
    topic = random.choice(["Refunds", "Baggage Questions", "Flight Changes"])
    steps = [
        "Navigate to 'https://www.spirit.com/s/contact-us'.",
        *_ui_cleanups(),
        f"Locate the section related to '{topic}'.",
        "Validate contact instructions or steps.",
    ]
    return {"task_type": "spirit_contact_us", "topic": topic, "steps": steps}

_TASK_GENERATORS: Dict[SPIRIT_TASK_TYPES, Callable[[dict], dict]] = {
    "spirit_one_way_search": spirit_one_way_search,
    "spirit_round_trip_search": spirit_round_trip_search,
    "spirit_filter_nonstop": spirit_filter_nonstop,
    "spirit_filter_bag_options": spirit_filter_bag_options,
    "spirit_sort_lowest": spirit_sort_lowest,
    "spirit_price_cap": spirit_price_cap,
    "spirit_view_fares": spirit_view_fares,
    "spirit_flight_status": spirit_flight_status,
    "spirit_contact_us": spirit_contact_us,
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