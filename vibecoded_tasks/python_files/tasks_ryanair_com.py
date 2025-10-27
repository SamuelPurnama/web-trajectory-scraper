import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

RYANAIR_TASK_TYPES = Literal[
    "ryanair_one_way_search",
    "ryanair_round_trip_search",
    "ryanair_view_flight_deals",
    "ryanair_check_baggage_policy",
    "ryanair_explore_destinations",
    "ryanair_view_fare_finder",
    "ryanair_help_center_topic",
    "ryanair_budget_flight_search"
]

RYANAIR_SAMPLING_CONFIG: Dict[RYANAIR_TASK_TYPES, int] = {
    "ryanair_one_way_search": 10,
    "ryanair_round_trip_search": 10,
    "ryanair_view_flight_deals": 10,
    "ryanair_check_baggage_policy": 10,
    "ryanair_explore_destinations": 10,
    "ryanair_view_fare_finder": 10,
    "ryanair_help_center_topic": 10,
    "ryanair_budget_flight_search": 10,
}

DESTINATIONS = [
    "Dublin","London","Barcelona","Madrid","Rome","Milan","Paris","Berlin",
    "Lisbon","Warsaw","Krakow","Vienna","Prague","Brussels","Budapest",
    "Amsterdam","Frankfurt","Munich","Zurich","Geneva","Stockholm","Copenhagen",
    "Oslo","Helsinki","Athens","Istanbul","Tel Aviv","Dubai","Doha","Cairo",
    "Casablanca","Tunis","Algiers","Lagos","Nairobi","Johannesburg","Cape Town",
    "New York","Boston","Chicago","Los Angeles","Miami","Toronto","Vancouver",
    "Mexico City","Buenos Aires","São Paulo","Rio de Janeiro","Lima","Bogotá",
    "Sydney","Melbourne","Perth","Auckland","Wellington","Bangkok","Singapore",
    "Hong Kong","Tokyo","Seoul","Beijing","Shanghai","Mumbai","Delhi","Bangalore", "Moscow"
]
RETURNABLE_DESTINATIONS = [
    ("Dublin","London"),("London","Dublin"),("Barcelona","Paris"),("Rome","Berlin"),
    ("Madrid","Lisbon"),("Vienna","Prague"),("Warsaw","Krakow"),("Amsterdam","Frankfurt"),
    ("Munich","Zurich"),("Stockholm","Copenhagen"),("Athens","Istanbul"),("New York","Boston"),
    ("Los Angeles","Miami"),("Toronto","Vancouver"),("Sydney","Melbourne"),("Tokyo","Seoul")
]
BAGS = ["cabin bag allowance", "priority & 2 cabin bags", "checked bag options", "oversize/overweight fees"]
HELP_TOPICS = [
    ("Baggage Information","https://www.ryanair.com/ie/en/plan-trip/flying-with-us/bags"),
    ("Check-in","https://help.ryanair.com/hc/en-gb/articles/360017824698-Check-in"),
    ("Name change","https://help.ryanair.com/hc/en-gb/articles/360017828258-Name-change")
]

# Time options for budget search
TIME_OPTIONS = [
    "tomorrow",
    "next week", 
    "this weekend",
    "next month",
    "in 2 weeks",
    "next Friday",
    "next Monday"
]

# Price ranges for budget search
PRICE_RANGES = [
    ("under $50", 50),
    ("under $75", 75), 
    ("under $100", 100),
    ("under $150", 150),
    ("under $200", 200),
    ("under $300", 300)
]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    if oneway:
        origin, destination = random.sample(DESTINATIONS, 2)
    else:
        origin, destination = random.choice(RETURNABLE_DESTINATIONS)
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": origin, "to": destination, "depart": dep, "return": ret, "adults": 1}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (cookies, promos).",
        "Only navigate; do not enter personal data or purchase."
    ]

