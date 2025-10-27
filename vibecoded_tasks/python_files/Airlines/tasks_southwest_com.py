import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

SWA_TASK_TYPES = Literal[
    "swa_one_way_search",
    "swa_round_trip_search",
    "swa_filter_nonstop",
    "swa_select_fare_type",
    "swa_view_flight_status",
    "swa_checkin_flow",
    "swa_manage_booking",
]

SWA_SAMPLING_CONFIG: Dict[SWA_TASK_TYPES, int] = {
    "swa_one_way_search": 10,
    "swa_round_trip_search": 10,
    "swa_filter_nonstop": 10,
    "swa_select_fare_type": 10,
    "swa_view_flight_status": 10,
    "swa_checkin_flow": 10,
    "swa_manage_booking": 10,
}

SWA_AIRPORTS = ["DAL", "HOU", "MDW", "LAS", "DEN", "PHX", "BWI", "MCO", "LAX", "ATL"]
FARE_TYPES = ["Business Select", "Anytime", "Wanna Get Away"]
STATUS_CODES = ["On Time", "Delayed", "Cancelled"]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    o, d = random.sample(SWA_AIRPORTS, 2)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss popups or banners.",
        "Do not book or purchase anything; only search and view results.",
    ]

def _swa_home() -> list[str]:
    return [
        "Go to url 'https://www.southwest.com' with the booking widget visible.",
        "Ensure the 'Flight' tab is active.",
        *_ui_hygiene(),
    ]

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    return [
        f"{prefix}Focus the 'Departure City' field and type '{origin}'.",
        f"{prefix}Select '{origin}' from autocomplete.",
        f"{prefix}Focus the 'Destination City' field and type '{dest}'.",
        f"{prefix}Select '{dest}' from autocomplete.",
    ]

def swa_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _swa_home() + [
        "Select 'One Way'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date to '{t['depart']}'.",
        "Set travelers to 1 adult.",
        "Click 'Search' to see available flights.",
    ]
    return {"task_type": "swa_one_way_search", **t, "steps": steps}

def swa_round_trip_search(_: dict) -> dict:
    t = _trip_base(oneway=False)
    steps = _swa_home() + [
        "Select 'Round Trip'.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date to '{t['depart']}' and return date to '{t['return']}'.",
        "Set travelers to 1 adult.",
        "Click 'Search' to see available flights.",
    ]
    return {"task_type": "swa_round_trip_search", **t, "steps": steps}

def swa_filter_nonstop(_: dict) -> dict:
    base = swa_round_trip_search({})
    base["task_type"] = "swa_filter_nonstop"
    base["steps"] += ["Enable the 'Nonstop' filter on the search results page."]
    return base

def swa_select_fare_type(_: dict) -> dict:
    base = swa_round_trip_search({})
    fare_type = random.choice(FARE_TYPES)
    base["task_type"] = "swa_select_fare_type"
    base["fare_type"] = fare_type
    base["steps"] += [f"Select the '{fare_type}' fare type on the flight results page."]
    return base

def swa_view_flight_status(_: dict) -> dict:
    flight_number = random.randint(1000, 9999)
    status = random.choice(STATUS_CODES)
    steps = [
        "Go to url 'https://www.southwest.com/air/flight-status/?clk=HP-FLTSTATUS'.",
        *_ui_hygiene(),
        f"Search flight number '{flight_number}'.",
        f"Verify the flight status is '{status}'.",
    ]
    return {"task_type": "swa_view_flight_status", "flight_number": flight_number, "status": status, "steps": steps}

def swa_checkin_flow(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.southwest.com/air/check-in/?clk=HP-CHKIN'.",
        *_ui_hygiene(),
        "Enter a valid reservation number to proceed with check-in.",
        "Verify check-in options are displayed (e.g., seat selection).",
    ]
    return {"task_type": "swa_checkin_flow", "steps": steps}

def swa_manage_booking(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.southwest.com/air/manage-reservation/?clk=HP-MANAGE-FLT'.",
        *_ui_hygiene(),
        "Enter reservation details (without valid reservation number use a mock).",
        "Verify that manage booking options like change flight or cancel appear.",
    ]
    return {"task_type": "swa_manage_booking", "steps": steps}

_TASK_GENERATORS: Dict[SWA_TASK_TYPES, Callable[[dict], dict]] = {
    "swa_one_way_search": swa_one_way_search,
    "swa_round_trip_search": swa_round_trip_search,
    "swa_filter_nonstop": swa_filter_nonstop,
    "swa_select_fare_type": swa_select_fare_type,
    "swa_view_flight_status": swa_view_flight_status,
    "swa_checkin_flow": swa_checkin_flow,
    "swa_manage_booking": swa_manage_booking,
}

def generate_swa_task(task_type: SWA_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = get_instruction("Southwest", task["steps"]).model_dump()
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
    items = list(SWA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_swa_task, ttype, p))
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