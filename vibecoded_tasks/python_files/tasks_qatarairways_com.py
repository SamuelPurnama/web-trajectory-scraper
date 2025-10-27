import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

QATAR_TASK_TYPES = Literal[
    "qatar_one_way_search",
    "qatar_round_trip_search",
    "qatar_view_flight_deals",
    "qatar_check_baggage_policy",
    "qatar_explore_destinations",
    "qatar_view_reward_seats",
    "qatar_help_center_topic"
]

QATAR_SAMPLING_CONFIG: Dict[QATAR_TASK_TYPES, int] = {
    "qatar_one_way_search": 10,
    "qatar_round_trip_search": 10,
    "qatar_view_flight_deals": 10,
    "qatar_check_baggage_policy": 10,
    "qatar_explore_destinations": 10,
    "qatar_view_reward_seats": 10,
    "qatar_help_center_topic": 10,
}

DESTINATIONS = ["Doha", "London", "New York", "Tokyo", "Delhi", "Lagos", "Dubai", "Miami", "Los Angeles"]
RETURNABLE_DESTINATIONS = [("Doha", "London"), ("Doha", "New York"), ("Tokyo", "Doha"), ("Delhi", "Doha")]
BAGS = ["carry-on allowance", "checked baggage allowance", "excess/overweight fees"]
HELP_TOPICS = [("Baggage Information", "https://www.qatarairways.com/en/baggage.html")]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    if oneway:
        origin, destination = random.sample(DESTINATIONS, 2)
    else:
        origin, destination = random.choice(RETURNABLE_DESTINATIONS)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": origin, "to": destination, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners that may obscure navigation.",
        "Only navigate; do not make any purchases or enter personal information."
    ]

def _search_home() -> list[str]:
    return [
        "Go to 'https://www.qatarairways.com' and locate the flight search widget.",
        *_ui_hygiene(),
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Qatar Airways", steps).model_dump()

def qatar_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _search_home() + [
        "Select 'One-way' trip type.",
        f"Enter departure city '{t['from']}' and arrival city '{t['to']}'.",
        f"Set departure date to '{t['depart']}'.",
        "Set number of adults to 1.",
        "Click 'Search' to display flight options.",
    ]
    return {"task_type": "qatar_one_way_search", **t, "steps": steps}

def qatar_round_trip_search(_: dict) -> dict:
    t = _trip_base(oneway=False)
    steps = _search_home() + [
        "Select 'Return' (round trip) trip type.",
        f"Enter departure city '{t['from']}' and arrival city '{t['to']}'.",
        f"Set travel dates to: departure '{t['depart']}', return '{t['return']}'.",
        "Set number of adults to 1.",
        "Click 'Search' to display flight options.",
    ]
    return {"task_type": "qatar_round_trip_search", **t, "steps": steps}

def qatar_view_flight_deals(_: dict) -> dict:
    steps = [
        "Navigate to 'https://www.qatarairways.com/en/offers.html'.",
        *_ui_hygiene(),
        "Browse available flight deals.",
        "Note the destination and the lowest price available for at least one deal."
    ]
    return {"task_type": "qatar_view_flight_deals", "focus": "flight deals", "steps": steps}

def qatar_check_baggage_policy(_: dict) -> dict:
    focus = random.choice(BAGS)
    steps = [
        "Go to 'https://www.qatarairways.com/en/baggage.html'.",
        *_ui_hygiene(),
        f"Locate and summarize information about: {focus}.",
    ]
    return {"task_type": "qatar_check_baggage_policy", "focus": focus, "steps": steps}

def qatar_explore_destinations(_: dict) -> dict:
    destination = random.choice(DESTINATIONS)
    steps = [
        "Go to 'https://www.qatarairways.com/en/destinations.html'.",
        *_ui_hygiene(),
        f"Find information about flights to {destination} and summarize key highlights.",
    ]
    return {"task_type": "qatar_explore_destinations", "destination": destination, "steps": steps}

def qatar_view_reward_seats(_: dict) -> dict:
    steps = [
        "Visit 'https://www.qatarairways.com/en/Privilege-Club/spend-avios.html'.",
        *_ui_hygiene(),
        "If available, use 'Book with Avios' in the booking widget to check reward seat availability for a chosen route and month.",
        "List any example dates/routes showing reward seats, or summarize how to check availability.",
    ]
    return {"task_type": "qatar_view_reward_seats", "focus": "reward seats", "steps": steps}

def qatar_help_center_topic(_: dict) -> dict:
    """Help center topic search task."""
    steps = [
        "Visit 'https://www.qatarairways.com/en/help.html'.",
        *_ui_hygiene(),
        "Browse the help center topics and find information about a specific topic (e.g., baggage, check-in, booking).",
        "Summarize the key information found about the topic.",
    ]
    return {"task_type": "qatar_help_center_topic", "focus": "help center", "steps": steps}

def _instr(steps: list[str]) -> dict:
    return get_instruction("Qatar Airways", steps).model_dump()

def generate_task(task_type: QATAR_TASK_TYPES, payload: dict) -> dict:
    """Generate a task based on the task type."""
    task_functions = {
        "qatar_one_way_search": qatar_one_way_search,
        "qatar_round_trip_search": qatar_round_trip_search,
        "qatar_view_flight_deals": qatar_view_flight_deals,
        "qatar_check_baggage_policy": qatar_check_baggage_policy,
        "qatar_explore_destinations": qatar_explore_destinations,
        "qatar_view_reward_seats": qatar_view_reward_seats,
        "qatar_help_center_topic": qatar_help_center_topic,
    }
    
    if task_type not in task_functions:
        raise ValueError(f"Unknown task type: {task_type}")
    
    task = task_functions[task_type](payload)
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
    items = list(QATAR_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for task_type, count in items:
            for _ in range(count):
                if i < len(payloads):
                    payload = payloads[i]
                else:
                    payload = {}
                fut = ex.submit(generate_task, task_type, payload)
                futures.append(fut)
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
