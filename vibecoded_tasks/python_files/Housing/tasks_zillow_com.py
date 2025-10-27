import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

ZILLOW_TASK_TYPES = Literal[
    "zillow_home_search",
    "zillow_rent_search",
    "zillow_sold_search",
    "zillow_filter_price",
    "zillow_filter_beds_baths",
    "zillow_filter_home_type",
    "zillow_filter_days_on_zillow",
    "zillow_sort_results",
    "zillow_pagination",
    "zillow_view_home_details",
    "zillow_save_home",
    "zillow_draw_map_search",
    "zillow_school_filter",
]

ZILLOW_SAMPLING_CONFIG: Dict[ZILLOW_TASK_TYPES, int] = {
    "zillow_home_search": 10,
    "zillow_rent_search": 10,
    "zillow_sold_search": 10,
    "zillow_filter_price": 10,
    "zillow_filter_beds_baths": 10,
    "zillow_filter_home_type": 10,
    "zillow_filter_days_on_zillow": 10,
    "zillow_sort_results": 10,
    "zillow_pagination": 10,
    "zillow_view_home_details": 10,
    "zillow_save_home": 10,
    "zillow_draw_map_search": 10,
    "zillow_school_filter": 10,
}

CITIES = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
    "Boston, MA", "Nashville, TN", "El Paso, TX", "Detroit, MI", "Oklahoma City, OK"
]

NEIGHBORHOODS = [
    "Upper East Side, New York, NY", "Hollywood, Los Angeles, CA", "Lincoln Park, Chicago, IL",
    "Montrose, Houston, TX", "Arcadia, Phoenix, AZ", "Fishtown, Philadelphia, PA",
    "Alamo Heights, San Antonio, TX", "La Jolla, San Diego, CA", "Lakewood, Dallas, TX",
    "Willow Glen, San Jose, CA", "Zilker, Austin, TX", "Riverside, Jacksonville, FL",
    "Tanglewood, Fort Worth, TX", "German Village, Columbus, OH", "Dilworth, Charlotte, NC",
    "Mission District, San Francisco, CA", "Broad Ripple, Indianapolis, IN", "Ballard, Seattle, WA",
    "Capitol Hill, Denver, CO", "Georgetown, Washington, DC", "Back Bay, Boston, MA",
    "East Nashville, Nashville, TN", "Kern Place, El Paso, TX", "Corktown, Detroit, MI",
    "Bricktown, Oklahoma City, OK"
]

PRICE_RANGES = [
    (50000, 100000), (100000, 150000), (150000, 200000), (200000, 250000), (250000, 300000),
    (300000, 350000), (350000, 400000), (400000, 450000), (450000, 500000), (500000, 600000),
    (600000, 700000), (700000, 800000), (800000, 900000), (900000, 1000000), (1000000, 1250000),
    (1250000, 1500000), (1500000, 1750000), (1750000, 2000000), (2000000, 2500000), (2500000, 3000000),
    (3000000, 4000000), (4000000, 5000000)
]

BEDS = [0, 1, 2, 3, 4, 5, 6, 7]
BATHS = [1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 7]
HOME_TYPES = [
    "House", "Apartment", "Condo", "Townhouse", "Multi-Family", "Land", "Manufactured",
    "Co-op", "Duplex", "Loft", "Cottage", "Cabin", "Farm", "Villa", "Bungalow", "Ranch",
    "Mobile", "Tiny House", "Penthouse", "Triplex", "Quadruplex", "Other"
]

DAYS_ON_ZILLOW = [
    "Any", "1 day", "3 days", "7 days", "14 days", "30 days", "45 days", "60 days", "90 days",
    "120 days", "180 days", "365 days", "2 years", "3 years", "4 years", "5 years", "6 years",
    "7 years", "8 years", "9 years", "10 years"
]

