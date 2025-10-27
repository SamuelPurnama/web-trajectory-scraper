import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

RYANAIR_TASK_TYPES = Literal[
    "ryanair_one_way_search",
    "ryanair_round_trip_search",
    "ryanair_filter_nonstop",
    "ryanair_explore_destinations",
    "ryanair_flight_deals",
    "ryanair_baggage_info",
    "ryanair_contact_support",
    "ryanair_special_assistance_info",
    "ryanair_car_hire_info",
]

RYANAIR_SAMPLING_CONFIG: Dict[RYANAIR_TASK_TYPES, int] = {
    "ryanair_one_way_search": 10,
    "ryanair_round_trip_search": 10,
    "ryanair_filter_nonstop": 10,
    "ryanair_explore_destinations": 10,
    "ryanair_flight_deals": 10,
    "ryanair_baggage_info": 10,
    "ryanair_contact_support": 10,
    "ryanair_special_assistance_info": 10,
    "ryanair_car_hire_info": 10,
}

DESTINATIONS = ["DUB","STN","MAD","BCN","CDG","AMS","FRA","VIE","VLC","MXP"]
EASY_PAIRS = [("DUB","STN"),("MAD","BCN"),("CDG","AMS"),("FRA","MXP"),("VIE","VLC")]
WINDOWS = ["Morning (5–11am)","Afternoon (12–5pm)"]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    if random.random() < 0.8 and EASY_PAIRS:
        o, d = random.choice(EASY_PAIRS)
    else:
        o, d = random.sample(DESTINATIONS, 2)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss pop-ups/banners.",
        "Do not book or purchase anything; only search and view results.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.ryanair.com/'.",
        "Ensure the booking widget is visible.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, click 'Done' on the calendar/date picker."

def _instr(steps: list[str]) -> dict:
    return get_instruction("Ryanair", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus the 'Departure airport' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{origin}'.",
        f"{p}Select the autocomplete option for '{origin}' (airport).",
        f"{p}Confirm origin shows '{origin}' correctly.",
        f"{p}Close the dropdown before proceeding.",
        f"{p}Focus the 'Destination airport' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{dest}'.",
        f"{p}Select the autocomplete option for '{dest}' (airport).",
        f"{p}Confirm destination shows '{dest}' correctly.",
        f"{p}Ensure the dropdown is closed before proceeding.",
    ]

def ryanair_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _book_home() + [
        "Select 'One Way' option.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date to '{t['depart']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search' to get results.",
    ]
    return {"task_type":"ryanair_one_way_search",**t,"steps":steps}

def ryanair_round_trip_search(_: dict) -> dict:
    t = _trip_base()
    steps = _book_home() + [
        "Select 'Return' option.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set dates: departure '{t['depart']}', return '{t['return']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Search' to get results.",
    ]
    return {"task_type":"ryanair_round_trip_search",**t,"steps":steps}

def ryanair_filter_nonstop(_: dict) -> dict:
    base = ryanair_round_trip_search({})
    base["task_type"] = "ryanair_filter_nonstop"
    base["steps"] += ["Enable the 'Nonstop' filter.","Ensure dropdowns are closed before proceeding."]
    return base

def ryanair_explore_destinations(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.ryanair.com/us/en/cheap-flight-destinations'.",
        *_ui_hygiene(),
        "Select a recommended destination and report on its cheapest flight.",
    ]
    return {"task_type":"ryanair_explore_destinations","steps":steps}

def ryanair_flight_deals(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.ryanair.com/us/en/lp/promotion/flash-sale'.",
        *_ui_hygiene(),
        "Note one highlighted deal: destination and price.",
    ]
    return {"task_type":"ryanair_flight_deals","steps":steps}

def ryanair_baggage_info(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.ryanair.com/us/en/lp/travel-extras/bag-sizers-and-gate-bag-fees-explained'.",
        *_ui_hygiene(),
        "Summarize the key points about baggage policies.",
    ]
    return {"task_type":"ryanair_baggage_info","steps":steps}

def ryanair_contact_support(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.ryanair.com/us/en/r/help/contact-us'.",
        *_ui_hygiene(),
        "Identify all available contact methods and operation hours.",
    ]
    return {"task_type":"ryanair_contact_support","steps":steps}

def ryanair_special_assistance_info(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.ryanair.com/us/en/r/help/special-assistance'.",
        *_ui_hygiene(),
        "Find and summarize the steps required to request special assistance.",
    ]
    return {"task_type":"ryanair_special_assistance_info","steps":steps}

def ryanair_car_hire_info(_: dict) -> dict:
    steps = [
        "Go to url 'https://carhire.ryanair.com/' and set language to English if not already.",
        "View available car hire deals and summarize the first visible offer.",
        *_ui_hygiene(),
    ]
    return {"task_type":"ryanair_car_hire_info","steps":steps}

_TASK_GENERATORS: Dict[RYANAIR_TASK_TYPES, Callable[[dict], dict]] = {
    "ryanair_one_way_search": ryanair_one_way_search,
    "ryanair_round_trip_search": ryanair_round_trip_search,
    "ryanair_filter_nonstop": ryanair_filter_nonstop,
    "ryanair_explore_destinations": ryanair_explore_destinations,
    "ryanair_flight_deals": ryanair_flight_deals,
    "ryanair_baggage_info": ryanair_baggage_info,
    "ryanair_contact_support": ryanair_contact_support,
    "ryanair_special_assistance_info": ryanair_special_assistance_info,
    "ryanair_car_hire_info": ryanair_car_hire_info,
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
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)