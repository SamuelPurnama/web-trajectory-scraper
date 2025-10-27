import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

FLYBREEZE_TASK_TYPES = Literal[
    "flybreeze_one_way_search",
    "flybreeze_round_trip_search",
    "flybreeze_check_in",
    "flybreeze_flight_status",
    "flybreeze_info_faqs",
    "flybreeze_careers",
    "flybreeze_contact_support",
]

FLYBREEZE_SAMPLING_CONFIG: Dict[FLYBREEZE_TASK_TYPES, int] = {
    "flybreeze_one_way_search": 10,
    "flybreeze_round_trip_search": 10,
    "flybreeze_check_in": 10,
    "flybreeze_flight_status": 10,
    "flybreeze_info_faqs": 10,
    "flybreeze_careers": 10,
    "flybreeze_contact_support": 10,
}

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    origin = "SFO"
    destination = "LAX"
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=3)).strftime("%Y-%m-%d")
    return {"from": origin, "to": destination, "depart": dep, "return": ret, "adults": pax}

def _instr(steps: list[str]) -> dict:
    return get_instruction("FlyBreeze", steps).model_dump()

def flybreeze_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = [
        "Go to url 'https://www.flybreeze.com'.",
        "Select the 'Flights' tab.",
        "Choose 'One Way'.",
        f"Enter origin as '{t['from']}'.",
        f"Enter destination as '{t['to']}'.",
        f"Set departure date to '{t['depart']}'.",
        "Set travelers to 1 adult.",
        "Click 'Search' to view results.",
    ]
    return {"task_type": "flybreeze_one_way_search", **t, "steps": steps}

def flybreeze_round_trip_search(_: dict) -> dict:
    t = _trip_base(oneway=False)
    steps = [
        "Go to url 'https://www.flybreeze.com'.",
        "Select the 'Flights' tab.",
        "Choose 'Round Trip'.",
        f"Enter origin as '{t['from']}'.",
        f"Enter destination as '{t['to']}'.",
        f"Set departure date to '{t['depart']}'.",
        f"Set return date to '{t['return']}'.",
        "Set travelers to 1 adult.",
        "Click 'Search' to view results.",
    ]
    return {"task_type": "flybreeze_round_trip_search", **t, "steps": steps}

def flybreeze_check_in(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flybreeze.com/check-in/search'.",
        "Enter the required details for check-in.",
        "Click 'Check In'.",
        "Verify check-in confirmation message is displayed.",
    ]
    return {"task_type": "flybreeze_check_in", "steps": steps}

def flybreeze_flight_status(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flybreeze.com/flight-status'.",
        "Enter flight details or select from options.",
        "Click 'Check Status'.",
        "Verify flight status information is displayed.",
    ]
    return {"task_type": "flybreeze_flight_status", "steps": steps}

def flybreeze_info_faqs(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flybreeze.com/support'.",
        "Browse the FAQ sections.",
        "Verify FAQs are accessible and sections are expandable.",
    ]
    return {"task_type": "flybreeze_info_faqs", "steps": steps}

def flybreeze_careers(_: dict) -> dict:
    steps = [
        "Go to url 'https://jobs.flybreeze.com'.",
        "Browse available job listings.",
        "Select and view details for one job listing.",
        "Verify job description and application process is clear.",
    ]
    return {"task_type": "flybreeze_careers", "steps": steps}

def flybreeze_contact_support(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flybreeze.com/support?a=Contact-Support---id--8PUFhDWYSySIZDc9nJq_ng'.",
        "Locate and verify the support contact methods listed.",
        "Ensure methods like phone and email are accessible.",
    ]
    return {"task_type": "flybreeze_contact_support", "steps": steps}

_TASK_GENERATORS: Dict[FLYBREEZE_TASK_TYPES, Callable[[dict], dict]] = {
    "flybreeze_one_way_search": flybreeze_one_way_search,
    "flybreeze_round_trip_search": flybreeze_round_trip_search,
    "flybreeze_check_in": flybreeze_check_in,
    "flybreeze_flight_status": flybreeze_flight_status,
    "flybreeze_info_faqs": flybreeze_info_faqs,
    "flybreeze_careers": flybreeze_careers,
    "flybreeze_contact_support": flybreeze_contact_support,
}

def generate_flybreeze_task(task_type: FLYBREEZE_TASK_TYPES, payload: dict) -> dict:
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
    items = list(FLYBREEZE_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_flybreeze_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)