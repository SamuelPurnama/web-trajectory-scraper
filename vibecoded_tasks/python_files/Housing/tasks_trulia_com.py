import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

TRULIA_TASK_TYPES = Literal[
    "trulia_home_search",
    "trulia_rent_search",
    "trulia_filter_beds_baths",
    "trulia_filter_price_range",
    "trulia_filter_home_type",
    "trulia_filter_amenities",
    "trulia_sort_newest",
    "trulia_sort_lowest_price",
    "trulia_property_detail",
    "trulia_save_home_flow",
    "trulia_contact_agent_flow",
    "trulia_neighborhood_explorer",
    "trulia_school_filter",
    "trulia_map_draw_search",
    "trulia_sign_up_flow",
]

TRULIA_SAMPLING_CONFIG: Dict[TRULIA_TASK_TYPES, int] = {
    "trulia_home_search": 10,
    "trulia_rent_search": 10,
    "trulia_filter_beds_baths": 10,
    "trulia_filter_price_range": 10,
    "trulia_filter_home_type": 10,
    "trulia_filter_amenities": 10,
    "trulia_sort_newest": 10,
    "trulia_sort_lowest_price": 10,
    "trulia_property_detail": 10,
    "trulia_save_home_flow": 10,
    "trulia_contact_agent_flow": 10,
    "trulia_neighborhood_explorer": 10,
    "trulia_school_filter": 10,
    "trulia_map_draw_search": 10,
    "trulia_sign_up_flow": 10,
}

CITIES = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
    "Boston, MA", "Nashville, TN", "El Paso, TX", "Detroit, MI", "Oklahoma City, OK"
]

RENT_CITIES = [
    "Miami, FL", "Atlanta, GA", "Orlando, FL", "Portland, OR", "Las Vegas, NV",
    "Minneapolis, MN", "Tampa, FL", "Sacramento, CA", "Raleigh, NC", "Kansas City, MO",
    "Cleveland, OH", "Pittsburgh, PA", "Salt Lake City, UT", "St. Louis, MO", "Baltimore, MD",
    "Cincinnati, OH", "Milwaukee, WI", "San Jose, CA", "San Diego, CA", "Dallas, TX",
    "Phoenix, AZ", "Houston, TX", "Denver, CO", "Charlotte, NC", "Seattle, WA"
]

PRICE_RANGES = [
    "$100k-$200k", "$200k-$300k", "$300k-$400k", "$400k-$500k", "$500k-$600k",
    "$600k-$700k", "$700k-$800k", "$800k-$900k", "$900k-$1M", "$1M-$1.2M",
    "$1.2M-$1.5M", "$1.5M-$2M", "$2M-$2.5M", "$2.5M-$3M", "$3M-$4M",
    "$4M-$5M", "$5M-$7M", "$7M-$10M", "$10M-$15M", "$15M-$20M", "$20M+"
]

BED_BATH_COMBOS = [
    {"beds": 1, "baths": 1}, {"beds": 2, "baths": 1}, {"beds": 2, "baths": 2},
    {"beds": 3, "baths": 2}, {"beds": 3, "baths": 3}, {"beds": 4, "baths": 2},
    {"beds": 4, "baths": 3}, {"beds": 5, "baths": 3}, {"beds": 5, "baths": 4},
    {"beds": 6, "baths": 4}, {"beds": 1, "baths": 2}, {"beds": 2, "baths": 3},
    {"beds": 3, "baths": 1}, {"beds": 4, "baths": 1}, {"beds": 5, "baths": 2},
    {"beds": 6, "baths": 3}, {"beds": 2, "baths": 4}, {"beds": 3, "baths": 4},
    {"beds": 4, "baths": 4}, {"beds": 5, "baths": 5}, {"beds": 6, "baths": 5}
]

HOME_TYPES = [
    "Single-Family Home", "Condo", "Townhome", "Multi-Family Home", "Apartment",
    "Co-op", "Lot/Land", "Mobile/Manufactured", "Farm", "House", "Duplex",
    "Triplex", "Quadruplex", "Loft", "Studio", "Cottage", "Cabin", "Tiny Home",
    "Villa", "Bungalow", "Mansion", "Ranch", "Row House"
]

