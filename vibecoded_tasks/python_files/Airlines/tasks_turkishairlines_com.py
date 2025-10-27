import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

THY_TASK_TYPES = Literal[
    "thy_one_way_search",
    "thy_round_trip_search",
    "thy_book_flight",
    "thy_manage_booking",
    "thy_check_flight_status",
    "thy_flight_deals",
    "thy_miles_smiles_info",
]

THY_SAMPLING_CONFIG: Dict[THY_TASK_TYPES, int] = {
    "thy_one_way_search": 10,
    "thy_round_trip_search": 10,
    "thy_book_flight": 10,
    "thy_manage_booking": 10,
    "thy_check_flight_status": 10,
    "thy_flight_deals": 10,
    "thy_miles_smiles_info": 10,
}

AIRPORTS = ["IST", "ANK", "ADB", "ESB", "AYT", "SAW", "SZF", "VAS"]
INTL_AIRPORTS = ["JFK", "LHR", "CDG", "FRA", "AMS", "SFO", "ORD", "LAX"]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(one_way=False, domestic=True):
    if domestic:
        o, d = random.sample(AIRPORTS, 2)
    else:
        o = random.choice(AIRPORTS)
        d = random.choice(INTL_AIRPORTS)
    pax = 1
    dep = _rand_date()
    ret = None if one_way else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss popups/banners (e.g., 'I understand', 'Join Miles&Smiles', 'Subscribe').",
        "Do not book or purchase anything; only search and view results.",
    ]

def _flight_search_home() -> list[str]:
    return [
        "Go to url 'https://www.turkishairlines.com/en-us/flights/booking/'.",
        "Ensure the flight search widget is active.",
        *_ui_hygiene(),
    ]

def _from_to_steps(origin: str, dest: str) -> list[str]:
    return [
        f"Focus the 'From' field and clear any existing text.",
        f"Type '{origin}' and select the correct airport from the dropdown.",
        f"Focus the 'To' field and clear any existing text.",
        f"Type '{dest}' and select the correct airport from the dropdown.",
    ]

def thy_one_way_search(_: dict) -> dict:
    t = _trip_base(one_way=True, domestic=True)
    steps = _flight_search_home() + [
        "Select 'One Way' option.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set depart date to '{t['depart']}'.",
        "Set travelers to 1 adult.",
        "Click 'Search Flights' to view results.",
    ]
    return {"task_type": "thy_one_way_search", **t, "steps": steps}

def thy_round_trip_search(_: dict) -> dict:
    t = _trip_base(domestic=True)
    steps = _flight_search_home() + [
        "Select 'Round Trip' option.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set depart date to '{t['depart']}' and return date to '{t['return']}'.",
        "Set travelers to 1 adult.",
        "Click 'Search Flights' to view results.",
    ]
    return {"task_type": "thy_round_trip_search", **t, "steps": steps}

def thy_book_flight(_: dict) -> dict:
    t = _trip_base(domestic=False)
    steps = _flight_search_home() + [
        "Ensure 'Round Trip' is selected.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set depart date to '{t['depart']}' and return date to '{t['return']}'.",
        "Set travelers to 1 adult.",
        "Click 'Search Flights' to proceed to booking options.",
        "Note: Only view booking options; do not proceed to payment.",
    ]
    return {"task_type": "thy_book_flight", **t, "steps": steps}

def thy_manage_booking(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.turkishairlines.com/en-us/flights/manage-booking/'.",
        *_ui_hygiene(),
        "Enter a mock PNR and surname to access the 'Manage Booking' section.",
        "Ensure navigation is consistent without performing actual changes.",
    ]
    return {"task_type": "thy_manage_booking", "steps": steps}

def thy_check_flight_status(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.turkishairlines.com/en-us/flights/flight-status/'.",
        *_ui_hygiene(),
        "Use flight number 'TK123' and current date to check flight status.",
        "Verify the status and schedule without making any changes.",
    ]
    return {"task_type": "thy_check_flight_status", "steps": steps}

def thy_flight_deals(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.turkishairlines.com/en-us/flight-deals/'.",
        *_ui_hygiene(),
        "Browse the listed deals and report the first domestic and international offer.",
        "Note down the destination and price for each deal.",
    ]
    return {"task_type": "thy_flight_deals", "steps": steps}

def thy_miles_smiles_info(_: dict) -> dict:
    focus = random.choice(["membership benefits", "earning miles", "redeeming miles"])
    steps = [
        "Go to url 'https://www.turkishairlines.com/en-us/miles-and-smiles/'.",
        *_ui_hygiene(),
        f"Navigate to the section on {focus} and summarize the key points.",
        "Ensure the information is relevant and up-to-date based on the visit.",
    ]
    return {"task_type": "thy_miles_smiles_info", "steps": steps, "focus": focus}

_TASK_GENERATORS: Dict[THY_TASK_TYPES, Callable[[dict], dict]] = {
    "thy_one_way_search": thy_one_way_search,
    "thy_round_trip_search": thy_round_trip_search,
    "thy_book_flight": thy_book_flight,
    "thy_manage_booking": thy_manage_booking,
    "thy_check_flight_status": thy_check_flight_status,
    "thy_flight_deals": thy_flight_deals,
    "thy_miles_smiles_info": thy_miles_smiles_info,
}

def generate_thy_task(task_type: THY_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 10, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list):
        payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(THY_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_thy_task, ttype, p))
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