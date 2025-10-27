import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

APTCITIES = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ", "Philadelphia, PA", "San Antonio, TX",
    "San Diego, CA", "Dallas, TX", "San Jose, CA", "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH",
    "Charlotte, NC", "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
    "Boston, MA", "El Paso, TX", "Nashville, TN", "Detroit, MI", "Oklahoma City, OK", "Portland, OR", "Las Vegas, NV",
    "Memphis, TN", "Louisville, KY", "Baltimore, MD"
]
APTSTATES = [
    "NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH", "NC", "IN", "WA", "CO", "DC", "MA", "TN", "MI", "OK", "OR", "NV", "KY", "MD"
]
APTNEIGHBORHOODS = [
    "Downtown", "Midtown", "Uptown", "Chinatown", "SoHo", "Harlem", "Brooklyn Heights", "Hollywood", "Mission District",
    "South End", "Capitol Hill", "Queen Anne", "Lincoln Park", "The Loop", "River North", "West Loop", "South Boston",
    "Beacon Hill", "Fremont", "Ballard", "Upper East Side", "Chelsea", "Financial District", "Nob Hill", "Pacific Heights"
]
APTSEARCH_TERMS = [
    "studio", "1 bedroom", "2 bedroom", "pet friendly", "luxury", "downtown", "pool", "gym", "washer dryer", "parking",
    "balcony", "loft", "furnished", "utilities included", "short term", "student", "affordable", "senior", "family", "modern", "renovated",
    "garden", "city view", "hardwood", "walk-in closet"
]
APTMINPRICES = [str(x*100) for x in range(5, 25)]  # 500-2400
APTMAXPRICES = [str(x*100) for x in range(10, 41)] # 1000-4000
APTBEDROOMS = ["Studio", "1 Bed", "2 Beds", "3 Beds", "4 Beds", "5 Beds"]
APTBATHS = ["1 Bath", "1.5 Baths", "2 Baths", "2.5 Baths", "3+ Baths"]
APTPETS = ["Cats Allowed", "Dogs Allowed", "No Pets", "Large Dogs", "Small Dogs", "Breed Restrictions"]
APTSORTS = [
    "Best Match", "Price: Low to High", "Price: High to Low", "Beds", "Baths", "Move-In Date", "Newest", "Distance", "Square Feet", "Top Rated"
]
APTAMENITIES = [
    "Pool", "Fitness Center", "Washer/Dryer", "Parking", "Dishwasher", "Air Conditioning", "Balcony", "Hardwood Floors", "Elevator",
    "Doorman", "Pet Friendly", "Fireplace", "Walk-In Closets", "Laundry Facility", "Furnished", "Controlled Access", "Garage",
    "Playground", "Business Center", "Wheelchair Access", "Refrigerator", "Microwave", "Patio", "Cable Ready"
]
APTPROPERTY_TYPES = [
    "Apartment", "House", "Condo", "Townhome", "Loft", "Studio", "Senior Housing", "Student Housing", "Corporate Housing",
    "Duplex", "Triplex", "Fourplex", "Mobile Home", "Manufactured", "Sublet", "Room", "Penthouse", "Basement", "Cottage",
    "Bungalow", "Cabin"
]
APTCOMMUNITIES = [
    "Avalon", "Camden", "Equity", "Greystar", "UDR", "Lincoln", "Bozzuto", "Related", "Gables", "Windsor", "Fairfield",
    "Morgan", "Trammell Crow", "AMLI", "Cortland", "Bell Partners", "Pinnacle", "Alliance", "Village Green", "Wood Partners"
]
APTMOVEINDATES = [(dt.date.today() + dt.timedelta(days=d)).strftime("%Y-%m-%d") for d in range(1, 61, 3)]  # 20+ dates
APTFAQ_TOPICS = [
    "How do I schedule a tour?", "How do I apply for an apartment?", "What is the pet policy?", "How do I contact the property manager?",
    "What are the lease terms?", "How do I report an issue?", "How do I reset my password?", "How do I save my favorite listings?",
    "How do I filter for pet-friendly apartments?", "How do I use the map search?", "How do I compare apartments?", "How do I find short-term rentals?",
    "How do I find affordable apartments?", "How do I find furnished apartments?", "How do I contact support?", "How do I unsubscribe from emails?",
    "How do I find senior housing?", "How do I find student housing?", "How do I use the rent calculator?", "How do I search by school district?",
    "How do I find apartments with utilities included?", "How do I view floor plans?", "How do I request a virtual tour?"
]
APTREGISTER_FIELDS = [
    "First Name", "Last Name", "Email", "Password", "Phone Number", "Agree to Terms", "Show Password", "Marketing Opt-in", "Zip Code", "Preferred City"
]
APTLOGIN_ERRORS = [
    "Invalid email or password", "Account locked", "Email not registered", "Password required", "Captcha required", "Too many attempts"
]
APTCONTACT_REASONS = [
    "Schedule a tour", "Request more information", "Check availability", "Ask about pet policy", "Request virtual tour",
    "Ask about lease terms", "Request application", "Ask about parking", "Ask about amenities", "Report a listing issue",
    "Ask about move-in specials", "Ask about utilities", "Ask about furnished options", "Ask about short-term lease", "Request floor plans",
    "Request photos", "Ask about neighborhood", "Ask about public transit", "Ask about accessibility", "Ask about security"
]
APTADVANCED_FILTERS = [
    {"amenity": "Pool", "pet": "Dogs Allowed", "bed": "2 Beds", "bath": "2 Baths"},
    {"amenity": "Fitness Center", "pet": "Cats Allowed", "bed": "1 Bed", "bath": "1 Bath"},
    {"amenity": "Washer/Dryer", "pet": "No Pets", "bed": "Studio", "bath": "1 Bath"},
    {"amenity": "Parking", "pet": "Dogs Allowed", "bed": "3 Beds", "bath": "2.5 Baths"},
    {"amenity": "Balcony", "pet": "Cats Allowed", "bed": "2 Beds", "bath": "2 Baths"},
    {"amenity": "Hardwood Floors", "pet": "No Pets", "bed": "1 Bed", "bath": "1 Bath"},
    {"amenity": "Elevator", "pet": "Dogs Allowed", "bed": "Studio", "bath": "1 Bath"},
    {"amenity": "Doorman", "pet": "Cats Allowed", "bed": "2 Beds", "bath": "2 Baths"},
    {"amenity": "Fireplace", "pet": "Dogs Allowed", "bed": "3 Beds", "bath": "2.5 Baths"},
    {"amenity": "Walk-In Closets", "pet": "Cats Allowed", "bed": "2 Beds", "bath": "2 Baths"},
    {"amenity": "Laundry Facility", "pet": "No Pets", "bed": "1 Bed", "bath": "1 Bath"},
    {"amenity": "Furnished", "pet": "Dogs Allowed", "bed": "Studio", "bath": "1 Bath"},
    {"amenity": "Controlled Access", "pet": "Cats Allowed", "bed": "2 Beds", "bath": "2 Baths"},
    {"amenity": "Garage", "pet": "Dogs Allowed", "bed": "3 Beds", "bath": "2.5 Baths"},
    {"amenity": "Playground", "pet": "Cats Allowed", "bed": "2 Beds", "bath": "2 Baths"},
    {"amenity": "Business Center", "pet": "No Pets", "bed": "1 Bed", "bath": "1 Bath"},
    {"amenity": "Wheelchair Access", "pet": "Dogs Allowed", "bed": "Studio", "bath": "1 Bath"},
    {"amenity": "Refrigerator", "pet": "Cats Allowed", "bed": "2 Beds", "bath": "2 Baths"},
    {"amenity": "Microwave", "pet": "Dogs Allowed", "bed": "3 Beds", "bath": "2.5 Baths"},
    {"amenity": "Patio", "pet": "Cats Allowed", "bed": "2 Beds", "bath": "2 Baths"},
    {"amenity": "Cable Ready", "pet": "No Pets", "bed": "1 Bed", "bath": "1 Bath"}
]