AMENITIES = [
    "Pool", "Garage", "Fireplace", "Air Conditioning", "Basement", "Hardwood Floors",
    "Fenced Yard", "Walk-In Closet", "Laundry Room", "Patio", "Balcony", "Elevator",
    "Wheelchair Access", "Fitness Center", "Doorman", "Pet Friendly", "Washer/Dryer",
    "Dishwasher", "Security System", "Garden", "Solar Panels", "Smart Home", "Sauna"
]

SCHOOL_RATINGS = [
    "10/10", "9/10", "8/10", "7/10", "6/10", "5/10", "4/10", "3/10", "2/10", "1/10",
    "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"
]

NEIGHBORHOODS = [
    "Upper East Side", "Williamsburg", "Lincoln Park", "Downtown", "Capitol Hill",
    "Silver Lake", "SoHo", "The Heights", "Mission District", "Back Bay",
    "Greenwich Village", "Hyde Park", "Queen Anne", "South End", "Echo Park",
    "Lakeview", "Ballard", "Old Town", "Nob Hill", "West Loop", "Harlem",
    "North End", "South Beach"
]

EMAIL_DOMAINS = [
    "example.com", "mail.com", "testmail.com", "fakemail.org", "samplemail.net",
    "myinbox.com", "webmail.com", "mailinator.com", "tempmail.com", "mailbox.org",
    "email.com", "mailservice.com", "mailhub.com", "postbox.com", "truliamail.com",
    "inboxnow.com", "mailcity.com", "mailplanet.com", "mailbox.net", "mailworld.com"
]

def _rand_email():
    user = f"user{random.randint(10000,99999)}"
    domain = random.choice(EMAIL_DOMAINS)
    return f"{user}@{domain}"

def _rand_phone():
    return f"555-{random.randint(100,999)}-{random.randint(1000,9999)}"

def _rand_date(start_days=1, end_days=60) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, cookie banners, or sign-up prompts.",
        "Do not submit any personal information.",
    ]

def _search_home_steps(city: str) -> list[str]:
    return [
        "Go to url 'https://www.trulia.com'.",
        *_ui_hygiene(),
        "Ensure the 'Buy' tab is selected.",
        f"Focus the main search input and type '{city}'.",
        f"Select '{city}' from the autocomplete dropdown.",
        "Click the search button.",
        "Wait for the listings page to load.",
        f"Assert that the results page title or heading contains '{city}'."
    ]

def _search_rent_steps(city: str) -> list[str]:
    return [
        "Go to url 'https://www.trulia.com'.",
        *_ui_hygiene(),
        "Select the 'Rent' tab.",
        f"Focus the main search input and type '{city}'.",
        f"Select '{city}' from the autocomplete dropdown.",
        "Click the search button.",
        "Wait for the rental listings page to load.",
        f"Assert that the results page title or heading contains '{city}'."
    ]

def _filter_beds_baths_steps(city: str, beds: int, baths: int) -> list[str]:
    return _search_home_steps(city) + [
        f"Open the 'Beds & Baths' filter.",
        f"Set beds to '{beds}+' and baths to '{baths}+'.",
        "Apply the filter.",
        "Wait for results to update.",
        f"Assert that all visible listings show at least {beds} beds and {baths} baths."
    ]

def _filter_price_range_steps(city: str, price_range: str) -> list[str]:
    return _search_home_steps(city) + [
        "Open the 'Price' filter.",
        f"Set the price range to '{price_range}'.",
        "Apply the filter.",
        "Wait for results to update.",
        f"Assert that all visible listings are within the '{price_range}' range."
    ]

def _filter_home_type_steps(city: str, home_type: str) -> list[str]:
    return _search_home_steps(city) + [
        "Open the 'Home Type' filter.",
        f"Select '{home_type}'.",
        "Apply the filter.",
        "Wait for results to update.",
        f"Assert that all visible listings are of type '{home_type}'."
    ]

def _filter_amenities_steps(city: str, amenity: str) -> list[str]:
    return _search_home_steps(city) + [
        "Open the 'More Filters' section.",
        f"Select the '{amenity}' amenity.",
        "Apply the filter.",
        "Wait for results to update.",
        f"Assert that all visible listings include '{amenity}'."
    ]

