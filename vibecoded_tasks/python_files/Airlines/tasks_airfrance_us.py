import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

AIRFRANCE_TASK_TYPES = Literal[
    "airfrance_one_way_search",
    "airfrance_round_trip_search",
    "airfrance_check_flight_status",
    "airfrance_browse_deals",
    "airfrance_view_destinations",
    "airfrance_contact_support",
    "airfrance_view_app_info",
]

AIRFRANCE_SAMPLING_CONFIG: Dict[AIRFRANCE_TASK_TYPES, int] = {
    "airfrance_one_way_search": 10,
    "airfrance_round_trip_search": 10,
    "airfrance_check_flight_status": 10,
    "airfrance_browse_deals": 10,
    "airfrance_view_destinations": 10,
    "airfrance_contact_support": 10,
    "airfrance_view_app_info": 10,
}

AIRPORTS = ["JFK", "CDG", "LHR", "AMS", "FRA", "NRT", "HND", "LAX", "SFO", "ORD"]
CABINS = ["Economy", "Premium Economy", "Business", "First"]
DEAL_CITIES = ["Bengaluru", "Florence", "Nairobi", "Dubai", "Paris", "Cairo"]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    o, d = random.sample(AIRPORTS, 2)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners that appear on the website.",
        "Only explore information; do not attempt to purchase anything.",
    ]

def _general_steps() -> list[str]:
    return [
        "Navigate to the Air France website 'https://www.airfrance.us'.",
        *_ui_hygiene(),
    ]

def _flight_search_steps(oneway: bool = False) -> list[str]:
    t = _trip_base(oneway=oneway)
    flight_type = "One way" if oneway else "Round trip"
    return [
        f"Select '{flight_type}' in the flight booking options.",
        f"Enter '{t['from']}' in the 'From' field.",
        f"Enter '{t['to']}' in the 'To' field.",
        f"Set the departure date to '{t['depart']}'.",
        *(["Set the return date to '{t['return']}'." if not oneway else []]),
        "Confirm search parameters and look at available flights.",
    ]

def airfrance_one_way_search(_: dict) -> dict:
    steps = _general_steps() + _flight_search_steps(oneway=True)
    return {"task_type": "airfrance_one_way_search", "steps": steps}

def airfrance_round_trip_search(_: dict) -> dict:
    steps = _general_steps() + _flight_search_steps(oneway=False)
    return {"task_type": "airfrance_round_trip_search", "steps": steps}

def airfrance_check_flight_status(_: dict) -> dict:
    flight_num = f"AF{random.randint(100, 999)}"
    steps = _general_steps() + [
        "Click on the 'Flight status' link.",
        f"Enter flight number '{flight_num}' and view the status.",
        "Check for updates or changes to the flight schedule.",
    ]
    return {"task_type": "airfrance_check_flight_status", "flight_number": flight_num, "steps": steps}

def airfrance_browse_deals(_: dict) -> dict:
    city = random.choice(DEAL_CITIES)
    steps = _general_steps() + [
        "Navigate to the 'Deals' section.",
        f"Look for any promotional deals for flights to or from '{city}'.",
        "Note any available discounts or special offers displayed for a limited time.",
    ]
    return {"task_type": "airfrance_browse_deals", "deal_city": city, "steps": steps}

def airfrance_view_destinations(_: dict) -> dict:
    steps = _general_steps() + [
        "Access the 'Travel destinations' page.",
        "Explore various destinations offered by Air France.",
        "Select any interesting location and note down information provided such as attractions or travel tips.",
    ]
    return {"task_type": "airfrance_view_destinations", "steps": steps}

def airfrance_contact_support(_: dict) -> dict:
    support_option = random.choice(["Refund", "Claims", "Invoice Request"])
    steps = _general_steps() + [
        "Open the 'Contact us' page.",
        f"Select the support option for '{support_option}'.",
        "View instructions and requirements for submitting a request.",
    ]
    return {"task_type": "airfrance_contact_support", "support_option": support_option, "steps": steps}

def airfrance_view_app_info(_: dict) -> dict:
    steps = _general_steps() + [
        "Go to the 'Air France app' page.",
        "Review features highlighted for the mobile app, such as booking management or flight notifications.",
        "Note any available information for downloading the app.",
    ]
    return {"task_type": "airfrance_view_app_info", "steps": steps}

_TASK_GENERATORS: Dict[AIRFRANCE_TASK_TYPES, Callable[[dict], dict]] = {
    "airfrance_one_way_search": airfrance_one_way_search,
    "airfrance_round_trip_search": airfrance_round_trip_search,
    "airfrance_check_flight_status": airfrance_check_flight_status,
    "airfrance_browse_deals": airfrance_browse_deals,
    "airfrance_view_destinations": airfrance_view_destinations,
    "airfrance_contact_support": airfrance_contact_support,
    "airfrance_view_app_info": airfrance_view_app_info,
}

def generate_airfrance_task(task_type: AIRFRANCE_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = get_instruction("Air France", task["steps"]).model_dump()
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