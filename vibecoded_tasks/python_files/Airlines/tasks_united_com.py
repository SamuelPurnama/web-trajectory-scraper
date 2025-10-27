import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

UNITED_TASK_TYPES = Literal[
    "united_one_way_search",
    "united_round_trip_search",
    "united_filter_nonstop",
    "united_filter_cabin",
    "united_price_cap",
    "united_baggage_info",
    "united_mileageplus_info",
    "united_flight_status",
    "united_change_cancel_info",
    "united_help_center_topic"
]

UNITED_SAMPLING_CONFIG: Dict[UNITED_TASK_TYPES, int] = {
    "united_one_way_search": 10,
    "united_round_trip_search": 10,
    "united_filter_nonstop": 10,
    "united_filter_cabin": 10,
    "united_price_cap": 10,
    "united_baggage_info": 10,
    "united_mileageplus_info": 10,
    "united_flight_status": 10,
    "united_change_cancel_info": 10,
    "united_help_center_topic": 10,
}

AIRPORTS = ["ORD", "DEN", "SFO", "LAX", "IAH", "EWR", "IAD"]
INTL = ["LHR", "NRT", "FRA", "HND", "YVR", "YYZ"]
EASY_PAIRS = [("ORD", "DEN"), ("LAX", "SFO"), ("EWR", "IAD")]
CABINS_EASY = ["Economy", "Premium Economy", "Business", "First"]
WINDOWS = ["Morning (5–11am)", "Afternoon (12–5pm)"]
BAGS = ["carry-on size/weight", "first checked bag fees", "oversize/overweight fees", "sports equipment"]
HELP_TOPICS = [("Baggage Information", "baggage"), ("MileagePlus Program", "mileageplus"), ("Travelling with Pets", "pets")]


def _rand_date(start_days=10, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")


def _trip_base(oneway=False, domestic=True):
    if domestic and random.random() < 0.8 and EASY_PAIRS:
        o, d = random.choice(EASY_PAIRS)
    else:
        pool = AIRPORTS if domestic else (AIRPORTS + INTL)
        o, d = random.sample(pool, 2)
    pax = 1
    dep = _rand_date()
    ret = None if oneway else (dt.datetime.strptime(dep, "%Y-%m-%d").date() + dt.timedelta(days=random.randint(3, 6))).strftime("%Y-%m-%d")
    return {"from": o, "to": d, "depart": dep, "return": ret, "adults": pax}


def _ui_hygiene() -> list[str]:
    return [
        "Dismiss popups or banners if any appear.",
        "Do not book or purchase anything; only search and view results.",
    ]


def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.united.com' with the booking widget visible.",
        "Ensure you're on the 'BOOK' tab.",
        *_ui_hygiene(),
    ]


def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus on the 'From' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{origin}'.",
        f"{p}Select the autocomplete option for '{origin}' (airport).",
        f"{p}Confirm origin reads '{origin}'; press Enter if necessary.",
        f"{p}Focus on the 'To' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{dest}'.",
        f"{p}Select the autocomplete option for '{dest}' (airport).",
        f"{p}Confirm destination reads '{dest}'; press Enter if needed.",
    ]


def united_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True, domestic=True)
    steps = _book_home() + [
        "Select 'One way' trip type.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set departure date to '{t['depart']}'.",
        "Set travelers to 1 adult.",
        "Click 'Find flights' to view results.",
    ]
    return {"task_type": "united_one_way_search", **t, "steps": steps}


def united_round_trip_search(_: dict) -> dict:
    t = _trip_base()
    steps = _book_home() + [
        "Select 'Round trip' trip type.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set dates: departure '{t['depart']}', return '{t['return']}'.",
        "Set travelers to 1 adult.",
        "Click 'Find flights' to view results.",
    ]
    return {"task_type": "united_round_trip_search", **t, "steps": steps}


def united_filter_nonstop(_: dict) -> dict:
    base = united_round_trip_search({})
    base["task_type"] = "united_filter_nonstop"
    base["steps"].append("Enable the 'Nonstop' filter and observe filtered results.")
    return base


def united_filter_cabin(_: dict) -> dict:
    base = united_round_trip_search({})
    cabin = random.choice(CABINS_EASY)
    base["task_type"] = "united_filter_cabin"
    base["target_cabin"] = cabin
    base["steps"].append(f"Filter results for cabin class: '{cabin}' and observe changes.")
    return base


def united_price_cap(_: dict) -> dict:
    base = united_round_trip_search({})
    cap = random.choice([200, 300, 500, 700, 1000])
    base["task_type"] = "united_price_cap"
    base["max_price"] = cap
    base["steps"].append(f"Apply a price filter with a maximum cap of ${cap} and list the first compatible result.")
    return base


def united_baggage_info(_: dict) -> dict:
    focus = random.choice(BAGS)
    steps = [
        "Go to url 'https://www.united.com/en/us/fly/travel/baggage/baggage-information-and-fees.html'.",
        *_ui_hygiene(),
        f"Find and outline the following information: {focus}.",
    ]
    return {"task_type": "united_baggage_info", "focus": focus, "steps": steps}


def united_mileageplus_info(_: dict) -> dict:
    focus = "MileagePlus membership benefits"
    steps = [
        "Go to url 'https://www.united.com/en/us/fly/mileageplus.html'.",
        *_ui_hygiene(),
        f"List two benefits of the MileagePlus program.",
    ]
    return {"task_type": "united_mileageplus_info", "focus": focus, "steps": steps}


def united_flight_status(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.united.com/en/us/flightstatus'.",
        *_ui_hygiene(),
        "Enter a sample flight number and departure date.",
        "Observe and report the flight status information displayed.",
    ]
    return {"task_type": "united_flight_status", "steps": steps}


def united_change_cancel_info(_: dict) -> dict:
    focus = random.choice(["change a flight", "cancel a booking"])
    steps = [
        "Go to url 'https://www.united.com/ual/en/US/fly/manage-reservations.html'.",
        *_ui_hygiene(),
        f"Summarize information on how to: {focus}.",
    ]
    return {"task_type": "united_change_cancel_info", "focus": focus, "steps": steps}


def united_help_center_topic(_: dict) -> dict:
    topic, slug = random.choice(HELP_TOPICS)
    url = "https://www.united.com/en/us/fly/help-center.html"
    steps = [
        f"Go to url '{url}'.",
        *_ui_hygiene(),
        f"Open the '{topic}' section and highlight two key points.",
    ]
    return {"task_type": "united_help_center_topic", "topic": topic, "steps": steps}


_TASK_GENERATORS: Dict[UNITED_TASK_TYPES, Callable[[dict], dict]] = {
    "united_one_way_search": united_one_way_search,
    "united_round_trip_search": united_round_trip_search,
    "united_filter_nonstop": united_filter_nonstop,
    "united_filter_cabin": united_filter_cabin,
    "united_price_cap": united_price_cap,
    "united_baggage_info": united_baggage_info,
    "united_mileageplus_info": united_mileageplus_info,
    "united_flight_status": united_flight_status,
    "united_change_cancel_info": united_change_cancel_info,
    "united_help_center_topic": united_help_center_topic,
}


def generate_united_task(task_type: UNITED_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = get_instruction("United", task["steps"]).model_dump()
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
    items = list(UNITED_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_united_task, ttype, p))
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