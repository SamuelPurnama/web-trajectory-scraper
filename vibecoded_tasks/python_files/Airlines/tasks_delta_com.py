import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

DELTA_TASK_TYPES = Literal[
    "delta_one_way_search",
    "delta_round_trip_search",
    "delta_filter_nonstop",
    "delta_filter_cabin",
    "delta_sort_lowest",
    "delta_price_cap",
    "delta_time_window_filter",
    "delta_fare_details",
    "delta_baggage_info",
    "delta_change_cancel_info",
    "delta_ecredit_page",
    "delta_premium_select_info",
    "delta_flight_deals",
    "delta_discover_map",
    "delta_join_skymiles",
    "delta_mobile_app_page",
    "delta_help_center_topic",
]

DELTA_SAMPLING_CONFIG: Dict[DELTA_TASK_TYPES, int] = {
    "delta_one_way_search": 10,
    "delta_round_trip_search": 10,
    "delta_filter_nonstop": 10,
    "delta_filter_cabin": 10,
    "delta_sort_lowest": 10,
    "delta_price_cap": 10,
    "delta_time_window_filter": 10,
    "delta_fare_details": 10,
    "delta_baggage_info": 10,
    "delta_change_cancel_info": 10,
    "delta_ecredit_page": 10,
    "delta_premium_select_info": 10,
    "delta_flight_deals": 10,
    "delta_discover_map": 10,
    "delta_join_skymiles": 10,
    "delta_mobile_app_page": 10,
    "delta_help_center_topic": 10,
}

AIRPORTS = ["SEA","SFO","LAX","SAN","PHX","DEN","SLC","PDX","LAS","AUS",
            "DFW","IAH","ORD","MSP","ATL","MCO","JFK","EWR","BOS","BWI",
            "IAD","CLT","RDU"]
INTL = ["YVR","YYZ","CUN","SJD"]
EASY_PAIRS = [("SEA","SFO"),("LAX","SFO"),("SEA","DEN"),("PHX","DEN"),
              ("PDX","SLC"),("AUS","DEN"),("LAX","LAS"),("JFK","BOS"),
              ("EWR","CLT")]
CABINS_EASY = ["Main Cabin","Comfort+","First Class"]
WINDOWS = ["Morning (5–11am)","Afternoon (12–5pm)"]
BAGS = ["carry-on size/weight","first checked bag fees","oversize/overweight fees",
        "sports equipment","musical instruments","international baggage differences"]
CHANGE_FOCI = ["how to cancel online","same-day change eligibility","award ticket change rules",
               "24-hour risk-free cancellation","refund vs eCredit after cancel",
               "Basic Economy change/cancel policy","change fees on international flights",
               "how to rebook after cancellation"]
HELP_TOPICS = [("Refunds & eCredits","refunds-and-compensation"),
               ("Seat Selection","seats"),("Travel Documents","travel-documents"),
               ("Travel Waivers","alerts"),("Check-in","check-in"),
               ("Disability & Assistance","special-assistance")]

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
        "Dismiss popups/banners (e.g., 'I understand', 'Join SkyMiles for free', 'Shop with miles').",
        "Do not book or purchase anything; only search and view results.",
    ]

def _book_home() -> list[str]:
    return [
        "Go to url 'https://www.delta.com' with the booking widget visible.",
        "Ensure the 'BOOK' tab is active.",
        *_ui_hygiene(),
    ]

def _calendar_done_step() -> str:
    return "After setting dates, click 'Done' on the calendar/date picker."

def _instr(steps: list[str]) -> dict:
    return get_instruction("Delta", steps).model_dump()

def _from_to_steps(origin: str, dest: str, prefix: str = "") -> list[str]:
    p = (prefix + " ") if prefix else ""
    return [
        f"{p}Focus the 'From' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{origin}'.",
        f"{p}Select the autocomplete option for '{origin}' (airport).",
        f"{p}Confirm origin shows '{origin}' with correct city; press Enter if needed.",
        f"{p}Close the autocomplete/dropdown before proceeding (e.g., Tab or click outside).",
        f"{p}Focus the 'To' field.",
        f"{p}Clear/reset the field.",
        f"{p}Type '{dest}'.",
        f"{p}Select the autocomplete option for '{dest}' (airport).",
        f"{p}Confirm destination shows '{dest}' with correct city; press Enter if needed.",
        f"{p}Ensure the dropdown is closed before proceeding.",
    ]