SORT_OPTIONS = [
    "Newest", "Price (Low to High)", "Price (High to Low)", "Beds", "Baths", "Square Feet",
    "Lot Size", "Year Built", "Open Houses", "3D Tour", "Walk Score", "Transit Score",
    "Bike Score", "Days on Zillow", "HOA Fee", "Monthly Payment", "Price Reduction",
    "Foreclosures", "Recently Sold", "Pending", "Active"
]

SCHOOL_RATINGS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
SCHOOL_LEVELS = ["Elementary", "Middle", "High", "Preschool", "Private", "Charter", "Magnet", "Public", "Alternative", "Online"]

def _rand_city() -> str:
    return random.choice(CITIES)

def _rand_neighborhood() -> str:
    return random.choice(NEIGHBORHOODS)

def _rand_price_range() -> tuple:
    return random.choice(PRICE_RANGES)

def _rand_beds() -> int:
    return random.choice(BEDS)

def _rand_baths() -> float:
    return random.choice(BATHS)

def _rand_home_types() -> list:
    n = random.randint(1, 3)
    return random.sample(HOME_TYPES, n)

def _rand_days_on_zillow() -> str:
    return random.choice(DAYS_ON_ZILLOW)

def _rand_sort_option() -> str:
    return random.choice(SORT_OPTIONS)

def _rand_school_rating() -> int:
    return random.choice(SCHOOL_RATINGS)

def _rand_school_level() -> str:
    return random.choice(SCHOOL_LEVELS)

def _ui_hygiene() -> list:
    return [
        "Dismiss any popups, banners, or cookie notices.",
        "Do not log in or create an account unless specified.",
        "Do not submit any personal information.",
    ]

def _instr(steps: list) -> dict:
    return get_instruction("Zillow", steps).model_dump()

def zillow_home_search(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        f"Focus the search box and type '{city}'.",
        "Select the city from the autocomplete suggestions.",
        "Ensure the search results page loads for the selected city.",
        "Assert that the results page title or heading includes the city name.",
        "Verify that at least one home listing is present.",
    ]
    return {"task_type": "zillow_home_search", "city": city, "steps": steps}

def zillow_rent_search(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        "Click the 'Rent' tab.",
        f"Focus the search box and type '{city}'.",
        "Select the city from the autocomplete suggestions.",
        "Ensure the rental results page loads for the city.",
        "Assert that the page shows rental listings for the city.",
        "Verify that at least one rental listing is present.",
    ]
    return {"task_type": "zillow_rent_search", "city": city, "steps": steps}

def zillow_sold_search(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        "Click the 'Sold' tab.",
        f"Focus the search box and type '{city}'.",
        "Select the city from the autocomplete suggestions.",
        "Ensure the sold homes results page loads for the city.",
        "Assert that the page shows sold listings for the city.",
        "Verify that at least one sold listing is present.",
    ]
    return {"task_type": "zillow_sold_search", "city": city, "steps": steps}

def zillow_filter_price(_: dict) -> dict:
    city = _rand_city()
    price_min, price_max = _rand_price_range()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Open the 'Price' filter.",
        f"Set minimum price to ${price_min:,}.",
        f"Set maximum price to ${price_max:,}.",
        "Apply the filter.",
        "Assert that all visible listings have prices within the selected range.",
    ]
    return {"task_type": "zillow_filter_price", "city": city, "price_min": price_min, "price_max": price_max, "steps": steps}

def zillow_filter_beds_baths(_: dict) -> dict:
    city = _rand_city()
    beds = _rand_beds()
    baths = _rand_baths()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Open the 'Beds & Baths' filter.",
        f"Set minimum beds to {beds}.",
        f"Set minimum baths to {baths}.",
        "Apply the filter.",
        "Assert that all visible listings have at least the selected number of beds and baths.",
    ]
    return {"task_type": "zillow_filter_beds_baths", "city": city, "beds": beds, "baths": baths, "steps": steps}

def zillow_filter_home_type(_: dict) -> dict:
    city = _rand_city()
    home_types = _rand_home_types()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Open the 'Home Type' filter.",
        f"Select home types: {', '.join(home_types)}.",
        "Apply the filter.",
        "Assert that all visible listings match at least one of the selected home types.",
    ]
    return {"task_type": "zillow_filter_home_type", "city": city, "home_types": home_types, "steps": steps}

