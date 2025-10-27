import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

STUDENTCOM_TASK_TYPES = Literal[
    "studentcom_city_search",
    "studentcom_property_detail",
    "studentcom_filter_room_type",
    "studentcom_filter_price_range",
    "studentcom_sort_results",
    "studentcom_view_country_listing",
    "studentcom_view_city_listing",
    "studentcom_view_university_listing"
]

STUDENTCOM_SAMPLING_CONFIG: Dict[STUDENTCOM_TASK_TYPES, int] = {
    "studentcom_city_search": 10,
    "studentcom_university_search": 10,
    "studentcom_property_detail": 10,
    "studentcom_filter_room_type": 10,
    "studentcom_filter_price_range": 10,
    "studentcom_sort_results": 10,
    "studentcom_view_country_listing": 10,
    "studentcom_view_city_listing": 10,
    "studentcom_view_university_listing": 10,
}

CITIES = [
    "London", "Sydney", "Melbourne", "Dublin", "New York", "Los Angeles", "Berlin", "Toronto", "Singapore", "Hong Kong",
    "Boston", "Madrid", "Barcelona", "Lisbon", "Paris", "Liverpool", "Rome", "Milan", "Brisbane", "Montréal",
    "Seoul", "Manchester", "Glasgow", "Perth", "Washington, D.C", "Tokyo", "Valencia", "Edinburgh", "Chicago, IL",
    "Leeds", "Birmingham", "Porto", "Auckland", "Bologna", "Adelaide", "Nottingham", "Leicester", "Vienna", "Zurich"
]

UNIVERSITIES = [
    "Arizona State University (ASU)", "Coventry University", "Curtin University", "Grand Canyon University (GCU)",
    "Griffith University", "King's College London", "Monash University", "Nottingham Trent University",
    "Ohio State University", "Queensland University of Technology (QUT)", "RMIT University",
    "Pennsylvania State University (Penn State)", "University of Birmingham", "University of Edinburgh",
    "University of Glasgow", "University of Manchester", "University College London (UCL)",
    "University of Central Florida (UCF)", "University of Melbourne", "University of New South Wales (UNSW)",
    "University of Nottingham", "University of Queensland (UQ)", "University of Sydney",
    "University of Technology Sydney (UTS)", "University of Leeds", "University of Hull", "University of Essex",
    "New York University", "Georgia Tech University", "University of Florida", "Emory University"
]

PROPERTIES_GLASGOW = [
    "Kaplan Living Glasgow - Old Dumbarton Road", "Aparthotel Adagio Glasgow Central", "Martha Street Apartments",
    "Scotway House", "Foundry Courtyard", "Bridle Works", "Clyde Court", "The Social Hub Glasgow",
    "Kaplan Living Glasgow – Argyle Street", "Riverside"
]

ROOM_TYPES = [
    "Studio", "En-suite", "Non-en-suite", "Twin Room", "Single Room", "Double Room", "Apartment", "Shared Room",
    "Private Room", "1 Bed Apartment", "2 Bed Apartment", "3 Bed Apartment", "4 Bed Apartment", "5 Bed Apartment",
    "Penthouse", "Cluster Room", "Loft", "Premium Studio", "Deluxe Room", "Accessible Room", "Superior Room"
]

PRICE_RANGES = [
    "£100-£150", "£151-£200", "£201-£250", "£251-£300", "£301-£350", "£351-£400", "£401-£450", "£451-£500",
    "£501-£550", "£551-£600", "£601-£650", "£651-£700", "£701-£750", "£751-£800", "£801-£850", "£851-£900",
    "£901-£950", "£951-£1000", "£1001-£1050", "£1051-£1100", "£1101-£1150", "£1151-£1200"
]

SORT_OPTIONS = [
    "Recommended", "Lowest Price", "Highest Price", "Closest to University", "Furthest from University",
    "Most Popular", "Best Rated", "Newest", "Earliest Move-in", "Latest Move-in", "Earliest Move-out",
    "Latest Move-out", "Shortest Lease", "Longest Lease", "Best Value", "Instant Book", "Price Match",
    "Premium", "Standard", "Economy"
]