def _search_home() -> list[str]:
    return [
        "Go to 'https://www.ryanair.com' and locate the flight search widget.",
        *_ui_hygiene(),
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Ryanair", steps).model_dump()

def ryanair_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _search_home() + [
        "Select 'One way'.",
        f"Enter departure '{t['from']}' and arrival '{t['to']}'.",
        f"Set departure date to '{t['depart']}'.",
        "Set adults to 1.",
        "Click 'Search' to show flight options."
    ]
    return {"task_type": "ryanair_one_way_search", **t, "steps": steps}

def ryanair_round_trip_search(_: dict) -> dict:
    t = _trip_base(oneway=False)
    steps = _search_home() + [
        "Select 'Return'.",
        f"Enter departure '{t['from']}' and arrival '{t['to']}'.",
        f"Set dates: depart '{t['depart']}', return '{t['return']}'.",
        "Set adults to 1.",
        "Click 'Search' to show flight options."
    ]
    return {"task_type": "ryanair_round_trip_search", **t, "steps": steps}

def ryanair_view_flight_deals(_: dict) -> dict:
    steps = [
        "Navigate to 'https://www.ryanair.com/gb/en/cheap-flights'.",
        *_ui_hygiene(),
        "Browse deals and note one destination with its lowest shown price."
    ]
    return {"task_type": "ryanair_view_flight_deals", "focus": "flight deals", "steps": steps}

def ryanair_check_baggage_policy(_: dict) -> dict:
    focus = random.choice(BAGS)
    steps = [
        "Go to 'https://www.ryanair.com/ie/en/plan-trip/flying-with-us/bags'.",
        *_ui_hygiene(),
        f"Find and summarize: {focus}."
    ]
    return {"task_type": "ryanair_check_baggage_policy", "focus": focus, "steps": steps}

def ryanair_explore_destinations(_: dict) -> dict:
    destination = random.choice(DESTINATIONS)
    steps = [
        "Go to 'https://www.ryanair.com/gb/en/plan-trip/explore'.",
        *_ui_hygiene(),
        f"Use Explore to find info or routes to {destination}. Summarize key highlights."
    ]
    return {"task_type": "ryanair_explore_destinations", "destination": destination, "steps": steps}

def ryanair_view_fare_finder(_: dict) -> dict:
    steps = [
        "Visit 'https://www.ryanair.com/gb/en/cheap-flights/fare-finder'.",
        *_ui_hygiene(),
        "Search any route/month and report an example low fare shown (route + price)."
    ]
    return {"task_type": "ryanair_view_fare_finder", "focus": "fare finder", "steps": steps}

def ryanair_help_center_topic(_: dict) -> dict:
    topic, url = random.choice(HELP_TOPICS)
    steps = [
        f"Navigate to '{url}'.",
        *_ui_hygiene(),
        f"Read about '{topic}' and list the main points."
    ]
    return {"task_type": "ryanair_help_center_topic", "topic": topic, "url": url, "steps": steps}

def ryanair_budget_flight_search(_: dict) -> dict:
    origin = random.choice(DESTINATIONS)
    destination = random.choice([d for d in DESTINATIONS if d != origin])
    time_option = random.choice(TIME_OPTIONS)
    price_text, price_value = random.choice(PRICE_RANGES)
    
    # Simple date calculation based on time option
    time_to_days = {
        "tomorrow": 1,
        "next week": 7,
        "this weekend": 3,  # Approximate weekend
        "next month": 30,
        "in 2 weeks": 14,
        "next Friday": 5,   # Approximate
        "next Monday": 2,   # Approximate
    }
    days_ahead = time_to_days.get(time_option, 10)  # Default to 10 days
    dep_date = (dt.date.today() + dt.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    steps = _search_home() + [
        "Select 'One way'.",
        f"Enter departure '{origin}' and arrival '{destination}'.",
        f"Set departure date to '{dep_date}'.",
        "Set adults to 1.",
        "Click 'Search' to show flight options.",
        f"Look for flights {price_text} and report any found with their prices."
    ]
    
    return {
        "task_type": "ryanair_budget_flight_search", 
        "from": origin, 
        "to": destination, 
        "depart": dep_date,
        "time_option": time_option,
        "price_limit": price_text,
        "max_price": price_value,
        "steps": steps
    }

_TASK_GENERATORS: Dict[RYANAIR_TASK_TYPES, Callable[[dict], dict]] = {
    "ryanair_one_way_search": ryanair_one_way_search,
    "ryanair_round_trip_search": ryanair_round_trip_search,
    "ryanair_view_flight_deals": ryanair_view_flight_deals,
    "ryanair_check_baggage_policy": ryanair_check_baggage_policy,
    "ryanair_explore_destinations": ryanair_explore_destinations,
    "ryanair_view_fare_finder": ryanair_view_fare_finder,
    "ryanair_help_center_topic": ryanair_help_center_topic,
    "ryanair_budget_flight_search": ryanair_budget_flight_search,
}

def generate_ryanair_task(task_type: RYANAIR_TASK_TYPES, payload: dict) -> dict:
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
    items = list(RYANAIR_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_ryanair_task, ttype, p))
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