def delta_one_way_search(_: dict) -> dict:
    t = _trip_base(oneway=True, domestic=True)
    steps = _book_home() + [
        "Select 'One Way' and press Enter to confirm.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set depart date to '{t['depart']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Shop' to view results.",
    ]
    return {"task_type":"delta_one_way_search",**t,"steps":steps}

def delta_round_trip_search(_: dict) -> dict:
    t = _trip_base(domestic=True)
    steps = _book_home() + [
        "Select 'Round Trip' and press Enter to confirm.",
        *_from_to_steps(t["from"], t["to"]),
        f"Set dates: depart '{t['depart']}', return '{t['return']}'.",
        _calendar_done_step(),
        "Set travelers to 1 adult.",
        "Click 'Shop' to view results.",
    ]
    return {"task_type":"delta_round_trip_search",**t,"steps":steps}

def delta_filter_nonstop(_: dict) -> dict:
    base = delta_round_trip_search({})
    base["task_type"]="delta_filter_nonstop"
    base["steps"] += ["Enable the 'Nonstop' filter.","Ensure any search box/dropdown is closed before continuing."]
    return base

def delta_filter_cabin(_: dict) -> dict:
    base = delta_round_trip_search({})
    cabin = random.choice(CABINS_EASY)
    base["task_type"]="delta_filter_cabin"
    base["target_cabin"]=cabin
    base["steps"] += [f"Filter/select cabin to '{cabin}'.","Ensure any search box/dropdown is closed before continuing."]
    return base

def delta_sort_lowest(_: dict) -> dict:
    base = delta_round_trip_search({})
    base["task_type"]="delta_sort_lowest"
    base["steps"] += ["Sort by lowest price.","Ensure any search box/dropdown is closed before continuing."]
    return base

def delta_price_cap(_: dict) -> dict:
    base = delta_round_trip_search({})
    cap = random.choice([150, 250, 400, 600, 800, 1200])
    base["task_type"]="delta_price_cap"
    base["max_price"]=cap
    base["steps"] += [f"Use filters to find itineraries ≤ ${cap}; list the first one if any.","Ensure any search box/dropdown is closed before continuing."]
    return base

def delta_time_window_filter(_: dict) -> dict:
    base = delta_round_trip_search({})
    win = random.choice(WINDOWS)
    base["task_type"]="delta_time_window_filter"
    base["window"]=win
    base["steps"] += [f"Filter outbound departure time to {win}.","Ensure any search box/dropdown is closed before continuing."]
    return base

def delta_fare_details(_: dict) -> dict:
    base = delta_round_trip_search({})
    base["task_type"]="delta_fare_details"
    base["focus"]="fare rules panel"
    base["steps"] += ["Open fare details on the first result and confirm a fare rules panel appears.","Do not book; only view details."]
    return base

def delta_baggage_info(_: dict) -> dict:
    focus = random.choice(BAGS)
    steps = [
        "Go to url 'https://www.delta.com/us/en/baggage/overview'.",
        *_ui_hygiene(),
        f"Find and summarize: {focus}.",
    ]
    return {"task_type":"delta_baggage_info","focus":focus,"steps":steps}

def delta_change_cancel_info(_: dict) -> dict:
    focus = random.choice(CHANGE_FOCI)
    steps = [
        "Go to url 'https://www.delta.com/us/en/travel-planning-center/travel-planning-overview#changeorcancel'.",
        *_ui_hygiene(),
        f"On that page, summarize: {focus}.",
    ]
    return {"task_type":"delta_change_cancel_info","focus":focus,"steps":steps}

