import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

HOMES_TASK_TYPES = Literal[
    "homes_search_city",
    "homes_filter_price_range",
    "homes_filter_bedrooms",
    "homes_sort_newest",
    "homes_view_property_details",
    "homes_save_property_guest",
    "homes_contact_agent_guest",
    "homes_search_keyword",
    "homes_filter_property_type",
    "homes_filter_days_on_homes",
    "homes_filter_amenities",
    "homes_view_map_results",
    "homes_navigate_back_forward",
    "homes_signup_flow",
]

HOMES_SAMPLING_CONFIG: Dict[HOMES_TASK_TYPES, int] = {
    "homes_search_city": 10,
    "homes_filter_price_range": 10,
    "homes_filter_bedrooms": 10,
    "homes_sort_newest": 10,
    "homes_view_property_details": 10,
    "homes_save_property_guest": 10,
    "homes_contact_agent_guest": 10,
    "homes_search_keyword": 10,
    "homes_filter_property_type": 10,
    "homes_filter_days_on_homes": 10,
    "homes_filter_amenities": 10,
    "homes_view_map_results": 10,
    "homes_navigate_back_forward": 10,
    "homes_signup_flow": 10,
}

CITIES = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
    "Boston, MA", "Nashville, TN", "El Paso, TX", "Detroit, MI", "Portland, OR"
]

PRICE_RANGES = [
    (50000, 100000), (100000, 150000), (150000, 200000), (200000, 250000), (250000, 300000),
    (300000, 350000), (350000, 400000), (400000, 450000), (450000, 500000), (500000, 600000),
    (600000, 700000), (700000, 800000), (800000, 900000), (900000, 1000000), (1000000, 1200000),
    (1200000, 1400000), (1400000, 1600000), (1600000, 1800000), (1800000, 2000000), (2000000, 2500000),
    (2500000, 3000000), (3000000, 4000000), (4000000, 5000000)
]

BEDROOMS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "Studio", "Loft", "Penthouse", "Townhouse", "Duplex", "Triplex", "Quadruplex", "Condo", "Apartment", "House"]

PROPERTY_TYPES = [
    "Single Family", "Condo", "Townhouse", "Multi-Family", "Apartment", "Mobile Home",
    "Land", "Farm", "Co-op", "Loft", "Duplex", "Triplex", "Quadruplex", "Manufactured",
    "Cottage", "Bungalow", "Ranch", "Villa", "Cabin", "Penthouse", "Rowhouse", "Carriage House"
]

DAYS_ON_HOMES = [
    "Any", "1 day", "3 days", "7 days", "14 days", "21 days", "30 days", "45 days", "60 days",
    "90 days", "120 days", "180 days", "365 days", "2 years", "3 years", "5 years", "10 years", "15 years", "20 years", "25 years"
]

AMENITIES = [
    "Pool", "Garage", "Fireplace", "Basement", "Central Air", "Hardwood Floors", "Fenced Yard",
    "Deck", "Patio", "Walk-In Closet", "Laundry Room", "Finished Basement", "Attic", "Garden",
    "Elevator", "Doorman", "Gym", "Storage", "Balcony", "View", "Solar Panels", "Smart Home"
]

KEYWORDS = [
    "waterfront", "downtown", "gated", "historic", "renovated", "fixer", "luxury", "investment",
    "starter", "cul-de-sac", "corner lot", "open floor plan", "move-in ready", "new construction",
    "pet friendly", "walkable", "school district", "shopping", "public transit", "quiet", "views",
    "high-rise", "loft", "garden", "studio"
]

MAP_ZOOM_CITIES = [
    "Seattle, WA", "Miami, FL", "Atlanta, GA", "Dallas, TX", "San Francisco, CA",
    "Denver, CO", "Chicago, IL", "Boston, MA", "Portland, OR", "Phoenix, AZ",
    "Houston, TX", "San Diego, CA", "Washington, DC", "Charlotte, NC", "Austin, TX",
    "Las Vegas, NV", "Minneapolis, MN", "Tampa, FL", "Orlando, FL", "Baltimore, MD"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, cookie banners, or newsletter modals.",
        "Do not sign in or create an account unless the task requires it.",
        "Do not attempt to purchase or apply for anything.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Homes.com", steps).model_dump()

def _rand_email() -> str:
    return f"testuser{random.randint(10000,99999)}@example.com"