def _sort_newest_steps(city: str) -> list[str]:
    return _search_home_steps(city) + [
        "Open the 'Sort' dropdown.",
        "Select 'Newest Listings'.",
        "Wait for results to update.",
        "Assert that the first listing is among the most recently posted."
    ]

def _sort_lowest_price_steps(city: str) -> list[str]:
    return _search_home_steps(city) + [
        "Open the 'Sort' dropdown.",
        "Select 'Lowest Price'.",
        "Wait for results to update.",
        "Assert that the first listing has the lowest price among visible results."
    ]

def _property_detail_steps(city: str) -> list[str]:
    return _search_home_steps(city) + [
        "Click on the first listing card.",
        "Wait for the property detail page to load.",
        "Assert that the address and price are visible.",
        "Assert that the property page URL contains '/property/' or similar."
    ]

def _save_home_flow_steps(city: str) -> list[str]:
    return _search_home_steps(city) + [
        "Click on the first listing card.",
        "Wait for the property detail page to load.",
        "Click the 'Save' or 'Heart' button.",
        "If prompted, do not sign up; verify that a sign-in/sign-up modal appears.",
        "Assert that the listing is marked as saved (UI change or modal shown)."
    ]

def _contact_agent_flow_steps(city: str) -> list[str]:
    email = _rand_email()
    phone = _rand_phone()
    return _search_home_steps(city) + [
        "Click on the first listing card.",
        "Wait for the property detail page to load.",
        "Scroll to the 'Contact Agent' form.",
        f"Fill in the name field with 'Test User'.",
        f"Fill in the email field with '{email}'.",
        f"Fill in the phone field with '{phone}'.",
        "Enter 'I am interested in this property.' in the message box.",
        "Do not submit the form.",
        "Assert that the 'Send' or 'Contact' button is enabled.",
        "Clear the email field and verify the button is disabled.",
        "Refill the email field and verify the button is enabled again."
    ]

def _neighborhood_explorer_steps(neighborhood: str) -> list[str]:
    return [
        "Go to url 'https://www.trulia.com/neighborhoods/'.",
        *_ui_hygiene(),
        f"Search for '{neighborhood}' in the neighborhood search bar.",
        f"Select '{neighborhood}' from the suggestions.",
        "Wait for the neighborhood page to load.",
        f"Assert that the page heading contains '{neighborhood}'.",
        "Verify that at least one neighborhood feature (e.g., reviews, map, stats) is visible."
    ]

def _school_filter_steps(city: str, rating: str) -> list[str]:
    return _search_home_steps(city) + [
        "Open the 'Schools' filter.",
        f"Set minimum school rating to '{rating}'.",
        "Apply the filter.",
        "Wait for results to update.",
        f"Assert that all visible listings are near schools rated '{rating}' or higher."
    ]

def _map_draw_search_steps(city: str) -> list[str]:
    return _search_home_steps(city) + [
        "Click the 'Draw' button on the map.",
        "Draw a custom shape on the map covering part of the city.",
        "Apply the drawn area as a filter.",
        "Wait for results to update.",
        "Assert that all visible listings are within the drawn map area."
    ]

