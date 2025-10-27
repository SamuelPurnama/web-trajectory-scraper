import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

EXTRASPACE_TASK_TYPES = Literal[
    "extraspace_basic_search",
    "extraspace_filter_city",
    "extraspace_filter_unit_size",
    "extraspace_sort_price",
    "extraspace_check_specials",
    "extraspace_view_facility_details",
    "extraspace_check_access_hours",
    "extraspace_check_amenities",
    "extraspace_reserve_unit_flow",
    "extraspace_help_center_topic",
    "extraspace_navigate_locations",
]

EXTRASPACE_SAMPLING_CONFIG: Dict[EXTRASPACE_TASK_TYPES, int] = {
    "extraspace_basic_search": 10,
    "extraspace_filter_city": 10,
    "extraspace_filter_unit_size": 10,
    "extraspace_sort_price": 10,
    "extraspace_check_specials": 10,
    "extraspace_view_facility_details": 10,
    "extraspace_check_access_hours": 10,
    "extraspace_check_amenities": 10,
    "extraspace_reserve_unit_flow": 10,
    "extraspace_help_center_topic": 10,
    "extraspace_navigate_locations": 10,
}

CITIES = [
    "Los Angeles", "Chicago", "Houston", "Phoenix", "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "San Francisco", "Charlotte", "Indianapolis", "Seattle", "Denver", "Washington", "Boston", "El Paso",
    "Nashville", "Detroit", "Oklahoma City", "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee", "Albuquerque"
]

ZIP_CODES = [
    "90001", "60601", "77001", "85001", "78201", "92101", "75201", "95101", "78701", "32201",
    "76101", "43201", "94101", "28201", "46201", "98101", "80201", "20001", "02101", "79901",
    "37201", "48201", "73101", "97201", "89101", "38101", "40201", "21201", "53201", "87101"
]

SEARCH_TERMS = [
    "storage", "climate controlled", "drive up", "RV parking", "boat storage", "student storage", "business storage", "vehicle storage",
    "furniture storage", "short term", "long term", "24 hour access", "security", "cheap", "clean", "downtown", "near airport", "university", "garage", "mini storage",
    "locker", "warehouse", "moving", "boxes", "packing", "discount", "special", "first month free", "covered", "outdoor"
]

UNIT_SIZES = [
    "5x5", "5x10", "5x15", "10x10", "10x15", "10x20", "10x25", "10x30", "15x15", "15x20",
    "20x20", "20x25", "20x30", "25x25", "5x20", "7x10", "8x10", "10x12", "12x15", "15x30"
]

PRICE_RANGES = [
    "$10-$20", "$20-$30", "$30-$40", "$40-$50", "$50-$60", "$60-$70", "$70-$80", "$80-$90", "$90-$100", "$100-$120",
    "$120-$140", "$140-$160", "$160-$180", "$180-$200", "$200-$250", "$250-$300", "$300-$350", "$350-$400", "$400-$500", "$500+"
]

AMENITIES = [
    "climate controlled", "drive-up access", "elevator access", "indoor", "outdoor", "24 hour access", "security cameras", "fenced property",
    "gated access", "manager on site", "moving carts", "loading dock", "covered parking", "uncovered parking", "well-lit", "alarm system",
    "handicap accessible", "moving supplies", "online payments", "contactless rentals", "RV parking"
]

SPECIALS = [
    "first month free", "first month half off", "free lock", "no deposit", "online special", "student discount", "military discount",
    "senior discount", "refer a friend", "move-in special", "free truck rental", "price match", "long-term discount", "short-term discount",
    "no admin fee", "prepay discount", "holiday special", "limited time offer", "grand opening special", "free boxes"
]

HELP_TOPICS = [
    "How do I reserve a storage unit?", "What is climate controlled storage?", "How do I access my account?", "What are access hours?",
    "How do I pay my bill online?", "How do I change my reservation?", "What is drive-up access?", "Do I need insurance?",
    "How do I cancel my reservation?", "What size unit do I need?", "How do I contact customer service?", "What is contactless rental?",
    "How do I find a location?", "What amenities are available?", "What is the minimum rental period?", "How do I get a discount?",
    "How do I report an issue?", "How do I update my information?", "What documents do I need?", "How do I move out?"
]

FACILITY_FEATURES = [
    "manager lives on site", "video surveillance", "electronic gate access", "wide drive aisles", "moving carts available", "elevator access",
    "well-lit facility", "indoor units", "outdoor units", "climate controlled units", "non-climate units", "covered parking", "uncovered parking",
    "handicap accessible", "loading dock", "moving supplies for sale", "online bill pay", "contactless rentals", "RV parking", "boat parking"
]

