import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

HA_TASK_TYPES = Literal[
    "ha_one_way_search",
    "ha_round_trip_search",
    "ha_check_in",
    "ha_baggage_info",
    "ha_flight_info",
    "ha_hawaiianmiles_signup",
    "ha_online_checkin_info",
    "ha_fare_deals",
    "ha_help_contact_info",
]

HA_SAMPLING_CONFIG: Dict[HA_TASK_TYPES, int] = {
    "ha_one_way_search": 10,
    "ha_round_trip_search": 10,
    "ha_check_in": 10,
    "ha_baggage_info": 10,
    "ha_flight_info": 10,
    "ha_hawaiianmiles_signup": 10,
    "ha_online_checkin_info": 10,
    "ha_fare_deals": 10,
    "ha_help_contact_info": 10,
}

AIRPORTS = ["HNL", "OGG", "KOA", "LIH", "ITO", "JFK", "LAX", "SEA", "SFO", "LAS"]
EASY_PAIRS = [("HNL", "OGG"), ("HNL", "KOA"), ("HNL", "LIH"), ("JFK", "HNL"), ("LAX", "OGG")]
WINDOWS = ["Morning (5–11am)", "Afternoon (12–5pm)"]

def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _trip_base(oneway=False):
    if random.random() < 0.8 and EASY_PAIRS:
        o, d = random.choice(EASY_PAIRS)
    else:
        o, d = random.sample(AIRPORTS, 2)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss popups/banners if any (e.g., 'I understand', 'Sign up for HawaiianMiles').",
        "Do not book or purchase anything; only search and view results.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.hawaiianairlines.com' and ensure the booking widget is visible.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, confirm by clicking 'Done' or similar."

def _instr(steps: list[str]) -> dict:
    return get_instruction("Hawaiian Airlines", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus on 'From' field, clear it, and type '{origin}'.",
        f"Confirm selection for '{origin}' from autocomplete.",
        f"Focus on 'To' field, clear it, and type '{dest}'.",
        f"Confirm selection for '{dest}' from autocomplete.",
    ]

def ha_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True)
    steps = _book_home() + [
        "Select 'One Way' trip option.",
        *_from_to_steps(t["from"], t["to"]),
        f"Select depart date as '{t['depart']}'.",
        _calendar_done_step(),
        "Set passengers to 1 adult.",
        "Click 'Search Flights' to view options.",
    ]
    return {"task_type": "ha_one_way_search", **t, "steps": steps}

def ha_round_trip_search(_: dict) -> dict:
    t = _trip_base()
    steps = _book_home() + [
        "Select 'Round Trip' trip option.",
        *_from_to_steps(t["from"], t["to"]),
        f"Select depart date as '{t['depart']}' and return date as '{t['return']}'.",
        _calendar_done_step(),
        "Set passengers to 1 adult.",
        "Click 'Search Flights' to view options.",
    ]
    return {"task_type": "ha_round_trip_search", **t, "steps": steps}

def ha_check_in(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.hawaiianairlines.com/manage/check-in'.",
        *_ui_hygiene(),
        "Input a sample reservation code and last name (do not proceed further).",
        "Click 'Check-In' and verify error message handling.",
    ]
    return {"task_type": "ha_check_in", "steps": steps}

def ha_baggage_info(_: dict) -> dict:
    sections = ["Carry-on Baggage", "Checked Baggage Fees", "Excess Baggage", "Sporting Equipment"]
    focus = random.choice(sections)
    steps = [
        "Go to url 'https://www.hawaiianairlines.com/legal/list-of-all-fees'.",
        *_ui_hygiene(),
        f"Locate and summarize the section for: {focus}.",
    ]
    return {"task_type": "ha_baggage_info", "focus": focus, "steps": steps}

def ha_flight_info(_: dict) -> dict:
    routes = ["Hawaii to Mainland", "Hawaii Interisland", "International"]
    focus = random.choice(routes)
    steps = [
        "Go to url 'https://www.hawaiianairlines.com/our-services/special-assistance'.",
        *_ui_hygiene(),
        f"Summarize key points for: {focus} routes.",
    ]
    return {"task_type": "ha_flight_info", "focus": focus, "steps": steps}

def ha_hawaiianmiles_signup(_: dict) -> dict:
    verify = random.choice(["name and email fields", "password requirements", "marketing opt-in checkbox"])
    steps = [
        "Go to url 'https://www.hawaiianairlines.com/my-account/join-hawaiianmiles'.",
        *_ui_hygiene(),
        f"Verify the presence of {verify}.",
    ]
    return {"task_type": "ha_hawaiianmiles_signup", "verify": verify, "steps": steps}

def ha_online_checkin_info(_: dict) -> dict:
    steps = [
        "Go to url 'https://hawaiianair.custhelp.com/app/answers/detail/a_id/957'.",
        *_ui_hygiene(),
        "Summarize steps and information required for online check-in.",
    ]
    return {"task_type": "ha_online_checkin_info", "steps": steps}

def ha_fare_deals(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.hawaiianairlines.com/deals-and-offers/flights/hawaii'.",
        *_ui_hygiene(),
        "Report one popular fare deal, including destination and price.",
    ]
    return {"task_type": "ha_fare_deals", "focus": "single popular fare deal", "steps": steps}

def ha_help_contact_info(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.hawaiianairlines.com/contact-us'.",
        *_ui_hygiene(),
        "Identify the contact methods available for customer service assistance.",
    ]
    return {"task_type": "ha_help_contact_info", "steps": steps}

_TASK_GENERATORS: Dict[HA_TASK_TYPES, Callable[[dict], dict]] = {
    "ha_one_way_search": ha_one_way_search,
    "ha_round_trip_search": ha_round_trip_search,
    "ha_check_in": ha_check_in,
    "ha_baggage_info": ha_baggage_info,
    "ha_flight_info": ha_flight_info,
    "ha_hawaiianmiles_signup": ha_hawaiianmiles_signup,
    "ha_online_checkin_info": ha_online_checkin_info,
    "ha_fare_deals": ha_fare_deals,
    "ha_help_contact_info": ha_help_contact_info,
}

def generate_ha_task(task_type: HA_TASK_TYPES, payload: dict) -> dict:
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
    items = list(HA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_ha_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)