APT_TASK_TYPES = Literal[
    "apt_city_search",
    "apt_neighborhood_search",
    "apt_filter_price_range",
    "apt_filter_bed_bath",
    "apt_filter_amenities",
    "apt_sort_results",
    "apt_property_type_search",
    "apt_register_account",
    "apt_login_negative",
    "apt_contact_property",
    "apt_faq_browse",
    "apt_save_favorite",
    "apt_compare_listings",
    "apt_map_search",
    "apt_schedule_tour",
    "apt_view_floorplans",
    "apt_view_community_page"
]

APT_SAMPLING_CONFIG: Dict[APT_TASK_TYPES, int] = {
    "apt_city_search": 10,
    "apt_neighborhood_search": 10,
    "apt_filter_price_range": 10,
    "apt_filter_bed_bath": 10,
    "apt_filter_amenities": 10,
    "apt_sort_results": 10,
    "apt_property_type_search": 10,
    "apt_register_account": 10,
    "apt_login_negative": 10,
    "apt_contact_property": 10,
    "apt_faq_browse": 10,
    "apt_save_favorite": 10,
    "apt_compare_listings": 10,
    "apt_map_search": 10,
    "apt_schedule_tour": 10,
    "apt_view_floorplans": 10,
    "apt_view_community_page": 10
}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, banners, or cookie notices.",
        "Do not submit any sensitive or personal information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Apartments.com", steps).model_dump()

