import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

MOVOTO_TASK_TYPES = Literal[
    "movoto_home_search",
    "movoto_filter_price_range",
    "movoto_filter_beds_baths",
    "movoto_sort_results",
    "movoto_property_details",
    "movoto_save_search",
    "movoto_signup_flow",
    "movoto_contact_agent",
    "movoto_school_info",
    "movoto_map_draw_search",
    "movoto_open_house_filter",
    "movoto_recently_sold_search",
    "movoto_property_compare",
    "movoto_neighborhood_explore",
    "movoto_mortgage_calculator",
]

MOVOTO_SAMPLING_CONFIG: Dict[MOVOTO_TASK_TYPES, int] = {
    "movoto_home_search": 10,
    "movoto_filter_price_range": 10,
    "movoto_filter_beds_baths": 10,
    "movoto_sort_results": 10,
    "movoto_property_details": 10,
    "movoto_save_search": 10,
    "movoto_signup_flow": 10,
    "movoto_contact_agent": 10,
    "movoto_school_info": 10,
    "movoto_map_draw_search": 10,
    "movoto_open_house_filter": 10,
    "movoto_recently_sold_search": 10,
    "movoto_property_compare": 10,
    "movoto_neighborhood_explore": 10,
    "movoto_mortgage_calculator": 10,
}

CITIES = [
    "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ", "Philadelphia, PA",
    "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA", "Austin, TX",
    "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC", "San Francisco, CA",
    "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC", "Boston, MA",
    "Nashville, TN", "El Paso, TX", "Detroit, MI", "Oklahoma City, OK", "Portland, OR"
]

ZIP_CODES = [
    "90001", "60601", "77001", "85001", "19104", "78201", "92101", "75201", "95101", "78701",
    "32201", "76101", "43201", "28202", "94102", "46201", "98101", "80201", "20001", "02108",
    "37201", "79901", "48201", "73101", "97201"
]

PRICE_RANGES = [
    (100000, 200000), (200000, 300000), (300000, 400000), (400000, 500000), (500000, 600000),
    (600000, 700000), (700000, 800000), (800000, 900000), (900000, 1000000), (1000000, 1200000),
    (1200000, 1400000), (1400000, 1600000), (1600000, 1800000), (1800000, 2000000),
    (2000000, 2500000), (2500000, 3000000), (3000000, 3500000), (3500000, 4000000),
    (4000000, 4500000), (4500000, 5000000), (5000000, 6000000), (6000000, 7000000)
]

BEDS = [1, 2, 3, 4, 5, 6, 7, 8]
BATHS = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
SORT_ORDERS = [
    "Newest", "Price (Low to High)", "Price (High to Low)", "Beds (Most)", "Beds (Least)",
    "Baths (Most)", "Baths (Least)", "Sqft (Most)", "Sqft (Least)", "Open Houses", "Recently Sold",
    "Days on Movoto", "Year Built (Newest)", "Year Built (Oldest)", "Lot Size (Largest)",
    "Lot Size (Smallest)", "HOA Fees (Lowest)", "HOA Fees (Highest)", "Price Reduced", "Pending"
]
PROPERTY_TYPES = [
    "Single Family", "Condo", "Townhouse", "Multi-Family", "Land", "Mobile Home", "Co-op",
    "Apartment", "Loft", "Duplex", "Triplex", "Quadruplex", "Farm", "Manufactured", "Cottage",
    "Bungalow", "Ranch", "Victorian", "Colonial", "Cape Cod", "Contemporary", "Modern"
]
SCHOOL_LEVELS = [
    "Elementary", "Middle", "High", "Preschool", "Private", "Charter", "Magnet", "Public",
    "Alternative", "Vocational", "Special Education", "Online", "Montessori", "International",
    "Boarding", "Religious", "STEM", "Arts", "Language Immersion", "Gifted"
]
NEIGHBORHOODS = [
    "Downtown", "Uptown", "Midtown", "Chinatown", "Little Italy", "SoHo", "Harlem", "Hollywood",
    "Mission District", "Nob Hill", "South End", "Back Bay", "Ballard", "Capitol Hill", "Beverly Hills",
    "Brooklyn Heights", "Greenwich Village", "Silver Lake", "Wicker Park", "The Loop", "Queen Anne"
]
MORTGAGE_AMOUNTS = [
    150000, 200000, 250000, 300000, 350000, 400000, 450000, 500000, 550000, 600000,
    650000, 700000, 750000, 800000, 850000, 900000, 950000, 1000000, 1100000, 1200000, 1300000
]
INTEREST_RATES = [
    2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75, 5.0, 5.25, 5.5, 5.75, 6.0, 6.25, 6.5, 6.75, 7.0, 7.25, 7.5
]
DOWN_PAYMENTS = [
    5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100
]
YEARS = [15, 20, 25, 30]
EMAILS = [f"testuser{i}@example.com" for i in range(1, 25)]
NAMES = [f"Test User{i}" for i in range(1, 25)]
PHONE_NUMBERS = [f"555-01{str(i).zfill(2)}" for i in range(1, 25)]
DRAW_SHAPES = [
    "Rectangle", "Circle", "Polygon", "Freehand", "Lasso", "Ellipse", "Square", "Triangle", "Diamond",
    "Pentagon", "Hexagon", "Octagon", "Star", "Arrow", "Heart", "Cross", "Line", "Curve", "Wave", "Spiral"
]
OPEN_HOUSE_DAYS = [
    "This Weekend", "Today", "Next 7 Days", "Next 14 Days", "Next 30 Days", "Anytime", "Saturday", "Sunday",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Morning", "Afternoon", "Evening", "Open Now",
    "Virtual Only", "By Appointment", "Public", "Private"
]
COMPARE_COUNT = [2, 3, 4, 5]
RECENTLY_SOLD_RANGES = [
    "Last 7 Days", "Last 14 Days", "Last 30 Days", "Last 60 Days", "Last 90 Days", "Last 6 Months",
    "Last 12 Months", "Year to Date", "Last 2 Years", "Last 3 Years", "Last 5 Years", "Custom Date Range",
    "This Month", "Last Month", "This Year", "Last Year", "Past Weekend", "Past Week", "Past Quarter", "Past Half Year"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, newsletter signup, location prompts).",
        "Do not attempt to log in, purchase, or submit personal information unless the task specifies.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Movoto", steps).model_dump()