def zillow_filter_days_on_zillow(_: dict) -> dict:
    city = _rand_city()
    days = _rand_days_on_zillow()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Open the 'More' filter.",
        f"Set 'Days on Zillow' to '{days}'.",
        "Apply the filter.",
        "Assert that all visible listings have been on Zillow for less than or equal to the selected days.",
    ]
    return {"task_type": "zillow_filter_days_on_zillow", "city": city, "days_on_zillow": days, "steps": steps}

def zillow_sort_results(_: dict) -> dict:
    city = _rand_city()
    sort_option = _rand_sort_option()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Open the 'Sort' dropdown.",
        f"Select '{sort_option}' as the sort option.",
        "Assert that the results are sorted according to the selected option.",
    ]
    return {"task_type": "zillow_sort_results", "city": city, "sort_option": sort_option, "steps": steps}

def zillow_pagination(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Scroll to the bottom of the results page.",
        "Click the 'Next' page button.",
        "Assert that the results update to the next page.",
        "Verify that the page indicator shows the new page number.",
        "Click the 'Previous' page button.",
        "Assert that the results return to the previous page.",
    ]
    return {"task_type": "zillow_pagination", "city": city, "steps": steps}

def zillow_view_home_details(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Click on the first home listing.",
        "Assert that the home details page loads.",
        "Verify that the address and price are visible on the details page.",
        "Check that there is a photo gallery or main image present.",
    ]
    return {"task_type": "zillow_view_home_details", "city": city, "steps": steps}

def zillow_save_home(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Click on the first home listing.",
        "On the details page, click the 'Save' or heart icon.",
        "If prompted to sign in, cancel and do not proceed.",
        "Assert that the home is marked as saved (e.g., heart icon is filled or 'Saved' label appears).",
    ]
    return {"task_type": "zillow_save_home", "city": city, "steps": steps}

def zillow_draw_map_search(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Open the map view if not already visible.",
        "Click the 'Draw' button on the map.",
        "Draw a polygon on the map to select a custom area.",
        "Release the mouse to apply the drawn area.",
        "Assert that the results update to only show homes within the drawn area.",
        "Verify that the polygon remains visible on the map.",
    ]
    return {"task_type": "zillow_draw_map_search", "city": city, "steps": steps}

def zillow_school_filter(_: dict) -> dict:
    city = _rand_city()
    rating = _rand_school_rating()
    level = _rand_school_level()
    steps = [
        "Go to url 'https://www.zillow.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Open the 'Schools' filter.",
        f"Set minimum school rating to {rating}.",
        f"Select school level: {level}.",
        "Apply the filter.",
        "Assert that all visible listings are within zones of schools matching the selected rating and level.",
    ]
    return {"task_type": "zillow_school_filter", "city": city, "school_rating": rating, "school_level": level, "steps": steps}

_TASK_GENERATORS: Dict[ZILLOW_TASK_TYPES, Callable[[dict], dict]] = {
    "zillow_home_search": zillow_home_search,
    "zillow_rent_search": zillow_rent_search,
    "zillow_sold_search": zillow_sold_search,
    "zillow_filter_price": zillow_filter_price,
    "zillow_filter_beds_baths": zillow_filter_beds_baths,
    "zillow_filter_home_type": zillow_filter_home_type,
    "zillow_filter_days_on_zillow": zillow_filter_days_on_zillow,
    "zillow_sort_results": zillow_sort_results,
    "zillow_pagination": zillow_pagination,
    "zillow_view_home_details": zillow_view_home_details,
    "zillow_save_home": zillow_save_home,
    "zillow_draw_map_search": zillow_draw_map_search,
    "zillow_school_filter": zillow_school_filter,
}

def generate_zillow_task(task_type: ZILLOW_TASK_TYPES, payload: dict) -> dict:
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
    items = list(ZILLOW_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_zillow_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)