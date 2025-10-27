import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

LOOPNET_TASK_TYPES = Literal[
    "ln_search_property",
    "ln_filter_property_type",
    "ln_filter_price_range",
    "ln_filter_sqft_range",
    "ln_sort_results",
    "ln_view_property_details",
    "ln_save_property",
    "ln_contact_broker",
    "ln_signup_flow",
    "ln_help_center_topic",
]

LOOPNET_SAMPLING_CONFIG: Dict[LOOPNET_TASK_TYPES, int] = {
    "ln_search_property": 10,
    "ln_filter_property_type": 10,
    "ln_filter_price_range": 10,
    "ln_filter_sqft_range": 10,
    "ln_sort_results": 10,
    "ln_view_property_details": 10,
    "ln_save_property": 10,
    "ln_contact_broker": 10,
    "ln_signup_flow": 10,
    "ln_help_center_topic": 10,
}

LN_CITIES = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
    "Boston, MA", "Nashville, TN", "El Paso, TX", "Detroit, MI", "Oklahoma City, OK"
]

LN_PROPERTY_TYPES = [
    "Office", "Retail", "Industrial", "Multi-Family", "Land", "Hospitality",
    "Special Purpose", "Healthcare", "Sports & Entertainment", "Self Storage",
    "Flex", "Restaurant", "Shopping Center", "Warehouse", "Distribution",
    "Medical Office", "Car Wash", "Gas Station", "Bank", "Day Care", "School",
    "Church", "Data Center", "Truck Terminal", "Cold Storage"
]

LN_PRICE_RANGES = [
    "$100,000 - $250,000", "$250,000 - $500,000", "$500,000 - $750,000", "$750,000 - $1,000,000",
    "$1,000,000 - $2,000,000", "$2,000,000 - $3,000,000", "$3,000,000 - $5,000,000", "$5,000,000 - $7,500,000",
    "$7,500,000 - $10,000,000", "$10,000,000 - $15,000,000", "$15,000,000 - $20,000,000", "$20,000,000+",
    "$0 - $100,000", "$50,000 - $150,000", "$150,000 - $300,000", "$300,000 - $600,000",
    "$600,000 - $900,000", "$900,000 - $1,200,000", "$1,200,000 - $2,500,000", "$2,500,000 - $4,000,000"
]

LN_SQFT_RANGES = [
    "Under 1,000 SF", "1,000 - 2,500 SF", "2,500 - 5,000 SF", "5,000 - 10,000 SF",
    "10,000 - 20,000 SF", "20,000 - 50,000 SF", "50,000 - 100,000 SF", "100,000 - 250,000 SF",
    "250,000 - 500,000 SF", "500,000+ SF", "0 - 500 SF", "500 - 1,500 SF", "1,500 - 3,000 SF",
    "3,000 - 6,000 SF", "6,000 - 12,000 SF", "12,000 - 25,000 SF", "25,000 - 50,000 SF",
    "50,000 - 75,000 SF", "75,000 - 150,000 SF", "150,000+ SF"
]

LN_SORT_OPTIONS = [
    "Newest", "Price (Low to High)", "Price (High to Low)", "Size (Smallest)", "Size (Largest)",
    "Cap Rate (High to Low)", "Cap Rate (Low to High)", "Date Added (Newest)", "Date Added (Oldest)",
    "Distance (Closest)", "Distance (Farthest)", "Rent (Low to High)", "Rent (High to Low)",
    "Building Age (Newest)", "Building Age (Oldest)", "Lot Size (Largest)", "Lot Size (Smallest)",
    "Occupancy (High to Low)", "Occupancy (Low to High)", "Listing Status (Active)", "Listing Status (Pending)"
]

LN_SEARCH_TERMS = [
    "warehouse", "medical office", "retail space", "restaurant", "flex space", "shopping center",
    "self storage", "industrial", "distribution", "office building", "land for sale", "multifamily",
    "hotel", "gas station", "bank branch", "day care", "church", "data center", "truck terminal",
    "cold storage", "car wash", "school", "sports complex", "entertainment venue", "healthcare"
]