ACCESS_HOURS = [
    "6:00am - 10:00pm", "5:00am - 11:00pm", "24 hours", "7:00am - 7:00pm", "8:00am - 8:00pm", "9:00am - 9:00pm", "6:00am - 8:00pm",
    "7:00am - 9:00pm", "8:00am - 6:00pm", "9:00am - 5:00pm", "10:00am - 6:00pm", "6:00am - 6:00pm", "7:00am - 10:00pm", "8:00am - 10:00pm",
    "9:00am - 8:00pm", "10:00am - 8:00pm", "6:00am - 12:00am", "5:00am - 10:00pm", "7:00am - 8:00pm", "8:00am - 9:00pm"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, location prompts).",
        "Do not enter any personal or payment information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("ExtraSpace", steps).model_dump()

def _rand_date(start_days=1, end_days=60) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _rand_city_zip() -> dict:
    idx = random.randint(0, min(len(CITIES), len(ZIP_CODES))-1)
    return {"city": CITIES[idx], "zip": ZIP_CODES[idx]}

def extraspace_basic_search(_: dict) -> dict:
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.extraspace.com/'.",
        *_ui_hygiene(),
        f"Focus the main search input.",
        f"Type '{term}' and press Enter.",
        "Wait for search results to load.",
        "Verify that at least one result is shown.",
        "Assert that the search term appears in the results page or filter summary.",
    ]
    return {"task_type": "extraspace_basic_search", "search_term": term, "steps": steps}