def _rand_city():
    return random.choice(CITIES)

def _rand_zip():
    return random.choice(ZIP_CODES)

def _rand_price_range():
    return random.choice(PRICE_RANGES)

def _rand_beds():
    return random.choice(BEDS)

def _rand_baths():
    return random.choice(BATHS)

def _rand_sort():
    return random.choice(SORT_ORDERS)

def _rand_property_type():
    return random.choice(PROPERTY_TYPES)

def _rand_school_level():
    return random.choice(SCHOOL_LEVELS)

def _rand_neighborhood():
    return random.choice(NEIGHBORHOODS)

def _rand_mortgage_amount():
    return random.choice(MORTGAGE_AMOUNTS)

def _rand_interest_rate():
    return random.choice(INTEREST_RATES)

def _rand_down_payment():
    return random.choice(DOWN_PAYMENTS)

def _rand_years():
    return random.choice(YEARS)

def _rand_email():
    return random.choice(EMAILS)

def _rand_name():
    return random.choice(NAMES)

def _rand_phone():
    return random.choice(PHONE_NUMBERS)

def _rand_draw_shape():
    return random.choice(DRAW_SHAPES)

def _rand_open_house_day():
    return random.choice(OPEN_HOUSE_DAYS)

def _rand_compare_count():
    return random.choice(COMPARE_COUNT)

def _rand_recently_sold_range():
    return random.choice(RECENTLY_SOLD_RANGES)

def movoto_home_search(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Locate the main search bar.",
        f"Type '{city}' and select it from the autocomplete suggestions.",
        "Click the search button.",
        f"Assert that the results page loads and the location header contains '{city.split(',')[0]}'.",
        "Verify at least one property card is visible.",
    ]
    return {
        "task_type": "movoto_home_search",
        "city": city,
        "steps": steps,
        "assertion": f"Results page shows listings for '{city}'."
    }

def movoto_filter_price_range(_: dict) -> dict:
    city = _rand_city()
    price_min, price_max = _rand_price_range()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        "Locate the price range filter.",
        f"Set minimum price to ${price_min:,} and maximum price to ${price_max:,}.",
        "Apply the filter.",
        f"Assert that all visible property cards have prices between ${price_min:,} and ${price_max:,}.",
        "If no results, verify the page displays a 'No Results' or similar message.",
    ]
    return {
        "task_type": "movoto_filter_price_range",
        "city": city,
        "price_min": price_min,
        "price_max": price_max,
        "steps": steps,
        "assertion": f"All results are between ${price_min:,} and ${price_max:,}."
    }

