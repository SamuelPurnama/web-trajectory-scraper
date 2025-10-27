import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

REALTOR_TASK_TYPES = Literal[
    "realtor_home_search",
    "realtor_rent_search",
    "realtor_filter_price",
    "realtor_filter_beds_baths",
    "realtor_filter_property_type",
    "realtor_sort_results",
    "realtor_view_listing_details",
    "realtor_contact_agent",
    "realtor_save_listing",
    "realtor_mortgage_calculator",
    "realtor_school_info",
    "realtor_draw_map_area",
]

REALTOR_SAMPLING_CONFIG: Dict[REALTOR_TASK_TYPES, int] = {
    "realtor_home_search": 10,
    "realtor_rent_search": 10,
    "realtor_filter_price": 10,
    "realtor_filter_beds_baths": 10,
    "realtor_filter_property_type": 10,
    "realtor_sort_results": 10,
    "realtor_view_listing_details": 10,
    "realtor_contact_agent": 10,
    "realtor_save_listing": 10,
    "realtor_mortgage_calculator": 10,
    "realtor_school_info": 10,
    "realtor_draw_map_area": 10,
}

CITIES = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
    "Boston, MA", "Nashville, TN", "El Paso, TX", "Detroit, MI", "Oklahoma City, OK",
    "Portland, OR", "Las Vegas, NV", "Memphis, TN", "Louisville, KY", "Baltimore, MD"
]

PROPERTY_TYPES = [
    "Single Family Home", "Condo", "Townhome", "Multi-Family Home", "Apartment",
    "Mobile/Manufactured Home", "Co-op", "Farm", "Land", "Loft",
    "Duplex", "Triplex", "Quadruplex", "Cottage", "Bungalow",
    "Ranch", "Villa", "Cabin", "Penthouse", "Studio",
    "Tiny Home", "Castle", "Mansion", "Row House", "Carriage House"
]

PRICE_RANGES = [
    (50000, 100000), (100000, 150000), (150000, 200000), (200000, 250000), (250000, 300000),
    (300000, 350000), (350000, 400000), (400000, 450000), (450000, 500000), (500000, 600000),
    (600000, 700000), (700000, 800000), (800000, 900000), (900000, 1000000), (1000000, 1250000),
    (1250000, 1500000), (1500000, 1750000), (1750000, 2000000), (2000000, 2500000), (2500000, 3000000),
    (3000000, 4000000), (4000000, 5000000)
]

BED_CHOICES = [1,2,3,4,5,6,7,8,9,10,0]  # 0 = studio/any
BATH_CHOICES = [1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10,10.5,0] # 0 = any

SORT_OPTIONS = [
    "Newest", "Price (Low to High)", "Price (High to Low)", "Beds (Most)", "Baths (Most)",
    "Square Feet (Largest)", "Square Feet (Smallest)", "Lot Size (Largest)", "Lot Size (Smallest)",
    "Open Houses", "Reduced Price", "Recently Sold", "Pending", "Active", "Foreclosure",
    "Auction", "New Construction", "Coming Soon", "Price Reduced", "Recently Listed", "Best Match",
    "Distance", "Walk Score"
]

SCHOOL_TYPES = [
    "Elementary", "Middle", "High", "Private", "Charter", "Magnet", "Public", "Preschool",
    "Montessori", "Religious", "Boarding", "Vocational", "Special Education", "Alternative",
    "Online", "International", "STEM", "Arts", "Language Immersion", "Gifted", "IB", "AP"
]

MAP_DRAW_AREAS = [
    "Downtown", "Suburbs", "Waterfront", "Near Park", "Near School", "Near Hospital",
    "Near Shopping", "Near Airport", "Near University", "Historic District",
    "Business District", "Residential Area", "Industrial Area", "Golf Course", "Lakefront",
    "Mountain View", "Beachfront", "City Center", "Outskirts", "Transit Hub", "Entertainment District"
]

def _rand_future_date(days_ahead_min=10, days_ahead_max=60):
    d0 = dt.date.today() + dt.timedelta(days=random.randint(days_ahead_min, days_ahead_max))
    return d0.strftime("%Y-%m-%d")

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, banners, or cookie notices if present.",
        "Do not submit any personal information or make purchases.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Realtor", steps).model_dump()