COUNTRIES = [
    "United Kingdom", "United States", "Australia", "Spain", "Italy", "Canada", "Germany", "Ireland", "Portugal",
    "France", "Singapore", "Hong Kong", "South Korea", "Japan", "New Zealand", "China", "Netherlands", "Austria",
    "South Africa", "Hungary", "United Arab Emirates", "Belgium", "Poland", "Turkey", "Greece", "Sweden",
    "Switzerland", "Czech Republic", "Colombia", "Denmark", "Brazil", "Malta", "Mexico", "Chile", "Lithuania",
    "Luxembourg", "Argentina", "Latvia", "Peru"
]

PARTNERS = [
    "McGill University", "City of Glasgow College", "University of Glassgow", "University of Hull", "University of Leeds",
    "Newcastle University Medicine Malaysia", "University of Sheffield", "University of Manchester", "University of Liverpool",
    "Syracuse University London", "University College London", "Loughborough University London", "Screen and Film School Birmingham",
    "University of Arts London", "London School of Economics and Political Science", "University of Essex",
    "Ravensbourne University London", "Sunderland London", "King Stage Business School London", "Sotheby’s Institute of Art",
    "Richmond American University in London", "Arizona State University", "New York University", "Georgia Tech University",
    "University of Florida", "Emory University", "Boston University", "SAE Institutes", "ONCAMPUS", "Academic Programs International"
]

TESTIMONIALS = [
    "The process was very fast and efficient.",
    "Student.com was always kind and courteous to me.",
    "Amazing experience!",
    "Student.com helped me a lot!"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss popups/banners (e.g., 'Accept cookies', 'AI promo', 'Notifications').",
        "Do not submit any forms or make bookings; only search and view results.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Student.com", steps).model_dump()

def _rand_city():
    return random.choice(CITIES)

def _rand_university():
    return random.choice(UNIVERSITIES)

def _rand_property():
    return random.choice(PROPERTIES_GLASGOW)

def _rand_room_type():
    return random.choice(ROOM_TYPES)

def _rand_price_range():
    return random.choice(PRICE_RANGES)

def _rand_sort_option():
    return random.choice(SORT_OPTIONS)

def _rand_country():
    return random.choice(COUNTRIES)

def _rand_partner():
    return random.choice(PARTNERS)

def _rand_testimonial():
    return random.choice(TESTIMONIALS)

def studentcom_city_search(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.student.com/'.",
        *_ui_hygiene(),
        "Focus the search box labeled 'Search by city, university or property'.",
        f"Type '{city}' and select the autocomplete suggestion for '{city}'.",
        "Confirm search results page loads for the selected city.",
        "Verify at least one property is listed for the city.",
        "Assert the city name is present in the page heading or breadcrumb.",
    ]
    return {"task_type": "studentcom_city_search", "city": city, "steps": steps}

def studentcom_university_search(_: dict) -> dict:
    university = _rand_university()
    steps = [
        "Go to url 'https://www.student.com/'.",
        *_ui_hygiene(),
        "Focus the search box labeled 'Search by city, university or property'.",
        f"Type '{university}' and select the autocomplete suggestion for '{university}'.",
        "Confirm search results page loads for the selected university.",
        "Verify at least one property is listed for the university.",
        "Assert the university name is present in the page heading or breadcrumb.",
    ]
    return {"task_type": "studentcom_university_search", "university": university, "steps": steps}

def studentcom_property_detail(_: dict) -> dict:
    property_name = _rand_property()
    steps = [
        "Go to url 'https://www.student.com/'.",
        *_ui_hygiene(),
        "Scroll to the 'Student Accommodation Students Love' section.",
        f"Click the link labeled 'Go to {property_name} page'.",
        f"Verify the property detail page for '{property_name}' loads.",
        f"Assert the property name '{property_name}' is present in the page heading.",
        "Check that room types or pricing information is visible.",
    ]
    return {"task_type": "studentcom_property_detail", "property": property_name, "steps": steps}