def movoto_filter_beds_baths(_: dict) -> dict:
    city = _rand_city()
    beds = _rand_beds()
    baths = _rand_baths()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        "Locate the beds and baths filter.",
        f"Set beds to {beds}+ and baths to {baths}+.",
        "Apply the filter.",
        f"Assert that all visible property cards show at least {beds} beds and {baths} baths.",
        "If no results, verify the page displays a 'No Results' or similar message.",
    ]
    return {
        "task_type": "movoto_filter_beds_baths",
        "city": city,
        "beds": beds,
        "baths": baths,
        "steps": steps,
        "assertion": f"All results have at least {beds} beds and {baths} baths."
    }

def movoto_sort_results(_: dict) -> dict:
    city = _rand_city()
    sort_order = _rand_sort()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        "Locate the sort dropdown.",
        f"Select '{sort_order}' from the sort options.",
        "Wait for the results to update.",
        f"Assert that the results are sorted by '{sort_order}'.",
    ]
    return {
        "task_type": "movoto_sort_results",
        "city": city,
        "sort_order": sort_order,
        "steps": steps,
        "assertion": f"Results are sorted by '{sort_order}'."
    }

def movoto_property_details(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        "Click on the first property card.",
        "Wait for the property details page to load.",
        "Assert that the address, price, beds, baths, and property type are visible.",
        "Assert that there is a photo gallery or main image.",
        "Assert that there is a map or location section.",
    ]
    return {
        "task_type": "movoto_property_details",
        "city": city,
        "steps": steps,
        "assertion": "Property details page displays all key fields."
    }

def movoto_save_search(_: dict) -> dict:
    city = _rand_city()
    email = _rand_email()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        "Locate and click the 'Save Search' or 'Get Alerts' button.",
        f"Enter email address '{email}' in the prompt.",
        "Submit the form.",
        "Assert that a confirmation message appears (e.g., 'Search saved', 'You will receive alerts').",
        "Do not verify email receipt.",
    ]
    return {
        "task_type": "movoto_save_search",
        "city": city,
        "email": email,
        "steps": steps,
        "assertion": "Confirmation message for saved search is shown."
    }

def movoto_signup_flow(_: dict) -> dict:
    name = _rand_name()
    email = _rand_email()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        "Click on 'Sign Up' or 'Register' in the header.",
        f"Enter name '{name}' and email '{email}'.",
        "Choose a password (do not use a real one).",
        "Submit the form.",
        "Assert that a welcome message or 'account created' confirmation appears.",
        "Do not proceed with email verification.",
    ]
    return {
        "task_type": "movoto_signup_flow",
        "name": name,
        "email": email,
        "steps": steps,
        "assertion": "Signup confirmation or welcome message is shown."
    }

def movoto_contact_agent(_: dict) -> dict:
    city = _rand_city()
    name = _rand_name()
    email = _rand_email()
    phone = _rand_phone()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        "Click on the first property card.",
        "Wait for the property details page to load.",
        "Locate the 'Contact Agent' or 'Request Info' form.",
        f"Enter name '{name}', email '{email}', and phone '{phone}'.",
        "Enter a generic message (e.g., 'I am interested in this property.').",
        "Submit the form.",
        "Assert that a confirmation or thank you message appears.",
        "Do not expect a call or email.",
    ]
    return {
        "task_type": "movoto_contact_agent",
        "city": city,
        "name": name,
        "email": email,
        "phone": phone,
        "steps": steps,
        "assertion": "Confirmation message for agent contact is shown."
    }

def movoto_school_info(_: dict) -> dict:
    city = _rand_city()
    school_level = _rand_school_level()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        "Click on the first property card.",
        "Wait for the property details page to load.",
        "Locate the 'Schools' or 'Nearby Schools' section.",
        f"Filter or note schools of level '{school_level}'.",
        f"Assert that at least one school of type '{school_level}' is listed, or a 'No schools found' message is shown.",
    ]
    return {
        "task_type": "movoto_school_info",
        "city": city,
        "school_level": school_level,
        "steps": steps,
        "assertion": f"Schools section lists '{school_level}' or shows 'No schools found'."
    }

def movoto_map_draw_search(_: dict) -> dict:
    city = _rand_city()
    draw_shape = _rand_draw_shape()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        "Switch to map view.",
        f"Select the draw tool and draw a '{draw_shape}' area on the map.",
        "Wait for the results to update.",
        "Assert that only properties within the drawn area are shown.",
        "If no results, verify the page displays a 'No Results' or similar message.",
    ]
    return {
        "task_type": "movoto_map_draw_search",
        "city": city,
        "draw_shape": draw_shape,
        "steps": steps,
        "assertion": f"Results are limited to the '{draw_shape}' area."
    }

