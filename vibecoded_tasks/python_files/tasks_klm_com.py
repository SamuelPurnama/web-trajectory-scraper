import json, random, datetime as dt
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
    "klm_check_in",
    "klm_newsletter_signup",
    "klm_contact_options",
]

KLM_SAMPLING_CONFIG: Dict[KLM_TASK_TYPES, int] = {
    "klm_one_way_search": 10,
    "klm_round_trip_search": 10,
    "klm_filter_nonstop": 10,
    "klm_filter_cabin": 10,
    "klm_sort_lowest": 10,
    "klm_price_cap": 10,
    "klm_check_in": 10,
    "klm_newsletter_signup": 10,
    "klm_contact_options": 10,
}

AIRPORTS = ["AMS", "CDG", "FRA", "LHR", "MAD", "FCO", "SVO", "BCN", "IST", "CPT", "JFK", "NRT", "HKG"]
EASY_PAIRS = [("AMS", "CDG"), ("LHR", "AMS"), ("FRA", "MAD"), ("BCN", "IST")]
CABINS_EASY = ["Economy", "Business", "First"]
PRICE_CAPS = [100, 200, 300, 400, 500]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False, domestic=True):
    o, d = random.choice(EASY_PAIRS) if domestic else random.sample(AIRPORTS, 2)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups such as cookie consent notices.",
        "Do not book or purchase anything; only simulate interactions.",
    ]

def _booking_home() -> list[str]:
    return [
        "Go to url 'https://www.klm.com/' and ensure the booking widget is visible.",
        "Select the desired travel option tab (Flight, Car, Hotel).",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After selecting dates, click 'Done' to confirm selection."

def _instr(steps: list[str]) -> dict:
    return get_instruction("KLM", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus the 'Departure' field.",
        f"{p}Clear the input field, if needed.",
        f"{p}Enter '{origin}'.",
        f"{p}Choose the suggested option for '{origin}'.",
        f"{p}Focus the 'Destination' field.",
        f"{p}Enter '{dest}'.",
        f"{p}Select the suggested option for '{dest}'.",
    ]

def klm_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True, domestic=True)
    steps = _booking_home() + [
        "Select 'One Way'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date to '{t['depart']}'.",
        _calendar_done_step(),
        "Set number of travelers to 1.",
        "Press 'Search' to view available flights.",
    ]
    return {"task_type": "klm_one_way_search", **t, "steps": steps}

def klm_round_trip_search(_: dict) -> dict:
    t = _trip_base(domestic=False)
    steps = _booking_home() + [
        "Select 'Round Trip'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure to '{t['depart']}', and return to '{t['return']}'.",
        _calendar_done_step(),
        "Set number of travelers to 1 adult.",
        "Click 'Search' to display flight options.",
    ]
    return {"task_type": "klm_round_trip_search", **t, "steps": steps}

def klm_filter_nonstop(_: dict) -> dict:
    base = klm_round_trip_search({})
    base["task_type"] = "klm_filter_nonstop"
    base["steps"] += [
        "Apply filter for 'Nonstop flights only'.",
        "Ensure the dropdown is closed before continuing.",
    ]
    return base

def klm_filter_cabin(_: dict) -> dict:
    base = klm_round_trip_search({})
    cabin = random.choice(CABINS_EASY)
    base["task_type"] = "klm_filter_cabin"
    base["target_cabin"] = cabin
    base["steps"] += [
        f"Select cabin class '{cabin}'.",
        "Ensure any filters are applied correctly."
    ]
    return base

def klm_sort_lowest(_: dict) -> dict:
    base = klm_round_trip_search({})
    base["task_type"] = "klm_sort_lowest"
    base["steps"] += [
        "Sort results by 'Lowest Price'.",
        "Confirm results are sorted correctly."
    ]
    return base

def klm_price_cap(_: dict) -> dict:
    base = klm_round_trip_search({})
    cap = random.choice(PRICE_CAPS)
    base["task_type"] = "klm_price_cap"
    base["max_price"] = cap
    base["steps"] += [
        f"Apply a price filter to show flights under ${cap}.",
        "List the first available option, if present."
    ]
    return base

def klm_check_in(_: dict) -> dict:
    steps = [
        "Navigate to 'https://www.klm.com/check-in'.",
        *_ui_hygiene(),
        "Verify online check-in features are accessible.",
    ]
    return {"task_type": "klm_check_in", "steps": steps}

def klm_newsletter_signup(_: dict) -> dict:
    verify = random.choice(["name", "email", "promotional materials"])
    steps = [
        "Go to 'https://www.klm.com/subscription/subscribe'.",
        *_ui_hygiene(),
        f"Verify form fields for {verify} are visible."
    ]
    return {"task_type": "klm_newsletter_signup", "verify": verify, "steps": steps}

def klm_contact_options(_: dict) -> dict:
    steps = [
        "Visit url 'https://www.klm.com/contact'.",
        *_ui_hygiene(),
        "Check available contact options including phone and email.",
    ]
    return {"task_type": "klm_contact_options", "steps": steps}

_TASK_GENERATORS: Dict[KLM_TASK_TYPES, Callable[[dict], dict]] = {
    "klm_one_way_search": klm_one_way_search,
    "klm_round_trip_search": klm_round_trip_search,
    "klm_filter_nonstop": klm_filter_nonstop,
    "klm_filter_cabin": klm_filter_cabin,
    "klm_sort_lowest": klm_sort_lowest,
    "klm_price_cap": klm_price_cap,
    "klm_check_in": klm_check_in,
    "klm_newsletter_signup": klm_newsletter_signup,
    "klm_contact_options": klm_contact_options,
}

def generate_klm_task(task_type: KLM_TASK_TYPES, payload: dict) -> dict:
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
    items = list(KLM_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_klm_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)