LN_FAQ_TOPICS = [
    ("Account Management", "account-management"),
    ("Searching Properties", "search-properties"),
    ("Saving Listings", "saving-listings"),
    ("Contacting Brokers", "contacting-brokers"),
    ("Site Features", "site-features"),
    ("Privacy & Security", "privacy-security"),
    ("Subscription Plans", "subscription-plans"),
    ("Mobile App", "mobile-app"),
    ("Listing Your Property", "listing-property"),
    ("Lead Management", "lead-management"),
    ("Alerts & Notifications", "alerts-notifications"),
    ("Favorites", "favorites"),
    ("Saved Searches", "saved-searches"),
    ("Map Search", "map-search"),
    ("Photo Uploads", "photo-uploads"),
    ("User Verification", "user-verification"),
    ("Password Reset", "password-reset"),
    ("Broker Directory", "broker-directory"),
    ("Report Listing", "report-listing"),
    ("Help Center Overview", "help-center-overview"),
    ("Accessibility", "accessibility"),
    ("Contact Support", "contact-support"),
    ("Terms of Use", "terms-of-use"),
    ("Cookie Policy", "cookie-policy"),
    ("Advertising", "advertising")
]

def _rand_date(start_days=1, end_days=40) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, newsletter, location prompt).",
        "Do not attempt to sign in or purchase; only use public features.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("LoopNet", steps).model_dump()

def ln_search_property(_: dict) -> dict:
    city = random.choice(LN_CITIES)
    term = random.choice(LN_SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.loopnet.com/'.",
        *_ui_hygiene(),
        "Ensure the main search bar is visible.",
        f"Type '{term}' in the search bar.",
        f"Set location to '{city}'.",
        "Submit the search.",
        "Wait for results to load.",
        f"Assert that at least one result for '{term}' in '{city}' is displayed.",
    ]
    return {
        "task_type": "ln_search_property",
        "city": city,
        "search_term": term,
        "steps": steps
    }

def ln_filter_property_type(_: dict) -> dict:
    city = random.choice(LN_CITIES)
    prop_type = random.choice(LN_PROPERTY_TYPES)
    steps = [
        "Go to url 'https://www.loopnet.com/'.",
        *_ui_hygiene(),
        "Ensure the main search bar is visible.",
        f"Set location to '{city}'.",
        "Submit the search.",
        "Wait for results to load.",
        "Open the 'Property Type' filter.",
        f"Select '{prop_type}' as the property type.",
        "Apply the filter.",
        f"Assert that all results are of type '{prop_type}'."
    ]
    return {
        "task_type": "ln_filter_property_type",
        "city": city,
        "property_type": prop_type,
        "steps": steps
    }

def ln_filter_price_range(_: dict) -> dict:
    city = random.choice(LN_CITIES)
    price_range = random.choice(LN_PRICE_RANGES)
    steps = [
        "Go to url 'https://www.loopnet.com/'.",
        *_ui_hygiene(),
        "Ensure the main search bar is visible.",
        f"Set location to '{city}'.",
        "Submit the search.",
        "Wait for results to load.",
        "Open the 'Price' filter.",
        f"Set price range to '{price_range}'.",
        "Apply the filter.",
        f"Assert that all results have asking prices within '{price_range}'."
    ]
    return {
        "task_type": "ln_filter_price_range",
        "city": city,
        "price_range": price_range,
        "steps": steps
    }

def ln_filter_sqft_range(_: dict) -> dict:
    city = random.choice(LN_CITIES)
    sqft_range = random.choice(LN_SQFT_RANGES)
    steps = [
        "Go to url 'https://www.loopnet.com/'.",
        *_ui_hygiene(),
        "Ensure the main search bar is visible.",
        f"Set location to '{city}'.",
        "Submit the search.",
        "Wait for results to load.",
        "Open the 'Square Footage' filter.",
        f"Set square footage range to '{sqft_range}'.",
        "Apply the filter.",
        f"Assert that all results have square footage within '{sqft_range}'."
    ]
    return {
        "task_type": "ln_filter_sqft_range",
        "city": city,
        "sqft_range": sqft_range,
        "steps": steps
    }