def apt_city_search(_: dict) -> dict:
    city = random.choice(APTCITIES)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Focus the main search input.",
        f"Type '{city}' and select from autocomplete.",
        "Click the search button.",
        f"Assert the results page shows listings for '{city.split(',')[0]}' in the heading.",
        "Verify at least one listing is displayed.",
        "Check that the URL contains the city name or abbreviation.",
    ]
    return {"task_type": "apt_city_search", "city": city, "steps": steps}

def apt_neighborhood_search(_: dict) -> dict:
    city = random.choice(APTCITIES)
    hood = random.choice(APTNEIGHBORHOODS)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Focus the main search input.",
        f"Type '{hood}, {city}' and select from autocomplete.",
        "Click the search button.",
        f"Assert the results page shows listings for '{hood}' in '{city.split(',')[0]}'.",
        "Verify at least one listing is displayed.",
        "Check that the URL contains the neighborhood and city.",
    ]
    return {"task_type": "apt_neighborhood_search", "city": city, "neighborhood": hood, "steps": steps}

def apt_filter_price_range(_: dict) -> dict:
    city = random.choice(APTCITIES)
    minp = random.choice(APTMINPRICES)
    maxp = random.choice([x for x in APTMAXPRICES if int(x) > int(minp)])
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        f"Set minimum price filter to ${minp}.",
        f"Set maximum price filter to ${maxp}.",
        "Apply filters.",
        f"Assert that all displayed listings have rents between ${minp} and ${maxp}.",
        "If no listings, assert 'No results found' is shown.",
    ]
    return {"task_type": "apt_filter_price_range", "city": city, "min_price": minp, "max_price": maxp, "steps": steps}

def apt_filter_bed_bath(_: dict) -> dict:
    city = random.choice(APTCITIES)
    bed = random.choice(APTBEDROOMS)
    bath = random.choice(APTBATHS)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        f"Set bedrooms filter to '{bed}'.",
        f"Set bathrooms filter to '{bath}'.",
        "Apply filters.",
        f"Assert that all displayed listings have at least {bed} and {bath}.",
        "If no listings, assert 'No results found' is shown.",
    ]
    return {"task_type": "apt_filter_bed_bath", "city": city, "bedrooms": bed, "bathrooms": bath, "steps": steps}

def apt_filter_amenities(_: dict) -> dict:
    city = random.choice(APTCITIES)
    amenity = random.choice(APTAMENITIES)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        f"Open the 'Amenities' filter panel.",
        f"Select '{amenity}'.",
        "Apply filters.",
        f"Assert that all displayed listings mention '{amenity}' in amenities/features.",
        "If no listings, assert 'No results found' is shown.",
    ]
    return {"task_type": "apt_filter_amenities", "city": city, "amenity": amenity, "steps": steps}

def apt_sort_results(_: dict) -> dict:
    city = random.choice(APTCITIES)
    sort = random.choice(APTSORTS)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        f"Open the sort dropdown and select '{sort}'.",
        "Wait for results to update.",
        f"Assert that the listings are sorted by '{sort}'.",
        "If sort is 'Price: Low to High', verify first listing has lowest price.",
    ]
    return {"task_type": "apt_sort_results", "city": city, "sort": sort, "steps": steps}

def apt_property_type_search(_: dict) -> dict:
    city = random.choice(APTCITIES)
    ptype = random.choice(APTPROPERTY_TYPES)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        f"Open the 'Property Type' filter panel.",
        f"Select '{ptype}'.",
        "Apply filters.",
        f"Assert that all displayed listings are of type '{ptype}'.",
        "If no listings, assert 'No results found' is shown.",
    ]
    return {"task_type": "apt_property_type_search", "city": city, "property_type": ptype, "steps": steps}

def apt_register_account(_: dict) -> dict:
    field = random.choice(APTREGISTER_FIELDS)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        "Click 'Sign Up' or 'Register' in the header.",
        "Wait for registration form to appear.",
        f"Verify the presence of '{field}' field or checkbox.",
        "Do not submit the form.",
    ]
    return {"task_type": "apt_register_account", "field": field, "steps": steps}

def apt_login_negative(_: dict) -> dict:
    error = random.choice(APTLOGIN_ERRORS)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        "Click 'Sign In' in the header.",
        "Wait for login form to appear.",
        "Enter invalid credentials (e.g., 'fakeuser@example.com', 'wrongpassword').",
        "Submit the form.",
        f"Assert that error message '{error}' appears.",
    ]
    return {"task_type": "apt_login_negative", "expected_error": error, "steps": steps}