def _rand_phone() -> str:
    return f"555-{random.randint(100,999)}-{random.randint(1000,9999)}"

def _rand_name() -> str:
    first = random.choice(["Alex","Sam","Jordan","Taylor","Morgan","Casey","Jamie","Riley","Chris","Avery","Skyler","Drew","Cameron","Jesse","Harper","Reese","Blake","Quinn","Rowan","Parker"])
    last = random.choice(["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Moore","Martin","Lee","Perez","Clark","Lewis"])
    return f"{first} {last}"

def _rand_city() -> str:
    return random.choice(CITIES)

def _rand_price_range() -> tuple:
    return random.choice(PRICE_RANGES)

def _rand_bedrooms() -> str:
    return str(random.choice(BEDROOMS))

def _rand_property_type() -> str:
    return random.choice(PROPERTY_TYPES)

def _rand_days_on_homes() -> str:
    return random.choice(DAYS_ON_HOMES)

def _rand_amenities(n=2) -> list:
    return random.sample(AMENITIES, n)

def _rand_keyword() -> str:
    return random.choice(KEYWORDS)

def _rand_map_city() -> str:
    return random.choice(MAP_ZOOM_CITIES)

def homes_search_city(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        f"Assert the results page shows listings for '{city}'.",
        "Assert at least 1 property card is visible.",
    ]
    return {"task_type":"homes_search_city","city":city,"steps":steps}

def homes_filter_price_range(_: dict) -> dict:
    city = _rand_city()
    min_price, max_price = _rand_price_range()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Open the price filter dropdown.",
        f"Set minimum price to ${min_price:,}.",
        f"Set maximum price to ${max_price:,}.",
        "Apply the price filter.",
        f"Assert all visible listings have price between ${min_price:,} and ${max_price:,}.",
        "Assert at least 1 property card is visible.",
    ]
    return {"task_type":"homes_filter_price_range","city":city,"min_price":min_price,"max_price":max_price,"steps":steps}

def homes_filter_bedrooms(_: dict) -> dict:
    city = _rand_city()
    bedrooms = _rand_bedrooms()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Open the bedrooms filter dropdown.",
        f"Select '{bedrooms}' bedrooms.",
        "Apply the bedrooms filter.",
        f"Assert all visible listings show '{bedrooms}' bedrooms or more.",
        "Assert at least 1 property card is visible.",
    ]
    return {"task_type":"homes_filter_bedrooms","city":city,"bedrooms":bedrooms,"steps":steps}

def homes_sort_newest(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Open the sort dropdown.",
        "Select 'Newest' or 'Recently Listed'.",
        "Assert the first listing shows a recent listing date (e.g., 'Just Listed', '1 day ago').",
        "Assert at least 1 property card is visible.",
    ]
    return {"task_type":"homes_sort_newest","city":city,"steps":steps}

def homes_view_property_details(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Click the first property card.",
        "Assert the property details page loads.",
        "Assert the address, price, and at least 3 photos are visible.",
        "Assert a 'Contact Agent' button is present.",
    ]
    return {"task_type":"homes_view_property_details","city":city,"steps":steps}

def homes_save_property_guest(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Click the heart/save icon on the first property card.",
        "If prompted to sign in, cancel or close the modal.",
        "Assert the property is not added to saved list (since not signed in).",
        "Assert a sign-in prompt or tooltip is shown.",
    ]
    return {"task_type":"homes_save_property_guest","city":city,"steps":steps}

def homes_contact_agent_guest(_: dict) -> dict:
    city = _rand_city()
    name = _rand_name()
    email = _rand_email()
    phone = _rand_phone()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Click the first property card.",
        "Wait for property details page to load.",
        "Scroll to the 'Contact Agent' or inquiry form.",
        f"Fill in name: '{name}'.",
        f"Fill in email: '{email}'.",
        f"Fill in phone: '{phone}'.",
        "Type a short message: 'I am interested in this property.'",
        "Submit the form.",
        "Assert a confirmation banner or message appears (e.g., 'Message sent', 'Thank you').",
        "Assert no sign-in or payment is required.",
    ]
    return {"task_type":"homes_contact_agent_guest","city":city,"name":name,"email":email,"phone":phone,"steps":steps}

def homes_search_keyword(_: dict) -> dict:
    city = _rand_city()
    keyword = _rand_keyword()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Open the keyword filter or advanced search.",
        f"Enter keyword: '{keyword}'.",
        "Apply the keyword filter.",
        f"Assert at least 1 visible listing contains '{keyword}' in the description or features.",
    ]
    return {"task_type":"homes_search_keyword","city":city,"keyword":keyword,"steps":steps}