def _sign_up_flow_steps() -> list[str]:
    email = _rand_email()
    return [
        "Go to url 'https://www.trulia.com'.",
        *_ui_hygiene(),
        "Click the 'Sign Up' or 'Join' button in the header.",
        "Wait for the sign-up form/modal to appear.",
        f"Fill in the email field with '{email}'.",
        "Fill in the password field with 'TestPassword123!'.",
        "Do not submit the form.",
        "Assert that the 'Sign Up' or 'Create Account' button is enabled.",
        "Clear the email field and verify the button is disabled.",
        "Refill the email field and verify the button is enabled again."
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Trulia", steps).model_dump()

def trulia_home_search(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = _search_home_steps(city)
    return {
        "task_type": "trulia_home_search",
        "city": city,
        "steps": steps
    }

def trulia_rent_search(_: dict) -> dict:
    city = random.choice(RENT_CITIES)
    steps = _search_rent_steps(city)
    return {
        "task_type": "trulia_rent_search",
        "city": city,
        "steps": steps
    }

def trulia_filter_beds_baths(_: dict) -> dict:
    combo = random.choice(BED_BATH_COMBOS)
    city = random.choice(CITIES)
    steps = _filter_beds_baths_steps(city, combo["beds"], combo["baths"])
    return {
        "task_type": "trulia_filter_beds_baths",
        "city": city,
        "beds": combo["beds"],
        "baths": combo["baths"],
        "steps": steps
    }

def trulia_filter_price_range(_: dict) -> dict:
    price_range = random.choice(PRICE_RANGES)
    city = random.choice(CITIES)
    steps = _filter_price_range_steps(city, price_range)
    return {
        "task_type": "trulia_filter_price_range",
        "city": city,
        "price_range": price_range,
        "steps": steps
    }

def trulia_filter_home_type(_: dict) -> dict:
    home_type = random.choice(HOME_TYPES)
    city = random.choice(CITIES)
    steps = _filter_home_type_steps(city, home_type)
    return {
        "task_type": "trulia_filter_home_type",
        "city": city,
        "home_type": home_type,
        "steps": steps
    }

def trulia_filter_amenities(_: dict) -> dict:
    amenity = random.choice(AMENITIES)
    city = random.choice(CITIES)
    steps = _filter_amenities_steps(city, amenity)
    return {
        "task_type": "trulia_filter_amenities",
        "city": city,
        "amenity": amenity,
        "steps": steps
    }

def trulia_sort_newest(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = _sort_newest_steps(city)
    return {
        "task_type": "trulia_sort_newest",
        "city": city,
        "steps": steps
    }

def trulia_sort_lowest_price(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = _sort_lowest_price_steps(city)
    return {
        "task_type": "trulia_sort_lowest_price",
        "city": city,
        "steps": steps
    }

def trulia_property_detail(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = _property_detail_steps(city)
    return {
        "task_type": "trulia_property_detail",
        "city": city,
        "steps": steps
    }

def trulia_save_home_flow(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = _save_home_flow_steps(city)
    return {
        "task_type": "trulia_save_home_flow",
        "city": city,
        "steps": steps
    }

def trulia_contact_agent_flow(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = _contact_agent_flow_steps(city)
    return {
        "task_type": "trulia_contact_agent_flow",
        "city": city,
        "steps": steps
    }

def trulia_neighborhood_explorer(_: dict) -> dict:
    neighborhood = random.choice(NEIGHBORHOODS)
    steps = _neighborhood_explorer_steps(neighborhood)
    return {
        "task_type": "trulia_neighborhood_explorer",
        "neighborhood": neighborhood,
        "steps": steps
    }

def trulia_school_filter(_: dict) -> dict:
    city = random.choice(CITIES)
    rating = random.choice(SCHOOL_RATINGS)
    steps = _school_filter_steps(city, rating)
    return {
        "task_type": "trulia_school_filter",
        "city": city,
        "school_rating": rating,
        "steps": steps
    }

def trulia_map_draw_search(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = _map_draw_search_steps(city)
    return {
        "task_type": "trulia_map_draw_search",
        "city": city,
        "steps": steps
    }

def trulia_sign_up_flow(_: dict) -> dict:
    steps = _sign_up_flow_steps()
    return {
        "task_type": "trulia_sign_up_flow",
        "steps": steps
    }

_TASK_GENERATORS: Dict[TRULIA_TASK_TYPES, Callable[[dict], dict]] = {
    "trulia_home_search": trulia_home_search,
    "trulia_rent_search": trulia_rent_search,
    "trulia_filter_beds_baths": trulia_filter_beds_baths,
    "trulia_filter_price_range": trulia_filter_price_range,
    "trulia_filter_home_type": trulia_filter_home_type,
    "trulia_filter_amenities": trulia_filter_amenities,
    "trulia_sort_newest": trulia_sort_newest,
    "trulia_sort_lowest_price": trulia_sort_lowest_price,
    "trulia_property_detail": trulia_property_detail,
    "trulia_save_home_flow": trulia_save_home_flow,
    "trulia_contact_agent_flow": trulia_contact_agent_flow,
    "trulia_neighborhood_explorer": trulia_neighborhood_explorer,
    "trulia_school_filter": trulia_school_filter,
    "trulia_map_draw_search": trulia_map_draw_search,
    "trulia_sign_up_flow": trulia_sign_up_flow,
}

def generate_trulia_task(task_type: TRULIA_TASK_TYPES, payload: dict) -> dict:
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
    items = list(TRULIA_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_trulia_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)