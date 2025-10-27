import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

AIRFRANCE_TASK_TYPES = Literal[
    "airfrance_one_way_search",
    "airfrance_round_trip_search",
    "airfrance_book_promo_fare",
    "airfrance_check_in",
    "airfrance_subscription_signup",
    "airfrance_flight_status_check",
    "airfrance_explore_all_deals",
]

AIRFRANCE_SAMPLING_CONFIG: Dict[AIRFRANCE_TASK_TYPES, int] = {
    "airfrance_one_way_search": 10,
    "airfrance_round_trip_search": 10,
    "airfrance_book_promo_fare": 10,
    "airfrance_check_in": 10,
    "airfrance_subscription_signup": 10,
    "airfrance_flight_status_check": 10,
    "airfrance_explore_all_deals": 10,
}

PROMO_FARES = [
    ("Barcelona", "USD 398", "https://www.airfrance.us/search?pax=1:0:0:0:0:0:0:0&cabinClass=ECONOMY&connections=JFK:A%3EBCN:C-BCN:C%3EJFK:A&bookingFlow=LEISURE"),
    ("Cairo", "USD 722", "https://www.airfrance.us/search?pax=1:0:0:0:0:0:0:0&cabinClass=ECONOMY&connections=JFK:A%3ECAI:C-CAI:C%3EJFK:A&bookingFlow=LEISURE"),
    ("Zanzibar", "USD 1,069", "https://www.airfrance.us/search?pax=1:0:0:0:0:0:0:0&cabinClass=ECONOMY&connections=JFK:A%3EZNZ:C-ZNZ:C%3EJFK:A&bookingFlow=LEISURE")
]

AIRPORT_PAIRS = [
    ("JFK", "LAX"),
    ("LAX", "SFO"),
    ("ATL", "MIA"),
    ("ORD", "DFW"),
    ("SEA", "DEN")
]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    o, d = random.choice(AIRPORT_PAIRS)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Ensure no sensitive information is shared.",
        "Do not attempt to make any purchases.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.airfrance.us' with the booking widget visible.",
        "Ensure the booking tab is visible.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, click 'Done' on the calendar/date picker."

def _instr(steps: list[str]) -> dict:
    return get_instruction("AirFrance", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus on the 'From' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{origin}'.",
        f"{p}Select the autocomplete option for '{origin}' (airport).",
        f"{p}Confirm origin shows '{origin}' and proceed.",
        f"{p}Focus on the 'To' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{dest}'.",
        f"{p}Select the autocomplete option for '{dest}' (airport).",
        f"{p}Confirm destination shows '{dest}' and proceed.",
    ]

def airfrance_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _book_home() + [
        "Select 'One Way' and proceed.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set depart date to '{t['depart']}'.",
        _calendar_done_step(),
        "Set passengers to 1 adult.",
        "Click 'Search' to view results.",
    ]
    return {"task_type":"airfrance_one_way_search",**t,"steps":steps}

def airfrance_round_trip_search(_: dict) -> dict:
    t = _trip_base(oneway=False)
    steps = _book_home() + [
        "Select 'Round Trip' and proceed.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set dates: depart '{t['depart']}', return '{t['return']}'.",
        _calendar_done_step(),
        "Set passengers to 1 adult.",
        "Click 'Search' to view results.",
    ]
    return {"task_type":"airfrance_round_trip_search",**t,"steps":steps}

def airfrance_book_promo_fare(_: dict) -> dict:
    city, price, url = random.choice(PROMO_FARES)
    steps = [
        f"Go to url '{url}'.",
        *_ui_hygiene(),
        f"Ensure the promo fare for {city} at {price} is displayed.",
    ]
    return {"task_type": "airfrance_book_promo_fare", "city": city, "price": price, "steps": steps}

def airfrance_check_in(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.airfrance.us/check-in'.",
        *_ui_hygiene(),
        "Verify the presence of check-in form fields such as Name and Booking Reference.",
    ]
    return {"task_type": "airfrance_check_in", "steps": steps}

def airfrance_subscription_signup(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.airfrance.us/en/subscription/subscribe'.",
        *_ui_hygiene(),
        "Verify the presence of subscription fields such as email and preferences.",
    ]
    return {"task_type": "airfrance_subscription_signup", "steps": steps}

def airfrance_flight_status_check(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.airfrance.us/flight-status'.",
        *_ui_hygiene(),
        "Check the availability of entering flight details for status updates.",
    ]
    return {"task_type": "airfrance_flight_status_check", "steps": steps}

def airfrance_explore_all_deals(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.airfrance.us/deals'.",
        *_ui_hygiene(),
        "Review current offers and ensure deals are displayed with details.",
    ]
    return {"task_type": "airfrance_explore_all_deals", "steps": steps}

TASK_GENERATORS: Dict[AIRFRANCE_TASK_TYPES, Callable[[dict], dict]] = {
    "airfrance_one_way_search": airfrance_one_way_search,
    "airfrance_round_trip_search": airfrance_round_trip_search,
    "airfrance_book_promo_fare": airfrance_book_promo_fare,
    "airfrance_check_in": airfrance_check_in,
    "airfrance_subscription_signup": airfrance_subscription_signup,
    "airfrance_flight_status_check": airfrance_flight_status_check,
    "airfrance_explore_all_deals": airfrance_explore_all_deals,
}

def generate_airfrance_task(task_type: AIRFRANCE_TASK_TYPES, payload: dict) -> dict:
    task = TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = _instr(task["steps"])
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): 
        payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(AIRFRANCE_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_airfrance_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: 
                out.append(fut.result(timeout=timeout))
            except Exception: 
                pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)