def realtor_home_search(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = [
        "Go to url 'https://www.realtor.com'.",
        *_ui_hygiene(),
        "Ensure the 'Buy' tab is selected in the search bar.",
        f"Focus the location input and type '{city}'.",
        f"Select '{city}' from the autocomplete suggestions.",
        "Click the 'Search' button.",
        "Wait for results to load.",
        f"Assert that results page shows homes for sale in '{city}'.",
        "Assert at least 1 result is displayed.",
    ]
    return {"task_type":"realtor_home_search","city":city,"steps":steps}

def realtor_rent_search(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = [
        "Go to url 'https://www.realtor.com'.",
        *_ui_hygiene(),
        "Select the 'Rent' tab in the search bar.",
        f"Focus the location input and type '{city}'.",
        f"Select '{city}' from the autocomplete suggestions.",
        "Click the 'Search' button.",
        "Wait for results to load.",
        f"Assert that results page shows rentals in '{city}'.",
        "Assert at least 1 rental result is displayed.",
    ]
    return {"task_type":"realtor_rent_search","city":city,"steps":steps}

def realtor_filter_price(_: dict) -> dict:
    city = random.choice(CITIES)
    price_min, price_max = random.choice(PRICE_RANGES)
    steps = [
        "Go to url 'https://www.realtor.com'.",
        *_ui_hygiene(),
        "Ensure the 'Buy' tab is selected.",
        f"Type '{city}' in the location input and select from suggestions.",
        "Click 'Search'.",
        "Wait for results to load.",
        f"Open the 'Price' filter and set minimum to ${price_min:,} and maximum to ${price_max:,}.",
        "Apply the price filter.",
        f"Assert all visible listings have price between ${price_min:,} and ${price_max:,}.",
        "Assert at least 1 result is displayed.",
    ]
    return {"task_type":"realtor_filter_price","city":city,"price_min":price_min,"price_max":price_max,"steps":steps}

def realtor_filter_beds_baths(_: dict) -> dict:
    city = random.choice(CITIES)
    beds = random.choice(BED_CHOICES)
    baths = random.choice(BATH_CHOICES)
    beds_label = f"{beds}+" if beds else "Any"
    baths_label = f"{baths}+" if baths else "Any"
    steps = [
        "Go to url 'https://www.realtor.com'.",
        *_ui_hygiene(),
        "Ensure the 'Buy' tab is selected.",
        f"Type '{city}' in the location input and select from suggestions.",
        "Click 'Search'.",
        "Wait for results to load.",
        f"Open the 'Beds & Baths' filter.",
        f"Set beds to '{beds_label}'.",
        f"Set baths to '{baths_label}'.",
        "Apply the filter.",
        f"Assert all visible listings have at least {beds_label} beds and {baths_label} baths.",
        "Assert at least 1 result is displayed.",
    ]
    return {"task_type":"realtor_filter_beds_baths","city":city,"beds":beds,"baths":baths,"steps":steps}

def realtor_filter_property_type(_: dict) -> dict:
    city = random.choice(CITIES)
    prop_type = random.choice(PROPERTY_TYPES)
    steps = [
        "Go to url 'https://www.realtor.com'.",
        *_ui_hygiene(),
        "Ensure the 'Buy' tab is selected.",
        f"Type '{city}' in the location input and select from suggestions.",
        "Click 'Search'.",
        "Wait for results to load.",
        "Open the 'Property Type' filter.",
        f"Select '{prop_type}'.",
        "Apply the filter.",
        f"Assert all visible listings are of type '{prop_type}'.",
        "Assert at least 1 result is displayed.",
    ]
    return {"task_type":"realtor_filter_property_type","city":city,"property_type":prop_type,"steps":steps}

def realtor_sort_results(_: dict) -> dict:
    city = random.choice(CITIES)
    sort_option = random.choice(SORT_OPTIONS)
    steps = [
        "Go to url 'https://www.realtor.com'.",
        *_ui_hygiene(),
        "Ensure the 'Buy' tab is selected.",
        f"Type '{city}' in the location input and select from suggestions.",
        "Click 'Search'.",
        "Wait for results to load.",
        f"Open the 'Sort' dropdown and select '{sort_option}'.",
        "Wait for results to update.",
        f"Assert that the results are sorted by '{sort_option}'.",
        "Assert at least 1 result is displayed.",
    ]
    return {"task_type":"realtor_sort_results","city":city,"sort_option":sort_option,"steps":steps}

def realtor_view_listing_details(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = [
        "Go to url 'https://www.realtor.com'.",
        *_ui_hygiene(),
        "Ensure the 'Buy' tab is selected.",
        f"Type '{city}' in the location input and select from suggestions.",
        "Click 'Search'.",
        "Wait for results to load.",
        "Click the first listing in the results.",
        "Wait for the listing detail page to load.",
        "Assert that the address and price are visible on the detail page.",
        "Assert that the page URL contains '/realestateandhomes-detail/'.",
    ]
    return {"task_type":"realtor_view_listing_details","city":city,"steps":steps}

def realtor_contact_agent(_: dict) -> dict:
    city = random.choice(CITIES)
    fake_name = f"Test User {random.randint(1000,9999)}"
    fake_email = f"test{random.randint(1000,9999)}@example.com"
    fake_phone = f"555-01{random.randint(100,999)}"
    steps = [
        "Go to url 'https://www.realtor.com'.",
        *_ui_hygiene(),
        "Ensure the 'Buy' tab is selected.",
        f"Type '{city}' in the location input and select from suggestions.",
        "Click 'Search'.",
        "Wait for results to load.",
        "Click the first listing in the results.",
        "Wait for the listing detail page to load.",
        "Scroll to the 'Contact Agent' form.",
        f"Fill in name: '{fake_name}'.",
        f"Fill in email: '{fake_email}'.",
        f"Fill in phone: '{fake_phone}'.",
        "Attempt to submit the form.",
        "Assert that an error or captcha appears, or that a confirmation banner is shown.",
    ]
    return {"task_type":"realtor_contact_agent","city":city,"name":fake_name,"email":fake_email,"phone":fake_phone,"steps":steps}

def realtor_save_listing(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = [
        "Go to url 'https://www.realtor.com'.",
        *_ui_hygiene(),
        "Ensure the 'Buy' tab is selected.",
        f"Type '{city}' in the location input and select from suggestions.",
        "Click 'Search'.",
        "Wait for results to load.",
        "Click the first listing in the results.",
        "Wait for the listing detail page to load.",
        "Click the 'Save' or 'Favorite' button (heart icon).",
        "If prompted to sign in, assert that a login modal appears.",
        "If not prompted, assert that the listing is marked as saved (heart filled or similar).",
    ]
    return {"task_type":"realtor_save_listing","city":city,"steps":steps}

def realtor_mortgage_calculator(_: dict) -> dict:
    price = random.choice([p[1] for p in PRICE_RANGES])
    down_payment = random.choice([5,10,15,20,25,30])
    interest = random.choice([3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5,7.0,7.5,8.0,8.5,9.0,9.5,10.0])
    years = random.choice([15,20,25,30])
    steps = [
        "Go to url 'https://www.realtor.com/mortgage/tools/mortgage-calculator/'.",
        *_ui_hygiene(),
        f"Enter home price: ${price:,}.",
        f"Enter down payment: {down_payment}%.",
        f"Enter interest rate: {interest}%.",
        f"Set loan term to {years} years.",
        "Click 'Calculate' or equivalent.",
        "Assert that a monthly payment estimate is displayed.",
        "Assert that the payment value is greater than $0.",
    ]
    return {"task_type":"realtor_mortgage_calculator","price":price,"down_payment":down_payment,"interest":interest,"years":years,"steps":steps}

def realtor_school_info(_: dict) -> dict:
    city = random.choice(CITIES)
    school_type = random.choice(SCHOOL_TYPES)
    steps = [
        "Go to url 'https://www.realtor.com'.",
        *_ui_hygiene(),
        "Ensure the 'Buy' tab is selected.",
        f"Type '{city}' in the location input and select from suggestions.",
        "Click 'Search'.",
        "Wait for results to load.",
        "Open the 'Schools' map layer or tab.",
        f"Filter to show only '{school_type}' schools.",
        "Assert that at least 1 school of the selected type is displayed on the map or list.",
        "Click a school marker or name to view details.",
        "Assert that the school detail panel or page opens and shows school name and rating.",
    ]
    return {"task_type":"realtor_school_info","city":city,"school_type":school_type,"steps":steps}

def realtor_draw_map_area(_: dict) -> dict:
    city = random.choice(CITIES)
    area = random.choice(MAP_DRAW_AREAS)
    steps = [
        "Go to url 'https://www.realtor.com'.",
        *_ui_hygiene(),
        "Ensure the 'Buy' tab is selected.",
        f"Type '{city}' in the location input and select from suggestions.",
        "Click 'Search'.",
        "Wait for results to load.",
        "Switch to map view.",
        "Select the 'Draw' tool.",
        f"Draw a custom area around '{area}'.",
        "Apply the drawn area filter.",
        f"Assert that all visible listings are inside the drawn area labeled '{area}'.",
        "Assert at least 1 result is displayed.",
    ]
    return {"task_type":"realtor_draw_map_area","city":city,"area":area,"steps":steps}

_TASK_GENERATORS: Dict[REALTOR_TASK_TYPES, Callable[[dict], dict]] = {
    "realtor_home_search": realtor_home_search,
    "realtor_rent_search": realtor_rent_search,
    "realtor_filter_price": realtor_filter_price,
    "realtor_filter_beds_baths": realtor_filter_beds_baths,
    "realtor_filter_property_type": realtor_filter_property_type,
    "realtor_sort_results": realtor_sort_results,
    "realtor_view_listing_details": realtor_view_listing_details,
    "realtor_contact_agent": realtor_contact_agent,
    "realtor_save_listing": realtor_save_listing,
    "realtor_mortgage_calculator": realtor_mortgage_calculator,
    "realtor_school_info": realtor_school_info,
    "realtor_draw_map_area": realtor_draw_map_area,
}

def generate_realtor_task(task_type: REALTOR_TASK_TYPES, payload: dict) -> dict:
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
    items = list(REALTOR_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_realtor_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)