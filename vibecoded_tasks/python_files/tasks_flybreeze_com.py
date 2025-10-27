import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

BREEZE_TASK_TYPES = Literal[
    "breeze_search_flight",
    "breeze_check_in",
    "breeze_flight_status",
    "breeze_view_destinations",
    "breeze_bag_pricing",
    "breeze_newsletter_signup",
    "breeze_contact_support"
]

BREEZE_SAMPLING_CONFIG: Dict[BREEZE_TASK_TYPES, int] = {
    "breeze_search_flight": 10,
    "breeze_check_in": 10,
    "breeze_flight_status": 10,
    "breeze_view_destinations": 10,
    "breeze_bag_pricing": 10,
    "breeze_newsletter_signup": 10,
    "breeze_contact_support": 10,
}

AIRPORTS = ["JFK", "LAX", "SFO", "ORD", "DFW", "DEN", "SEA", "ATL", "PHX", "LAS"]
EASY_PAIRS = [("JFK", "LAX"), ("SFO", "ORD"), ("ATL", "DFW")]

def _rand_date(start_days=10, end_days=60) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    o, d = random.choice(EASY_PAIRS)
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(2, 5))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss popups/banners that appear.",
        "Do not complete any purchase; only search and view data.",
    ]

def _basic_steps() -> list[str]:
    return [
        "Go to the Breeze Airways website.",
        "Ensure the site's homepage is fully loaded.",
        *_ui_hygiene(),
    ]

def breeze_search_flight(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _basic_steps() + [
        "Navigate to the Flights page.",
        "Enter the origin as {from} and destination as {to}.",
        f"Set the departure date to {t['depart']}.",
        "Search for available flights.",
        "Verify that flight search results are displayed."
    ]
    return {"task_type": "breeze_search_flight", **t, "steps": [s.format(**t) for s in steps]}

def breeze_check_in(_: dict) -> dict:
    t = {"last_name": "Doe", "confirmation_code": "ABC123"}
    steps = _basic_steps() + [
        "Navigate to the Check-in page.",
        "Input the last name as '{last_name}' and confirmation code as '{confirmation_code}'.",
        "Attempt to check in.",
        "Verify that the check-in process begins or gives an error due to missing or incorrect information."
    ]
    return {"task_type": "breeze_check_in", **t, "steps": [s.format(**t) for s in steps]}
    
def breeze_flight_status(_: dict) -> dict:
    steps = _basic_steps() + [
        "Navigate to the Flight Status page.",
        "Search for the status of any flight.",
        "Verify that the current status of the flight displays accurately."
    ]
    return {"task_type": "breeze_flight_status", "steps": steps}

def breeze_view_destinations(_: dict) -> dict:
    steps = _basic_steps() + [
        "Navigate to the Destinations page.",
        "Browse the list of available destinations.",
        "Verify that destination details and available flights are shown."
    ]
    return {"task_type": "breeze_view_destinations", "steps": steps}

def breeze_bag_pricing(_: dict) -> dict:
    steps = _basic_steps() + [
        "Navigate to the Bag Pricing page.",
        "Review the pricing details for carry-ons and checked bags.",
        "Verify the displayed pricing information is correct and updated."
    ]
    return {"task_type": "breeze_bag_pricing", "steps": steps}

def breeze_newsletter_signup(_: dict) -> dict:
    t = {"email": "example@test.com"}
    steps = _basic_steps() + [
        "Navigate to the Newsletter Signup page.",
        "Enter an email address: {email}.",
        "Attempt to subscribe to the newsletter.",
        "Verify a success or error message is displayed."
    ]
    return {"task_type": "breeze_newsletter_signup", **t, "steps": [s.format(**t) for s in steps]}

def breeze_contact_support(_: dict) -> dict:
    steps = _basic_steps() + [
        "Navigate to the Contact Support page.",
        "Find contact information or a form to submit a support query.",
        "Verify that contact options are clearly displayed and accessible."
    ]
    return {"task_type": "breeze_contact_support", "steps": steps}

_TASK_GENERATORS: Dict[BREEZE_TASK_TYPES, Callable[[dict], dict]] = {
    "breeze_search_flight": breeze_search_flight,
    "breeze_check_in": breeze_check_in,
    "breeze_flight_status": breeze_flight_status,
    "breeze_view_destinations": breeze_view_destinations,
    "breeze_bag_pricing": breeze_bag_pricing,
    "breeze_newsletter_signup": breeze_newsletter_signup,
    "breeze_contact_support": breeze_contact_support,
}

def generate_breeze_task(task_type: BREEZE_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = get_instruction("Breeze", task["steps"]).model_dump()
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(BREEZE_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_breeze_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)