def extraspace_filter_city(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = [
        "Go to url 'https://www.extraspace.com/'.",
        *_ui_hygiene(),
        "Focus the main search input.",
        f"Type '{city}' and select the city from the autocomplete dropdown.",
        "Wait for search results to load.",
        f"Assert that the results page heading or filter summary includes '{city}'.",
        "Verify that all visible results are in or near '{city}'.",
    ]
    return {"task_type": "extraspace_filter_city", "city": city, "steps": steps}

def extraspace_filter_unit_size(_: dict) -> dict:
    size = random.choice(UNIT_SIZES)
    city = random.choice(CITIES)
    steps = [
        "Go to url 'https://www.extraspace.com/'.",
        *_ui_hygiene(),
        f"Search for storage in '{city}'.",
        "Wait for results to load.",
        "Open the 'Size' filter or equivalent.",
        f"Select unit size '{size}'.",
        "Apply the filter.",
        f"Assert that all visible results offer a '{size}' unit.",
        "Verify that at least one result is shown.",
    ]
    return {"task_type": "extraspace_filter_unit_size", "city": city, "unit_size": size, "steps": steps}

def extraspace_sort_price(_: dict) -> dict:
    city = random.choice(CITIES)
    sort_order = random.choice(["Lowest Price", "Highest Price"])
    steps = [
        "Go to url 'https://www.extraspace.com/'.",
        *_ui_hygiene(),
        f"Search for storage in '{city}'.",
        "Wait for results to load.",
        "Find and open the sort dropdown.",
        f"Select '{sort_order}'.",
        "Verify that results are sorted according to price.",
        "Assert that the first result matches the expected price order.",
    ]
    return {"task_type": "extraspace_sort_price", "city": city, "sort_order": sort_order, "steps": steps}

def extraspace_check_specials(_: dict) -> dict:
    special = random.choice(SPECIALS)
    city = random.choice(CITIES)
    steps = [
        "Go to url 'https://www.extraspace.com/'.",
        *_ui_hygiene(),
        f"Search for storage in '{city}'.",
        "Wait for results to load.",
        "Look for any units or banners advertising specials.",
        f"Verify that at least one result mentions '{special}' if available.",
        "If not found, assert that a 'no specials' message is shown or no special is present.",
    ]
    return {"task_type": "extraspace_check_specials", "city": city, "special": special, "steps": steps}

def extraspace_view_facility_details(_: dict) -> dict:
    city = random.choice(CITIES)
    feature = random.choice(FACILITY_FEATURES)
    steps = [
        "Go to url 'https://www.extraspace.com/'.",
        *_ui_hygiene(),
        f"Search for storage in '{city}'.",
        "Wait for results to load.",
        "Click on the first facility name or 'View Details' link.",
        "Wait for the facility details page to load.",
        f"Verify that the facility page lists '{feature}'.",
        "Assert that the address and contact info are visible.",
    ]
    return {"task_type": "extraspace_view_facility_details", "city": city, "feature": feature, "steps": steps}

def extraspace_check_access_hours(_: dict) -> dict:
    city = random.choice(CITIES)
    hours = random.choice(ACCESS_HOURS)
    steps = [
        "Go to url 'https://www.extraspace.com/'.",
        *_ui_hygiene(),
        f"Search for storage in '{city}'.",
        "Wait for results to load.",
        "Click on the first facility's 'View Details' link.",
        "Wait for the facility page to load.",
        "Locate the 'Access Hours' section.",
        f"Verify that the hours '{hours}' are present or that access hours are clearly listed.",
        "Assert that both office and access hours are shown.",
    ]
    return {"task_type": "extraspace_check_access_hours", "city": city, "access_hours": hours, "steps": steps}

def extraspace_check_amenities(_: dict) -> dict:
    city = random.choice(CITIES)
    amenity = random.choice(AMENITIES)
    steps = [
        "Go to url 'https://www.extraspace.com/'.",
        *_ui_hygiene(),
        f"Search for storage in '{city}'.",
        "Wait for results to load.",
        "Click on the first facility's 'View Details' link.",
        "Wait for the facility page to load.",
        f"Check the amenities/features section for '{amenity}'.",
        f"Assert that '{amenity}' is listed if available, or that a 'not available' indicator is present.",
    ]
    return {"task_type": "extraspace_check_amenities", "city": city, "amenity": amenity, "steps": steps}

def extraspace_reserve_unit_flow(_: dict) -> dict:
    city = random.choice(CITIES)
    size = random.choice(UNIT_SIZES)
    steps = [
        "Go to url 'https://www.extraspace.com/'.",
        *_ui_hygiene(),
        f"Search for storage in '{city}'.",
        "Wait for results to load.",
        f"Filter for unit size '{size}'.",
        "Click 'Reserve' or 'Hold' on the first available unit.",
        "On the reservation form, verify that no payment or personal info is required to proceed.",
        "Attempt to proceed to the next step without entering any info.",
        "Assert that an error message is shown for missing required fields.",
        "Fill in only required fields with generic data (e.g., John Doe, 555-555-5555).",
        "Do not submit the reservation; stop before confirming.",
        "Assert that the reservation summary page is visible and matches the selected unit.",
    ]
    return {"task_type": "extraspace_reserve_unit_flow", "city": city, "unit_size": size, "steps": steps}

def extraspace_help_center_topic(_: dict) -> dict:
    topic = random.choice(HELP_TOPICS)
    steps = [
        "Go to url 'https://www.extraspace.com/help/'.",
        *_ui_hygiene(),
        f"Search for or select the help topic: '{topic}'.",
        "Verify that the help article or FAQ page loads.",
        "Assert that at least two relevant points or answers are visible.",
    ]
    return {"task_type": "extraspace_help_center_topic", "help_topic": topic, "steps": steps}

def extraspace_navigate_locations(_: dict) -> dict:
    city = random.choice(CITIES)
    zip_code = random.choice(ZIP_CODES)
    steps = [
        "Go to url 'https://www.extraspace.com/locations/'.",
        *_ui_hygiene(),
        f"Use the location search to enter city '{city}' or zip code '{zip_code}'.",
        "Select the location from autocomplete if available.",
        "Wait for the list of facilities to load.",
        "Verify that at least one facility is shown for the city or zip.",
        "Assert that the page heading or filter summary matches the city or zip.",
    ]
    return {"task_type": "extraspace_navigate_locations", "city": city, "zip": zip_code, "steps": steps}

_TASK_GENERATORS: Dict[EXTRASPACE_TASK_TYPES, Callable[[dict], dict]] = {
    "extraspace_basic_search": extraspace_basic_search,
    "extraspace_filter_city": extraspace_filter_city,
    "extraspace_filter_unit_size": extraspace_filter_unit_size,
    "extraspace_sort_price": extraspace_sort_price,
    "extraspace_check_specials": extraspace_check_specials,
    "extraspace_view_facility_details": extraspace_view_facility_details,
    "extraspace_check_access_hours": extraspace_check_access_hours,
    "extraspace_check_amenities": extraspace_check_amenities,
    "extraspace_reserve_unit_flow": extraspace_reserve_unit_flow,
    "extraspace_help_center_topic": extraspace_help_center_topic,
    "extraspace_navigate_locations": extraspace_navigate_locations,
}

def generate_extraspace_task(task_type: EXTRASPACE_TASK_TYPES, payload: dict) -> dict:
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
    items = list(EXTRASPACE_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_extraspace_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)