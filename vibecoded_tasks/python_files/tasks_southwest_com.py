import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

SOUTHWEST_TASK_TYPES = Literal[
    "southwest_one_way_search",
    "southwest_round_trip_search",
    "southwest_check_in",
    "southwest_flight_status",
    "southwest_sign_up",
    "southwest_search_hotel",
    "southwest_view_baggage_policy"
]

SOUTHWEST_SAMPLING_CONFIG: Dict[SOUTHWEST_TASK_TYPES, int] = {
    "southwest_one_way_search": 10,
    "southwest_round_trip_search": 10,
    "southwest_check_in": 10,
    "southwest_flight_status": 10,
    "southwest_sign_up": 10,
    "southwest_search_hotel": 10,
    "southwest_view_baggage_policy": 10,
}

AIRPORTS = ["SEA", "SFO", "LAX", "SAN", "PHX", "DEN", "SLC", "PDX", "LAS", "AUS", "DFW", "IAH", "ORD", "MSP", "ATL", "MCO", "JFK", "EWR", "BOS", "BWI", "IAD", "CLT", "RDU"]
DEPARTURE_DATES = [(dt.date.today() + dt.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10, 41)]

def _rand_date() -> str:
    return random.choice(DEPARTURE_DATES)

def _trip_base(oneway=False) -> dict:
    origin, destination = random.sample(AIRPORTS, 2)
    departure = _rand_date()
    return {
        "from": origin,
        "to": destination,
        "depart": departure,
        "return": None if oneway else (dt.datetime.strptime(departure, "%Y-%m-%d") + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d"),
        "adults": 1
    }

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss popups or banners if any appear.",
        "Do not book or purchase anything; only search and view results.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Southwest", steps).model_dump()

def _from_to_steps(origin: str, dest: str) -> list[str]:
    return [
        f"Focus on the 'Departure City' field and type '{origin}'.",
        f"Select the option for '{origin}' in the autocomplete.",
        f"Focus on the 'Destination City' field and type '{dest}'.",
        f"Select the option for '{dest}' in the autocomplete.",
    ]

def southwest_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = [
        "Open 'https://www.southwest.com' and ensure the booking widget is visible.",
        *_ui_hygiene(),
        "Select 'One Way' under trip type.",
        *_from_to_steps(t["from"], t["to"]),
        f"Select a departure date: '{t['depart']}'.",
        "Click 'Search' to view flight options.",
    ]
    return {"task_type": "southwest_one_way_search", **t, "steps": steps}

def southwest_round_trip_search(_: dict) -> dict:
    t = _trip_base(oneway=False)
    steps = [
        "Open 'https://www.southwest.com' and ensure the booking widget is visible.",
        *_ui_hygiene(),
        "Select 'Round Trip' under trip type.",
        *_from_to_steps(t["from"], t["to"]),
        f"Select departure date as '{t['depart']}' and return date as '{t['return']}'.",
        "Click 'Search' to view round trip flight options.",
    ]
    return {"task_type": "southwest_round_trip_search", **t, "steps": steps}

def southwest_check_in(_: dict) -> dict:
    confirmation_number = "ABC123"  # Example fixed confirmation number
    steps = [
        "Open 'https://www.southwest.com/air/check-in'.",
        *_ui_hygiene(),
        f"Enter the confirmation number '{confirmation_number}'.",
        "Proceed to check-in using the button provided.",
        "Verify that the check-in is successful or identify any issues present.",
    ]
    return {"task_type": "southwest_check_in", "steps": steps}

def southwest_flight_status(_: dict) -> dict:
    flight_number = "WN123"  # Example fixed flight number
    steps = [
        "Open 'https://www.southwest.com/air/flight-status'.",
        *_ui_hygiene(),
        "Enter a sample flight number 'WN123'.",
        "Press the 'Check Status' button.",
        "Observe the current status and ensure it's displayed correctly.",
    ]
    return {"task_type": "southwest_flight_status", "steps": steps}

def southwest_sign_up(_: dict) -> dict:
    email = f"user{random.randint(1000, 9999)}@example.com"  # Generate a random email
    steps = [
        "Navigate to 'https://www.southwest.com/loyalty/enroll/?clk=HP-RR-ENROLL&f=z4297032zz'.",
        *_ui_hygiene(),
        f"Fill in the required fields using email '{email}' and other sample data.",
        "Agree to terms and conditions.",
        "Attempt to submit the sign-up form and confirm any resulting output or errors.",
    ]
    return {"task_type": "southwest_sign_up", "email": email, "steps": steps}

def southwest_search_hotel(_: dict) -> dict:
    city = random.choice(["Las Vegas", "San Francisco", "Chicago"])
    steps = [
        "Open 'https://www.southwesthotels.com'.",
        *_ui_hygiene(),
        f"Enter '{city}' in the hotel search bar.",
        "Select check-in and check-out dates.",
        "Press the 'Search' button.",
        "Verify that hotel results for '{city}' are shown.",
    ]
    return {"task_type": "southwest_search_hotel", "city": city, "steps": steps}

def southwest_view_baggage_policy(_: dict) -> dict:
    steps = [
        "Navigate to 'https://www.southwest.com/html/customer-service/travel-fees.html?clk=HOME-BOOKING-WIDGET-BAGGAGE-FEES'.",
        *_ui_hygiene(),
        "Scroll to view the baggage policies.",
        "Summarize key points about checked baggage fees and policies.",
    ]
    return {"task_type": "southwest_view_baggage_policy", "steps": steps}

_TASK_GENERATORS: Dict[SOUTHWEST_TASK_TYPES, Callable[[dict], dict]] = {
    "southwest_one_way_search": southwest_one_way_search,
    "southwest_round_trip_search": southwest_round_trip_search,
    "southwest_check_in": southwest_check_in,
    "southwest_flight_status": southwest_flight_status,
    "southwest_sign_up": southwest_sign_up,
    "southwest_search_hotel": southwest_search_hotel,
    "southwest_view_baggage_policy": southwest_view_baggage_policy,
}

def generate_southwest_task(task_type: SOUTHWEST_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = _instr(task["steps"])
    return task

def main(filepath: str, num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    random.seed(seed)
    futures, out = [], []
    items = list(SOUTHWEST_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        for ttype, cnt in items:
            for _ in range(cnt):
                futures.append(ex.submit(generate_southwest_task, ttype, {}))
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try:
                out.append(fut.result(timeout=timeout))
            except Exception:
                pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)