def homes_filter_property_type(_: dict) -> dict:
    city = _rand_city()
    prop_type = _rand_property_type()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Open the property type filter dropdown.",
        f"Select '{prop_type}'.",
        "Apply the property type filter.",
        f"Assert all visible listings are of type '{prop_type}'.",
        "Assert at least 1 property card is visible.",
    ]
    return {"task_type":"homes_filter_property_type","city":city,"property_type":prop_type,"steps":steps}

def homes_filter_days_on_homes(_: dict) -> dict:
    city = _rand_city()
    days = _rand_days_on_homes()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Open the 'Days on Homes.com' filter dropdown.",
        f"Select '{days}'.",
        "Apply the filter.",
        f"Assert all visible listings have been on Homes.com for '{days}' or less.",
        "Assert at least 1 property card is visible.",
    ]
    return {"task_type":"homes_filter_days_on_homes","city":city,"days_on_homes":days,"steps":steps}

def homes_filter_amenities(_: dict) -> dict:
    city = _rand_city()
    amenities = _rand_amenities(2)
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Open the amenities filter or advanced search.",
        f"Select amenities: {', '.join(amenities)}.",
        "Apply the amenities filter.",
        f"Assert all visible listings include both '{amenities[0]}' and '{amenities[1]}'.",
        "Assert at least 1 property card is visible.",
    ]
    return {"task_type":"homes_filter_amenities","city":city,"amenities":amenities,"steps":steps}

def homes_view_map_results(_: dict) -> dict:
    city = _rand_map_city()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Switch to map view.",
        "Zoom in and pan the map to view at least 10 property pins.",
        "Click on a map pin.",
        "Assert a property preview or card appears for the selected pin.",
        "Assert the map and list remain in sync.",
    ]
    return {"task_type":"homes_view_map_results","city":city,"steps":steps}

def homes_navigate_back_forward(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Focus the main search box.",
        f"Type '{city}' and select the autocomplete suggestion.",
        "Click the search button.",
        "Wait for results to load.",
        "Click the first property card.",
        "Wait for property details page to load.",
        "Use the browser back button to return to the search results.",
        "Assert the search results page is shown and scroll position is preserved.",
        "Use the browser forward button to return to the property details page.",
        "Assert the property details page reloads correctly.",
    ]
    return {"task_type":"homes_navigate_back_forward","city":city,"steps":steps}

def homes_signup_flow(_: dict) -> dict:
    name = _rand_name()
    email = _rand_email()
    steps = [
        "Go to url 'https://www.homes.com/'.",
        *_ui_hygiene(),
        "Click the 'Sign Up' or 'Register' button in the header.",
        "Wait for the registration form to appear.",
        f"Enter name: '{name}'.",
        f"Enter email: '{email}'.",
        "Enter password: 'TestPassword123!'.",
        "Accept terms and conditions.",
        "Submit the registration form.",
        "Assert a confirmation message or welcome banner appears.",
        "Assert user is now signed in (e.g., user avatar or name in header).",
        "Do not proceed with any payment or purchase.",
    ]
    return {"task_type":"homes_signup_flow","name":name,"email":email,"steps":steps}

_TASK_GENERATORS: Dict[HOMES_TASK_TYPES, Callable[[dict], dict]] = {
    "homes_search_city": homes_search_city,
    "homes_filter_price_range": homes_filter_price_range,
    "homes_filter_bedrooms": homes_filter_bedrooms,
    "homes_sort_newest": homes_sort_newest,
    "homes_view_property_details": homes_view_property_details,
    "homes_save_property_guest": homes_save_property_guest,
    "homes_contact_agent_guest": homes_contact_agent_guest,
    "homes_search_keyword": homes_search_keyword,
    "homes_filter_property_type": homes_filter_property_type,
    "homes_filter_days_on_homes": homes_filter_days_on_homes,
    "homes_filter_amenities": homes_filter_amenities,
    "homes_view_map_results": homes_view_map_results,
    "homes_navigate_back_forward": homes_navigate_back_forward,
    "homes_signup_flow": homes_signup_flow,
}

def generate_homes_task(task_type: HOMES_TASK_TYPES, payload: dict) -> dict:
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
    items = list(HOMES_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_homes_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)