def apt_contact_property(_: dict) -> dict:
    city = random.choice(APTCITIES)
    reason = random.choice(APTCONTACT_REASONS)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Click on the first listing to open its detail page.",
        "Locate the 'Contact' or 'Request Info' form.",
        f"Verify that '{reason}' is an available reason or can be entered in the message box.",
        "Do not submit the form.",
    ]
    return {"task_type": "apt_contact_property", "city": city, "reason": reason, "steps": steps}

def apt_faq_browse(_: dict) -> dict:
    topic = random.choice(APTFAQ_TOPICS)
    steps = [
        "Go to url 'https://www.apartments.com/help/' or click 'Help'/'FAQ' in the footer.",
        *_ui_hygiene(),
        f"Search or browse for the FAQ: '{topic}'.",
        f"Assert that the FAQ answer for '{topic}' is visible.",
        "If not found, assert a 'No results' or similar message is shown.",
    ]
    return {"task_type": "apt_faq_browse", "faq_topic": topic, "steps": steps}

def apt_save_favorite(_: dict) -> dict:
    city = random.choice(APTCITIES)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Click the 'heart' or 'save' icon on the first listing.",
        "Assert that the listing is marked as saved/favorite (icon changes or confirmation appears).",
        "If not signed in, assert that a sign-in prompt appears.",
    ]
    return {"task_type": "apt_save_favorite", "city": city, "steps": steps}

def apt_compare_listings(_: dict) -> dict:
    city = random.choice(APTCITIES)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Select the first two listings using the 'Compare' checkbox or button.",
        "Click 'Compare' to open the comparison view.",
        "Assert that both selected listings are displayed side by side.",
        "Verify at least rent and amenities are shown for both.",
    ]
    return {"task_type": "apt_compare_listings", "city": city, "steps": steps}

def apt_map_search(_: dict) -> dict:
    city = random.choice(APTCITIES)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Switch to map view.",
        "Pan or zoom the map to a different area.",
        "Assert that the listings update to match the visible map area.",
        "Click a map pin and verify the listing preview appears.",
    ]
    return {"task_type": "apt_map_search", "city": city, "steps": steps}

def apt_schedule_tour(_: dict) -> dict:
    city = random.choice(APTCITIES)
    movein = random.choice(APTMOVEINDATES)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Click on the first listing to open its detail page.",
        "Locate the 'Schedule a Tour' or 'Request Tour' button.",
        f"Open the tour scheduling form and select move-in date '{movein}'.",
        "Verify that available tour times are shown for the selected date.",
        "Do not submit the form.",
    ]
    return {"task_type": "apt_schedule_tour", "city": city, "movein_date": movein, "steps": steps}

def apt_view_floorplans(_: dict) -> dict:
    city = random.choice(APTCITIES)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "Wait for results to load.",
        "Click on the first listing to open its detail page.",
        "Locate the 'Floor Plans' section or tab.",
        "Assert that at least one floor plan is displayed with rent and bed/bath info.",
    ]
    return {"task_type": "apt_view_floorplans", "city": city, "steps": steps}

def apt_view_community_page(_: dict) -> dict:
    community = random.choice(APTCOMMUNITIES)
    city = random.choice(APTCITIES)
    steps = [
        "Go to url 'https://www.apartments.com'.",
        *_ui_hygiene(),
        f"Type '{community} {city}' in the search input and select from autocomplete.",
        "Click the search button.",
        "Click on the first listing to open its detail page.",
        f"Assert that the community name '{community}' appears on the page.",
        "Verify that at least one amenity or feature is listed.",
    ]
    return {"task_type": "apt_view_community_page", "community": community, "city": city, "steps": steps}

_TASK_GENERATORS: Dict[APT_TASK_TYPES, Callable[[dict], dict]] = {
    "apt_city_search": apt_city_search,
    "apt_neighborhood_search": apt_neighborhood_search,
    "apt_filter_price_range": apt_filter_price_range,
    "apt_filter_bed_bath": apt_filter_bed_bath,
    "apt_filter_amenities": apt_filter_amenities,
    "apt_sort_results": apt_sort_results,
    "apt_property_type_search": apt_property_type_search,
    "apt_register_account": apt_register_account,
    "apt_login_negative": apt_login_negative,
    "apt_contact_property": apt_contact_property,
    "apt_faq_browse": apt_faq_browse,
    "apt_save_favorite": apt_save_favorite,
    "apt_compare_listings": apt_compare_listings,
    "apt_map_search": apt_map_search,
    "apt_schedule_tour": apt_schedule_tour,
    "apt_view_floorplans": apt_view_floorplans,
    "apt_view_community_page": apt_view_community_page
}

def generate_apt_task(task_type: APT_TASK_TYPES, payload: dict) -> dict:
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
    items = list(APT_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_apt_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)