import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

VIRGIN_TASK_TYPES = Literal[
    "virgin_one_way_search",
    "virgin_round_trip_search",
    "virgin_view_flight_deals",
    "virgin_check_baggage_policy",
    "virgin_explore_destinations",
    "virgin_view_reward_seats",
    "virgin_help_center_topic"
]

VIRGIN_SAMPLING_CONFIG: Dict[VIRGIN_TASK_TYPES, int] = {
    "virgin_one_way_search": 10,
    "virgin_round_trip_search": 10,
    "virgin_view_flight_deals": 10,
    "virgin_check_baggage_policy": 10,
    "virgin_explore_destinations": 10,
    "virgin_view_reward_seats": 10,
    "virgin_help_center_topic": 10,
}

DESTINATIONS = ["London", "New York", "Tokyo", "Delhi", "Lagos", "Dubai", "Miami", "Los Angeles"]
RETURNABLE_DESTINATIONS = [("London", "New York"), ("Tokyo", "Los Angeles"), ("Delhi", "Dubai")]
BAGS = ["carry-on size/weight", "first checked bag fees", "oversize/overweight fees"]
HELP_TOPICS = [("Baggage Information", "https://www.virginatlantic.com/help/categories/070fb328-0c1c-4a04-a2bf-795834008bf1")]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    if oneway:
        origin, destination = random.choice(list(DESTINATIONS + ["London"]))
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
        "Go to 'https://www.virginatlantic.com' and locate the flight search widget.",
        *_ui_hygiene(),
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Virgin Atlantic", steps).model_dump()

def virgin_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _search_home() + [
        f"Select 'One Way' trip type.",
        f"Enter departure city '{t['from']}' and arrival city '{t['to']}'.",
        f"Set departure date to '{t['depart']}'.",
        "Set number of adults to 1.",
        "Click on 'Search' to display flight options.",
    ]
    return {"task_type": "virgin_one_way_search", **t, "steps": steps}

def virgin_round_trip_search(_: dict) -> dict:
    t = _trip_base(oneway=False)
    steps = _search_home() + [
        f"Select 'Round Trip' trip type.",
        f"Enter departure city '{t['from']}' and arrival city '{t['to']}'.",
        f"Set travel dates to: departure '{t['depart']}', return '{t['return']}'.",
        "Set number of adults to 1.",
        "Click on 'Search' to display flight options.",
    ]
    return {"task_type": "virgin_round_trip_search", **t, "steps": steps}

def virgin_view_flight_deals(_: dict) -> dict:
    steps = [
        "Navigate to 'https://flights.virginatlantic.com/en-gb/'.",
        *_ui_hygiene(),
        "Browse available flight deals.",
        "Note the destination and the lowest price available for at least one deal."
    ]
    return {"task_type": "virgin_view_flight_deals", "focus": "flight deals", "steps": steps}

def virgin_check_baggage_policy(_: dict) -> dict:
    focus = random.choice(BAGS)
    steps = [
        "Go to 'https://flywith.virginatlantic.com/us/en/upgrades-and-extras/optional-service-and-travel-fees.html'.",
        *_ui_hygiene(),
        f"Locate and summarize information about: {focus}.",
    ]
    return {"task_type": "virgin_check_baggage_policy", "focus": focus, "steps": steps}

def virgin_explore_destinations(_: dict) -> dict:
    destination = random.choice(DESTINATIONS)
    steps = [
        f"Go to 'https://www.virginatlantic.com/where-we-fly/{destination.lower()}'.",
        *_ui_hygiene(),
        f"Explore information about flights to {destination} and summarize key highlights."
    ]
    return {"task_type": "virgin_explore_destinations", "destination": destination, "steps": steps}

def virgin_view_reward_seats(_: dict) -> dict:
    steps = [
        "Visit 'https://www.virginatlantic.com/reward-flight-finder'.",
        *_ui_hygiene(),
        "Use the tool to check the availability of reward seats for a selected destination.",
        "Ensure to list the available reward seats for future planning."
    ]
    return {"task_type": "virgin_view_reward_seats", "focus": "reward seats", "steps": steps}

def virgin_help_center_topic(_: dict) -> dict:
    topic, url = random.choice(HELP_TOPICS)
    steps = [
        f"Navigate to '{url}'.",
        *_ui_hygiene(),
        f"Read the information provided about '{topic}' and list the main points.",
    ]
    return {"task_type": "virgin_help_center_topic", "topic": topic, "url": url, "steps": steps}

_TASK_GENERATORS: Dict[VIRGIN_TASK_TYPES, Callable[[dict], dict]] = {
    "virgin_one_way_search": virgin_one_way_search,
    "virgin_round_trip_search": virgin_round_trip_search,
    "virgin_view_flight_deals": virgin_view_flight_deals,
    "virgin_check_baggage_policy": virgin_check_baggage_policy,
    "virgin_explore_destinations": virgin_explore_destinations,
    "virgin_view_reward_seats": virgin_view_reward_seats,
    "virgin_help_center_topic": virgin_help_center_topic,
}

def generate_virgin_task(task_type: VIRGIN_TASK_TYPES, payload: dict) -> dict:
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
    items = list(VIRGIN_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_virgin_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)