def delta_ecredit_page(_: dict) -> dict:
    want = random.choice(["verify eCredit lookup fields are present","locate terms on eCredit expiration",
                          "find how to combine multiple eCredits","check if gift cards can be combined with eCredits"])
    steps = [
        "Go to url 'https://www.delta.com/redeem-ecredit/'.",
        *_ui_hygiene(),
        f"{want.capitalize()}.",
    ]
    return {"task_type":"delta_ecredit_page","focus":want,"steps":steps}

def delta_premium_select_info(_: dict) -> dict:
    want = random.choice(["seat features","amenities kit","dining","baggage allowance","priority services"])
    steps = [
        "Go to url 'https://www.delta.com/us/en/onboard/onboard-experience/delta-premium-economy'.",
        *_ui_hygiene(),
        f"List two concise perks about {want}.",
    ]
    return {"task_type":"delta_premium_select_info","focus":want,"steps":steps}

def delta_flight_deals(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.delta.com/us/en/flight-deals/current-flight-deals'.",
        *_ui_hygiene(),
        "Report one domestic deal: destination and lowest price shown.",
    ]
    return {"task_type":"delta_flight_deals","focus":"single domestic deal","steps":steps}

def delta_discover_map(_: dict) -> dict:
    target = random.choice(["Mexico","Canada"])
    steps = [
        "Go to url 'https://www.delta.com/us/en/travel-planning-center/find-your-destination/explore-top-destinations'.",
        *_ui_hygiene(),
        f"Open the '{target}' card and note the first visible blurb.",
    ]
    return {"task_type":"delta_discover_map","destination":target,"steps":steps}

def delta_join_skymiles(_: dict) -> dict:
    verify = random.choice(["name/email fields","password requirements","marketing opt-in checkbox","country/phone fields"])
    steps = [
        "Go to url 'https://www.delta.com/joinskymiles/'.",
        *_ui_hygiene(),
        f"Verify the presence of {verify}.",
    ]
    return {"task_type":"delta_join_skymiles","verify":verify,"steps":steps}

def delta_mobile_app_page(_: dict) -> dict:
    focus = random.choice(["check-in feature","live flight status","same-day changes","wallet/eCredits support"])
    steps = [
        "Go to url 'https://www.delta.com/us/en/delta-digital/mobile'.",
        *_ui_hygiene(),
        f"Confirm the page mentions {focus}.",
    ]
    return {"task_type":"delta_mobile_app_page","focus":focus,"steps":steps}

def delta_help_center_topic(_: dict) -> dict:
    topic, slug = random.choice(HELP_TOPICS)
    url = "https://www.delta.com/us/en/need-help/overview"
    steps = [
        f"Go to url '{url}'.",
        *_ui_hygiene(),
        f"Open the '{topic}' section (or its linked page) and summarize the first two key points.",
    ]
    return {"task_type":"delta_help_center_topic","topic":topic,"steps":steps}

_TASK_GENERATORS: Dict[DELTA_TASK_TYPES, Callable[[dict], dict]] = {
    "delta_one_way_search": delta_one_way_search,
    "delta_round_trip_search": delta_round_trip_search,
    "delta_filter_nonstop": delta_filter_nonstop,
    "delta_filter_cabin": delta_filter_cabin,
    "delta_sort_lowest": delta_sort_lowest,
    "delta_price_cap": delta_price_cap,
    "delta_time_window_filter": delta_time_window_filter,
    "delta_fare_details": delta_fare_details,
    "delta_baggage_info": delta_baggage_info,
    "delta_change_cancel_info": delta_change_cancel_info,
    "delta_ecredit_page": delta_ecredit_page,
    "delta_premium_select_info": delta_premium_select_info,
    "delta_flight_deals": delta_flight_deals,
    "delta_discover_map": delta_discover_map,
    "delta_join_skymiles": delta_join_skymiles,
    "delta_mobile_app_page": delta_mobile_app_page,
    "delta_help_center_topic": delta_help_center_topic,
}

def generate_delta_task(task_type: DELTA_TASK_TYPES, payload: dict) -> dict:
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
    items = list(DELTA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_delta_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)