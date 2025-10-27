import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

FLIGHTAWARE_TASK_TYPES = Literal[
    "check_flight_status",
    "explore_misery_map",
    "find_flight",
    "explore_cancelled_flights",
    "airport_delays",
    "browse_operator_fleet",
    "photo_exploration",
    "signup_process",
    "privacy_terms_verification"
]

FLIGHTAWARE_SAMPLING_CONFIG: Dict[FLIGHTAWARE_TASK_TYPES, int] = {
    "check_flight_status": 10,
    "explore_misery_map": 10,
    "find_flight": 10,
    "explore_cancelled_flights": 10,
    "airport_delays": 10,
    "browse_operator_fleet": 10,
    "photo_exploration": 10,
    "signup_process": 10,
    "privacy_terms_verification": 10,
}

FLIGHT_NUMS = ["AA100", "DL404", "UA1818", "WN300", "AS28", "NK340"]

def _rand_date(start_days=1, end_days=3) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or notifications.",
        "Do not attempt to perform any actions requiring purchase or login.",
    ]

def _check_flight_status(_: dict) -> dict:
    flight_number = random.choice(FLIGHT_NUMS)
    steps = [
        "Go to url 'https://www.flightaware.com/live'.",
        f"Search for flight number '{flight_number}'.",
        "Verify the flight status is displayed on the screen, including departure and arrival times.",
    ] + _ui_hygiene()
    return {"task_type": "check_flight_status", "flight_number": flight_number, "steps": steps}

def _explore_misery_map(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flightaware.com/miserymap/'.",
        "Zoom into a specific region to explore the map.",
        "Note any airports highlighted on the MiseryMap with visible delays or issues.",
    ] + _ui_hygiene()
    return {"task_type": "explore_misery_map", "steps": steps}

def _find_flight(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flightaware.com/live/findflight/'.",
        "Search for a non-stop flight from 'JFK' to 'LAX'.",
        "Verify a list of flights is displayed with corresponding airlines and timings.",
    ] + _ui_hygiene()
    return {"task_type": "find_flight", "steps": steps}

def _explore_cancelled_flights(_: dict) -> dict:
    date = _rand_date()
    steps = [
        "Go to url 'https://www.flightaware.com/live/cancelled/'.",
        f"Select the date '{date}'.",
        "Verify a list of cancelled flights is shown for the selected date.",
    ] + _ui_hygiene()
    return {"task_type": "explore_cancelled_flights", "date": date, "steps": steps}

def _airport_delays(_: dict) -> dict:
    airport_code = random.choice(["JFK", "SFO", "ORD", "ATL", "LAX"])
    steps = [
        f"Go to url 'https://www.flightaware.com/live/airport/delays'.",
        f"Find delay details for the airport code '{airport_code}'.",
        "Verify delay information is displayed, such as duration and affected flights.",
    ] + _ui_hygiene()
    return {"task_type": "airport_delays", "airport_code": airport_code, "steps": steps}

def _browse_operator_fleet(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flightaware.com/live/fleet/'.",
        "Select any airline operator to view available fleet.",
        "Verify the fleet of aircrafts is listed with specific models and numbers.",
    ] + _ui_hygiene()
    return {"task_type": "browse_operator_fleet", "steps": steps}

def _photo_exploration(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flightaware.com/photos/'.",
        "Browse through the latest photos uploaded.",
        "Verify photo details, such as the uploader and date, are correctly displayed.",
    ] + _ui_hygiene()
    return {"task_type": "photo_exploration", "steps": steps}

def _signup_process(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flightaware.com/account/join'.",
        "Review the signup form fields available without submitting any data.",
        "Verify presence of fields like Email, Password, and Name.",
    ] + _ui_hygiene()
    return {"task_type": "signup_process", "steps": steps}

def _privacy_terms_verification(_: dict) -> dict:
    target_page = random.choice(["Privacy", "Terms of Use"])
    url_map = {
        "Privacy": "https://www.flightaware.com/about/privacy",
        "Terms of Use": "https://www.flightaware.com/about/termsofuse"
    }
    url = url_map[target_page]
    steps = [
        f"Go to url '{url}'.",
        f"Verify that the '{target_page}' page contains expected sections or headers.",
    ] + _ui_hygiene()
    return {"task_type": f"privacy_{target_page.lower()}", "focus": target_page, "steps": steps}

_TASK_GENERATORS: Dict[FLIGHTAWARE_TASK_TYPES, Callable[[dict], dict]] = {
    "check_flight_status": _check_flight_status,
    "explore_misery_map": _explore_misery_map,
    "find_flight": _find_flight,
    "explore_cancelled_flights": _explore_cancelled_flights,
    "airport_delays": _airport_delays,
    "browse_operator_fleet": _browse_operator_fleet,
    "photo_exploration": _photo_exploration,
    "signup_process": _signup_process,
    "privacy_terms_verification": _privacy_terms_verification,
}

def generate_flightaware_task(task_type: FLIGHTAWARE_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = get_instruction("FlightAware", task["steps"]).model_dump()
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(FLIGHTAWARE_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_flightaware_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)