def studentcom_filter_room_type(_: dict) -> dict:
    city = _rand_city()
    room_type = _rand_room_type()
    steps = [
        "Go to url 'https://www.student.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' in the search box and select the suggestion.",
        "Wait for the city results page to load.",
        "Open the 'Room Type' filter dropdown.",
        f"Select '{room_type}' from the list.",
        "Apply the filter.",
        f"Verify that only properties with room type '{room_type}' are shown.",
        "Assert the filter chip or summary shows the selected room type.",
    ]
    return {"task_type": "studentcom_filter_room_type", "city": city, "room_type": room_type, "steps": steps}

def studentcom_filter_price_range(_: dict) -> dict:
    city = _rand_city()
    price_range = _rand_price_range()
    steps = [
        "Go to url 'https://www.student.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' in the search box and select the suggestion.",
        "Wait for the city results page to load.",
        "Open the 'All Filters' panel.",
        f"Set the price range filter to '{price_range}'.",
        "Apply the filter.",
        f"Verify that all listed properties have prices within '{price_range}'.",
        "Assert the filter summary or chip reflects the selected price range.",
    ]
    return {"task_type": "studentcom_filter_price_range", "city": city, "price_range": price_range, "steps": steps}

def studentcom_sort_results(_: dict) -> dict:
    city = _rand_city()
    sort_option = _rand_sort_option()
    steps = [
        "Go to url 'https://www.student.com/'.",
        *_ui_hygiene(),
        f"Search for '{city}' in the search box and select the suggestion.",
        "Wait for the city results page to load.",
        "Open the 'Sort by' dropdown.",
        f"Select '{sort_option}' from the list.",
        "Verify that the results are sorted according to '{sort_option}'.",
        "Assert the sort dropdown displays the selected option.",
    ]
    return {"task_type": "studentcom_sort_results", "city": city, "sort_option": sort_option, "steps": steps}

def studentcom_view_country_listing(_: dict) -> dict:
    country = _rand_country()
    steps = [
        "Go to url 'https://www.student.com/'.",
        *_ui_hygiene(),
        "Scroll to the 'Popular countries' section.",
        f"Click the link labeled '{country}'.",
        f"Verify the country listing page for '{country}' loads.",
        f"Assert '{country}' is present in the page heading or breadcrumb.",
        "Check that at least one city or property is listed.",
    ]
    return {"task_type": "studentcom_view_country_listing", "country": country, "steps": steps}

def studentcom_view_city_listing(_: dict) -> dict:
    city = _rand_city()
    steps = [
        "Go to url 'https://www.student.com/'.",
        *_ui_hygiene(),
        "Scroll to the 'Popular cities' section.",
        f"Click the link labeled '{city}'.",
        f"Verify the city listing page for '{city}' loads.",
        f"Assert '{city}' is present in the page heading or breadcrumb.",
        "Check that at least one property is listed.",
    ]
    return {"task_type": "studentcom_view_city_listing", "city": city, "steps": steps}

def studentcom_view_university_listing(_: dict) -> dict:
    university = _rand_university()
    steps = [
        "Go to url 'https://www.student.com/'.",
        *_ui_hygiene(),
        "Scroll to the 'Popular universities' section.",
        f"Click the link labeled '{university}'.",
        f"Verify the university listing page for '{university}' loads.",
        f"Assert '{university}' is present in the page heading or breadcrumb.",
        "Check that at least one property is listed.",
    ]
    return {"task_type": "studentcom_view_university_listing", "university": university, "steps": steps}

_TASK_GENERATORS: Dict[STUDENTCOM_TASK_TYPES, Callable[[dict], dict]] = {
    "studentcom_city_search": studentcom_city_search,
    "studentcom_university_search": studentcom_university_search,
    "studentcom_property_detail": studentcom_property_detail,
    "studentcom_filter_room_type": studentcom_filter_room_type,
    "studentcom_filter_price_range": studentcom_filter_price_range,
    "studentcom_sort_results": studentcom_sort_results,
    "studentcom_view_country_listing": studentcom_view_country_listing,
    "studentcom_view_city_listing": studentcom_view_city_listing,
    "studentcom_view_university_listing": studentcom_view_university_listing,
}

def generate_studentcom_task(task_type: STUDENTCOM_TASK_TYPES, payload: dict) -> dict:
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
    items = list(STUDENTCOM_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_studentcom_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)