def ln_sort_results(_: dict) -> dict:
    city = random.choice(LN_CITIES)
    sort_option = random.choice(LN_SORT_OPTIONS)
    steps = [
        "Go to url 'https://www.loopnet.com/'.",
        *_ui_hygiene(),
        "Ensure the main search bar is visible.",
        f"Set location to '{city}'.",
        "Submit the search.",
        "Wait for results to load.",
        "Open the 'Sort By' dropdown.",
        f"Select '{sort_option}' as the sort option.",
        "Wait for results to update.",
        f"Assert that the first page of results is sorted by '{sort_option}'."
    ]
    return {
        "task_type": "ln_sort_results",
        "city": city,
        "sort_option": sort_option,
        "steps": steps
    }

def ln_view_property_details(_: dict) -> dict:
    city = random.choice(LN_CITIES)
    steps = [
        "Go to url 'https://www.loopnet.com/'.",
        *_ui_hygiene(),
        "Ensure the main search bar is visible.",
        f"Set location to '{city}'.",
        "Submit the search.",
        "Wait for results to load.",
        "Click on the first property in the results.",
        "Wait for the property details page to load.",
        "Assert that the property details page contains address, price, and broker contact info."
    ]
    return {
        "task_type": "ln_view_property_details",
        "city": city,
        "steps": steps
    }

def ln_save_property(_: dict) -> dict:
    city = random.choice(LN_CITIES)
    steps = [
        "Go to url 'https://www.loopnet.com/'.",
        *_ui_hygiene(),
        "Ensure the main search bar is visible.",
        f"Set location to '{city}'.",
        "Submit the search.",
        "Wait for results to load.",
        "Click on the first property in the results.",
        "Wait for the property details page to load.",
        "Click the 'Save' or 'Favorite' button (should prompt for signup or login).",
        "Assert that a signup or login modal appears."
    ]
    return {
        "task_type": "ln_save_property",
        "city": city,
        "steps": steps
    }

def ln_contact_broker(_: dict) -> dict:
    city = random.choice(LN_CITIES)
    steps = [
        "Go to url 'https://www.loopnet.com/'.",
        *_ui_hygiene(),
        "Ensure the main search bar is visible.",
        f"Set location to '{city}'.",
        "Submit the search.",
        "Wait for results to load.",
        "Click on the first property in the results.",
        "Wait for the property details page to load.",
        "Locate the 'Contact Broker' or 'Request Info' button.",
        "Click the button.",
        "Assert that a contact form or modal appears (do not submit)."
    ]
    return {
        "task_type": "ln_contact_broker",
        "city": city,
        "steps": steps
    }

def ln_signup_flow(_: dict) -> dict:
    email = f"testuser{random.randint(10000,99999)}@example.com"
    steps = [
        "Go to url 'https://www.loopnet.com/'.",
        *_ui_hygiene(),
        "Click 'Sign Up' or 'Register' at the top right.",
        "Wait for the signup form to appear.",
        f"Enter email address '{email}'.",
        "Enter a valid password (e.g., 'Test1234!').",
        "Fill in required fields (first name, last name).",
        "Do not submit the form.",
        "Assert that the 'Sign Up' button is enabled and no error messages are shown."
    ]
    return {
        "task_type": "ln_signup_flow",
        "email": email,
        "steps": steps
    }

def ln_help_center_topic(_: dict) -> dict:
    topic, slug = random.choice(LN_FAQ_TOPICS)
    steps = [
        "Go to url 'https://www.loopnet.com/help/'.",
        *_ui_hygiene(),
        f"Find and open the '{topic}' help topic.",
        "Summarize the first two key points or FAQs listed.",
        "Assert that the help content for the topic is visible."
    ]
    return {
        "task_type": "ln_help_center_topic",
        "help_topic": topic,
        "steps": steps
    }

_TASK_GENERATORS: Dict[LOOPNET_TASK_TYPES, Callable[[dict], dict]] = {
    "ln_search_property": ln_search_property,
    "ln_filter_property_type": ln_filter_property_type,
    "ln_filter_price_range": ln_filter_price_range,
    "ln_filter_sqft_range": ln_filter_sqft_range,
    "ln_sort_results": ln_sort_results,
    "ln_view_property_details": ln_view_property_details,
    "ln_save_property": ln_save_property,
    "ln_contact_broker": ln_contact_broker,
    "ln_signup_flow": ln_signup_flow,
    "ln_help_center_topic": ln_help_center_topic,
}

def generate_ln_task(task_type: LOOPNET_TASK_TYPES, payload: dict) -> dict:
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
    items = list(LOOPNET_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_ln_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)