def movoto_open_house_filter(_: dict) -> dict:
    city = _rand_city()
    open_house_day = _rand_open_house_day()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        "Locate the 'Open House' filter.",
        f"Select '{open_house_day}' as the open house day.",
        "Apply the filter.",
        f"Assert that all visible property cards show an open house on '{open_house_day}', or a 'No Results' message is shown.",
    ]
    return {
        "task_type": "movoto_open_house_filter",
        "city": city,
        "open_house_day": open_house_day,
        "steps": steps,
        "assertion": f"All results have open house on '{open_house_day}' or show 'No Results'."
    }

def movoto_recently_sold_search(_: dict) -> dict:
    city = _rand_city()
    sold_range = _rand_recently_sold_range()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        "Locate the 'Recently Sold' or 'Sold' filter.",
        f"Select '{sold_range}' as the date range.",
        "Apply the filter.",
        f"Assert that all visible property cards show a sold date within '{sold_range}', or a 'No Results' message is shown.",
    ]
    return {
        "task_type": "movoto_recently_sold_search",
        "city": city,
        "sold_range": sold_range,
        "steps": steps,
        "assertion": f"All results sold within '{sold_range}' or show 'No Results'."
    }

def movoto_property_compare(_: dict) -> dict:
    city = _rand_city()
    count = _rand_compare_count()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        f"Select {count} different property cards using the 'Compare' or similar checkbox.",
        "Click the 'Compare' button.",
        "Assert that the comparison page loads and displays all selected properties side by side.",
        "Verify that address, price, beds, baths, and sqft are shown for each property.",
    ]
    return {
        "task_type": "movoto_property_compare",
        "city": city,
        "compare_count": count,
        "steps": steps,
        "assertion": f"Comparison page shows {count} properties with key fields."
    }

def movoto_neighborhood_explore(_: dict) -> dict:
    city = _rand_city()
    neighborhood = _rand_neighborhood()
    steps = [
        "Go to url 'https://www.movoto.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' and load the results page.",
        "Locate the neighborhoods or area filter.",
        f"Select '{neighborhood}' from the list.",
        "Apply the filter.",
        f"Assert that the results page header or filter shows '{neighborhood}'.",
        "Verify that all visible property cards are located in '{neighborhood}'.",
    ]
    return {
        "task_type": "movoto_neighborhood_explore",
        "city": city,
        "neighborhood": neighborhood,
        "steps": steps,
        "assertion": f"All results are in '{neighborhood}'."
    }

def movoto_mortgage_calculator(_: dict) -> dict:
    amount = _rand_mortgage_amount()
    rate = _rand_interest_rate()
    down = _rand_down_payment()
    years = _rand_years()
    steps = [
        "Go to url 'https://www.movoto.com/mortgage-calculator/'.",
        *_ui_hygiene(),
        f"Enter home price: ${amount:,}.",
        f"Enter down payment: {down}%.",
        f"Enter interest rate: {rate}%.",
        f"Set loan term to {years} years.",
        "Click 'Calculate' or equivalent.",
        "Assert that a monthly payment amount is displayed.",
        "Verify that the breakdown includes principal, interest, taxes, and insurance.",
    ]
    return {
        "task_type": "movoto_mortgage_calculator",
        "amount": amount,
        "down_payment": down,
        "interest_rate": rate,
        "years": years,
        "steps": steps,
        "assertion": "Monthly payment and breakdown are shown."
    }

_TASK_GENERATORS: Dict[MOVOTO_TASK_TYPES, Callable[[dict], dict]] = {
    "movoto_home_search": movoto_home_search,
    "movoto_filter_price_range": movoto_filter_price_range,
    "movoto_filter_beds_baths": movoto_filter_beds_baths,
    "movoto_sort_results": movoto_sort_results,
    "movoto_property_details": movoto_property_details,
    "movoto_save_search": movoto_save_search,
    "movoto_signup_flow": movoto_signup_flow,
    "movoto_contact_agent": movoto_contact_agent,
    "movoto_school_info": movoto_school_info,
    "movoto_map_draw_search": movoto_map_draw_search,
    "movoto_open_house_filter": movoto_open_house_filter,
    "movoto_recently_sold_search": movoto_recently_sold_search,
    "movoto_property_compare": movoto_property_compare,
    "movoto_neighborhood_explore": movoto_neighborhood_explore,
    "movoto_mortgage_calculator": movoto_mortgage_calculator,
}

def generate_movoto_task(task_type: MOVOTO_TASK_TYPES, payload: dict) -> dict:
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
    items = list(MOVOTO_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_movoto_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)