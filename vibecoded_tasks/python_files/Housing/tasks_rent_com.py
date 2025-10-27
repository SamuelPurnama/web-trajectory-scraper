import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

RENT_TASK_TYPES = Literal[
    "rent_search_city",
    "rent_filter_price_range",
    "rent_filter_bed_bath",
    "rent_filter_property_type",
    "rent_popular_search",
    "rent_footer_navigation",
    "rent_research_category_nav",
    "rent_research_searchbox",
    "rent_research_report_open",
    "rent_research_city_report",
    "rent_research_see_more",
    "rent_interactive_chart",
    "rent_contact_form_valid",
    "rent_contact_form_invalid",
    "rent_accessibility_feedback",
    "rent_download_app",
    "rent_social_media_link",
    "rent_let_us_help_link",
    "rent_research_topic_link",
    "rent_skip_to_content",
]

RENT_SAMPLING_CONFIG: Dict[RENT_TASK_TYPES, int] = {
    "rent_search_city": 10,
    "rent_filter_price_range": 10,
    "rent_filter_bed_bath": 10,
    "rent_filter_property_type": 10,
    "rent_popular_search": 10,
    "rent_footer_navigation": 10,
    "rent_research_category_nav": 10,
    "rent_research_searchbox": 10,
    "rent_research_report_open": 10,
    "rent_research_city_report": 10,
    "rent_research_see_more": 10,
    "rent_interactive_chart": 10,
    "rent_contact_form_valid": 10,
    "rent_contact_form_invalid": 10,
    "rent_accessibility_feedback": 10,
    "rent_download_app": 10,
    "rent_social_media_link": 10,
    "rent_let_us_help_link": 10,
    "rent_research_topic_link": 10,
    "rent_skip_to_content": 10,
}

CITIES = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ", "Philadelphia, PA",
    "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA", "Austin, TX", "Jacksonville, FL",
    "Fort Worth, TX", "Columbus, OH", "Charlotte, NC", "San Francisco, CA", "Indianapolis, IN", "Seattle, WA",
    "Denver, CO", "Washington, DC", "Boston, MA", "Nashville, TN", "El Paso, TX", "Detroit, MI", "Oklahoma City, OK"
]

PRICE_RANGES = [
    "$500-$700", "$700-$900", "$900-$1100", "$1100-$1300", "$1300-$1500", "$1500-$1700", "$1700-$1900", "$1900-$2100",
    "$2100-$2300", "$2300-$2500", "$2500-$2700", "$2700-$2900", "$2900-$3100", "$3100-$3300", "$3300-$3500",
    "$3500-$3700", "$3700-$3900", "$3900-$4100", "$4100-$4300", "$4300-$4500", "$4500-$4700", "$4700-$4900"
]

BEDROOMS = ["Studio", "1 Bed", "2 Beds", "3 Beds", "4 Beds", "5+ Beds"]
BATHROOMS = ["1 Bath", "1.5 Baths", "2 Baths", "2.5 Baths", "3 Baths", "3.5 Baths", "4+ Baths"]
PROPERTY_TYPES = [
    "Apartment", "House", "Townhome", "Condo", "Loft", "Studio", "Duplex", "Triplex", "Fourplex", "Mobile Home",
    "Senior Housing", "Student Housing", "Corporate Housing", "Short Term", "Furnished", "Unfurnished", "Luxury",
    "Affordable", "Pet Friendly", "Gated", "High Rise", "Low Rise", "Garden"
]
POPULAR_SEARCHES = [
    "Houses for Rent", "Cheap Apartments for Rent", "Pet Friendly Apartments", "Studio Apartments", "Luxury Apartments",
    "Furnished Apartments", "Short Term Rentals", "Townhomes for Rent", "Condos for Rent", "Apartments with Utilities Included",
    "Senior Apartments", "Student Apartments", "Gated Apartments", "Low Income Apartments", "Section 8 Apartments",
    "Apartments with Washer Dryer", "Apartments with Pool", "Apartments with Gym", "Apartments with Parking",
    "Apartments with Balcony", "Downtown Apartments", "Suburban Apartments"
]
FOOTER_LINKS = [
    "About Us", "Press & Media", "Careers", "Privacy Policy", "Terms of Service",
    "Do Not Share or Sell My Personal Information", "Site Map", "Accessibility"
]
RESEARCH_CATEGORIES = [
    "Industry Trends", "Renting Trends", "Surveys", "Market Reports"
]
RESEARCH_SEARCH_TERMS = [
    "average rent", "rent trends", "affordable cities", "pet friendly", "studio", "luxury", "utilities included",
    "short term", "senior housing", "student housing", "market report", "rent increase", "vacancy rate", "downtown",
    "suburban", "furnished", "unfurnished", "gated", "parking", "pool", "gym", "balcony", "low income"
]
RESEARCH_REPORTS = [
    "February 2025 Average Rent Report: Rents Rise as Construction Slows",
    "January 2025 Rent Report", "2025 Market Outlook", "2024 Year-End Rental Trends",
    "Top 10 Cities for Renters 2025", "Columbus, OH Has a Rapidly Falling Share of Rentals for Under $1,000",
    "Miami, FL Rent Growth", "Austin, TX Rental Market", "Affordable Rentals in Chicago",
    "Luxury Apartments in Los Angeles", "Pet Friendly Trends 2025", "Student Housing Insights",
    "Senior Housing Demand", "Short Term Rental Growth", "Gated Community Trends",
    "Downtown vs Suburban Rent", "Parking Availability Report", "Pool/Gym Amenities Study",
    "Washer Dryer In-Unit Trends", "Furnished Apartment Demand", "Section 8 Housing Report",
    "Renting with Pets: Survey"
]
CITY_REPORTS = [
    "Columbus, OH", "Miami, FL", "Austin, TX", "Chicago, IL", "Los Angeles, CA", "New York, NY",
    "San Francisco, CA", "Seattle, WA", "Denver, CO", "Boston, MA", "Houston, TX", "Dallas, TX",
    "San Diego, CA", "Charlotte, NC", "Indianapolis, IN", "Phoenix, AZ", "Philadelphia, PA",
    "San Antonio, TX", "Jacksonville, FL", "Washington, DC", "Nashville, TN", "Detroit, MI"
]
SEE_MORE_LABELS = [
    "See More Reports", "See More Market Reports", "See More Trends", "See More Surveys", "See More Research"
]
CHART_ACTIONS = [
    "hover over February 2025", "focus on Midwest region", "filter to last 12 months", "toggle National vs Regional",
    "zoom in on 2024 data", "view tooltip for January 2025", "switch to West region", "reset chart filters",
    "highlight Northeast region", "select 'All Regions'", "check legend for 'National'", "compare 2023 and 2025",
    "view trend line for South", "download chart image", "expand chart", "collapse chart", "switch to bar chart",
    "switch to line chart", "filter by city", "filter by state", "export data", "toggle accessibility mode"
]
CONTACT_VALID_NAMES = [
    "Alex Johnson", "Maria Lopez", "Chris Smith", "Taylor Nguyen", "Jordan Lee", "Morgan Patel", "Casey Kim",
    "Jamie Chen", "Robin Brown", "Drew Davis", "Avery Clark", "Riley Martinez", "Peyton Lewis", "Skyler Walker",
    "Dakota Hall", "Emerson Young", "Charlie King", "Reese Scott", "Harper Allen", "Quinn Wright", "Finley Baker"
]
CONTACT_VALID_EMAILS = [
    "alex.johnson@example.com", "maria.lopez@example.com", "chris.smith@example.com", "taylor.nguyen@example.com",
    "jordan.lee@example.com", "morgan.patel@example.com", "casey.kim@example.com", "jamie.chen@example.com",
    "robin.brown@example.com", "drew.davis@example.com", "avery.clark@example.com", "riley.martinez@example.com",
    "peyton.lewis@example.com", "skyler.walker@example.com", "dakota.hall@example.com", "emerson.young@example.com",
    "charlie.king@example.com", "reese.scott@example.com", "harper.allen@example.com", "quinn.wright@example.com",
    "finley.baker@example.com"
]
CONTACT_INVALID_EMAILS = [
    "alex.johnson@", "maria.lopez", "chris.smith@.com", "taylor@", "jordan.lee@com", "morgan.patel@.org",
    "casey.kim@domain", "jamie.chen@.net", "robin.brown@.edu", "drew.davis@.gov", "avery.clark@.co",
    "riley.martinez@.us", "peyton.lewis@.ca", "skyler.walker@.uk", "dakota.hall@.au", "emerson.young@.io",
    "charlie.king@.xyz", "reese.scott@.info", "harper.allen@.biz", "quinn.wright@.me", "finley.baker@.site"
]
LET_US_HELP_LINKS = [
    "Download App", "Avoid Scams", "List a Property", "Business Solutions"
]
SOCIAL_MEDIA_LINKS = [
    "Facebook", "Twitter", "Instagram", "LinkedIn", "TikTok", "YouTube", "Pinterest", "Snapchat",
    "Reddit", "Tumblr", "WhatsApp", "Telegram", "WeChat", "Line", "Viber", "VK", "Discord", "Clubhouse",
    "Threads", "Mastodon", "Xing"
]
RESEARCH_TOPIC_LINKS = [
    "Research", "Renting Trends", "Industry Trends", "Market Reports", "Surveys"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, banners, or cookie notices.",
        "Do not sign up, log in, or make any purchases.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Rent.com", steps).model_dump()

def rent_search_city(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = [
        "Go to url 'https://www.rent.com'.",
        *_ui_hygiene(),
        "Focus the main search input labeled 'City, State, or ZIP'.",
        f"Type '{city}' and select the autocomplete suggestion for that city.",
        "Click the search button.",
        f"Verify the results page shows listings for '{city}'.",
        "Assert the URL contains the city or state slug.",
        "Assert at least one property card is visible.",
    ]
    return {"task_type": "rent_search_city", "city": city, "steps": steps}

def rent_filter_price_range(_: dict) -> dict:
    city = random.choice(CITIES)
    price = random.choice(PRICE_RANGES)
    steps = [
        "Go to url 'https://www.rent.com'.",
        *_ui_hygiene(),
        f"Search for '{city}' as in a normal search.",
        "On the results page, locate the price range filter.",
        f"Set the price range to '{price}'.",
        "Apply the filter.",
        f"Verify that all visible listings show a price within '{price}'.",
        "Assert at least one property card is visible.",
        "Assert the filter chip or summary shows the selected price range.",
    ]
    return {"task_type": "rent_filter_price_range", "city": city, "price_range": price, "steps": steps}

def rent_filter_bed_bath(_: dict) -> dict:
    city = random.choice(CITIES)
    bed = random.choice(BEDROOMS)
    bath = random.choice(BATHROOMS)
    steps = [
        "Go to url 'https://www.rent.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "On the results page, open the beds filter dropdown.",
        f"Select '{bed}'.",
        "Open the baths filter dropdown.",
        f"Select '{bath}'.",
        "Apply the filters.",
        f"Verify all visible listings have at least '{bed}' and '{bath}'.",
        "Assert at least one property card is visible.",
        "Assert the filter summary shows the selected bed and bath.",
    ]
    return {"task_type": "rent_filter_bed_bath", "city": city, "bedroom": bed, "bathroom": bath, "steps": steps}

def rent_filter_property_type(_: dict) -> dict:
    city = random.choice(CITIES)
    ptype = random.choice(PROPERTY_TYPES)
    steps = [
        "Go to url 'https://www.rent.com'.",
        *_ui_hygiene(),
        f"Search for '{city}'.",
        "On the results page, open the property type filter.",
        f"Select '{ptype}'.",
        "Apply the filter.",
        f"Verify all visible listings are of type '{ptype}'.",
        "Assert at least one property card is visible.",
        "Assert the filter summary shows the selected property type.",
    ]
    return {"task_type": "rent_filter_property_type", "city": city, "property_type": ptype, "steps": steps}

def rent_popular_search(_: dict) -> dict:
    label = random.choice(POPULAR_SEARCHES)
    steps = [
        "Go to url 'https://www.rent.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Popular Searches' section.",
        f"Click the link labeled '{label}'.",
        "Verify the results page loads with the correct filter applied.",
        f"Assert the filter summary or page heading includes '{label}'.",
        "Assert at least one property card is visible.",
    ]
    return {"task_type": "rent_popular_search", "popular_search": label, "steps": steps}

def rent_footer_navigation(_: dict) -> dict:
    link = random.choice(FOOTER_LINKS)
    steps = [
        "Go to url 'https://www.rent.com'.",
        *_ui_hygiene(),
        "Scroll to the footer.",
        f"Click the link labeled '{link}'.",
        "Verify the new page or tab loads.",
        f"Assert the page heading or title contains '{link}'.",
        "Assert the URL matches the expected pattern for the footer page.",
    ]
    return {"task_type": "rent_footer_navigation", "footer_link": link, "steps": steps}

def rent_research_category_nav(_: dict) -> dict:
    cat = random.choice(RESEARCH_CATEGORIES)
    steps = [
        "Go to url 'https://www.rent.com/research/'.",
        *_ui_hygiene(),
        f"Click the navigation link labeled '{cat}'.",
        f"Verify the page loads with '{cat}' content.",
        "Assert the page heading or breadcrumb matches the category.",
        "Assert at least one article or report card is visible.",
    ]
    return {"task_type": "rent_research_category_nav", "category": cat, "steps": steps}

def rent_research_searchbox(_: dict) -> dict:
    term = random.choice(RESEARCH_SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.rent.com/research/'.",
        *_ui_hygiene(),
        "Focus the searchbox labeled 'Search'.",
        f"Type '{term}' and press Enter.",
        f"Verify the results list includes articles or reports related to '{term}'.",
        "Assert at least one result card is visible.",
        "Assert the searchbox retains the entered term.",
    ]
    return {"task_type": "rent_research_searchbox", "search_term": term, "steps": steps}

def rent_research_report_open(_: dict) -> dict:
    report = random.choice(RESEARCH_REPORTS)
    steps = [
        "Go to url 'https://www.rent.com/research/'.",
        *_ui_hygiene(),
        f"Locate the report titled '{report}'.",
        "Click the report title or image.",
        f"Verify the detailed report page loads for '{report}'.",
        "Assert the page heading matches the report title.",
        "Assert the URL contains a slugified version of the report title.",
    ]
    return {"task_type": "rent_research_report_open", "report_title": report, "steps": steps}

def rent_research_city_report(_: dict) -> dict:
    city = random.choice(CITY_REPORTS)
    steps = [
        "Go to url 'https://www.rent.com/research/'.",
        *_ui_hygiene(),
        f"Locate a city-specific report for '{city}'.",
        "Click the report link.",
        f"Verify the detailed report page loads for '{city}'.",
        "Assert the page heading or breadcrumb includes the city name.",
        "Assert the URL contains the city slug.",
    ]
    return {"task_type": "rent_research_city_report", "city": city, "steps": steps}

def rent_research_see_more(_: dict) -> dict:
    label = random.choice(SEE_MORE_LABELS)
    steps = [
        "Go to url 'https://www.rent.com/research/'.",
        *_ui_hygiene(),
        f"Scroll to the section with the '{label}' link.",
        f"Click '{label}'.",
        "Verify more reports or articles are loaded or navigated to.",
        "Assert the list of reports increases in length or a new page is loaded.",
    ]
    return {"task_type": "rent_research_see_more", "see_more_label": label, "steps": steps}

def rent_interactive_chart(_: dict) -> dict:
    action = random.choice(CHART_ACTIONS)
    steps = [
        "Go to url 'https://www.rent.com/research/'.",
        *_ui_hygiene(),
        "Scroll to the iframe labeled 'Interactive line chart: National and Regional Asking Rents'.",
        f"Perform the action: {action}.",
        "Verify the chart responds visually or with a tooltip/data change.",
        "Assert the chart interaction is reflected in the UI.",
    ]
    return {"task_type": "rent_interactive_chart", "chart_action": action, "steps": steps}

def rent_contact_form_valid(_: dict) -> dict:
    name = random.choice(CONTACT_VALID_NAMES)
    email = random.choice(CONTACT_VALID_EMAILS)
    steps = [
        "Go to url 'https://www.rent.com/research/'.",
        *_ui_hygiene(),
        "Scroll to the contact/interview request form.",
        f"Enter '{name}' in the 'Name *' textbox.",
        f"Enter '{email}' in the 'Email *' textbox.",
        "Click the 'Contact Us' button.",
        "Verify a success confirmation message appears.",
        "Assert the form fields are cleared or disabled after submission.",
    ]
    return {"task_type": "rent_contact_form_valid", "name": name, "email": email, "steps": steps}

def rent_contact_form_invalid(_: dict) -> dict:
    name = random.choice(CONTACT_VALID_NAMES)
    email = random.choice(CONTACT_INVALID_EMAILS)
    steps = [
        "Go to url 'https://www.rent.com/research/'.",
        *_ui_hygiene(),
        "Scroll to the contact/interview request form.",
        f"Enter '{name}' in the 'Name *' textbox.",
        f"Enter '{email}' in the 'Email *' textbox.",
        "Click the 'Contact Us' button.",
        "Verify an error message appears for invalid email.",
        "Assert the form is not submitted and fields are not cleared.",
    ]
    return {"task_type": "rent_contact_form_invalid", "name": name, "email": email, "steps": steps}

def rent_accessibility_feedback(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.rent.com/research/'.",
        *_ui_hygiene(),
        "Scroll to the link labeled 'accessibilityfeedback@rent.com'.",
        "Click the link.",
        "Verify the default email client opens with the 'To' field set to 'accessibilityfeedback@rent.com'.",
        "Assert the email compose window is visible.",
    ]
    return {"task_type": "rent_accessibility_feedback", "steps": steps}

def rent_download_app(_: dict) -> dict:
    platform = random.choice(["Android", "iOS"])
    steps = [
        "Go to url 'https://www.rent.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Download App' link (under 'Let Us Help' or similar).",
        f"Click the '{platform}' link.",
        f"Verify the app store page for '{platform}' opens in a new tab or window.",
        "Assert the page title or branding matches Rent.com and the selected platform.",
    ]
    return {"task_type": "rent_download_app", "platform": platform, "steps": steps}

def rent_social_media_link(_: dict) -> dict:
    platform = random.choice(SOCIAL_MEDIA_LINKS)
    steps = [
        "Go to url 'https://www.rent.com'.",
        *_ui_hygiene(),
        "Scroll to the footer or social media section.",
        f"Click the '{platform}' icon or link.",
        f"Verify the respective social media page for Rent.com opens in a new tab.",
        "Assert the URL matches the expected domain for '{platform}'.",
    ]
    return {"task_type": "rent_social_media_link", "platform": platform, "steps": steps}

def rent_let_us_help_link(_: dict) -> dict:
    label = random.choice(LET_US_HELP_LINKS)
    steps = [
        "Go to url 'https://www.rent.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Let Us Help' section.",
        f"Click the link labeled '{label}'.",
        "Verify the new page or tab loads.",
        f"Assert the page heading or title contains '{label}'.",
    ]
    return {"task_type": "rent_let_us_help_link", "let_us_help_link": label, "steps": steps}

def rent_research_topic_link(_: dict) -> dict:
    topic = random.choice(RESEARCH_TOPIC_LINKS)
    steps = [
        "Go to url 'https://www.rent.com/research/'.",
        *_ui_hygiene(),
        f"Locate a link labeled '{topic}' next to an article or in navigation.",
        f"Click the '{topic}' link.",
        "Verify the topic page loads.",
        "Assert the page heading or breadcrumb matches the topic.",
        "Assert at least one article or report card is visible.",
    ]
    return {"task_type": "rent_research_topic_link", "topic": topic, "steps": steps}

def rent_skip_to_content(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.rent.com'.",
        *_ui_hygiene(),
        "Locate the 'Skip to content' link at the top of the page.",
        "Click the link.",
        "Verify focus jumps to the main content area.",
        "Assert the main content is visible and keyboard focus is set correctly.",
    ]
    return {"task_type": "rent_skip_to_content", "steps": steps}

_TASK_GENERATORS: Dict[RENT_TASK_TYPES, Callable[[dict], dict]] = {
    "rent_search_city": rent_search_city,
    "rent_filter_price_range": rent_filter_price_range,
    "rent_filter_bed_bath": rent_filter_bed_bath,
    "rent_filter_property_type": rent_filter_property_type,
    "rent_popular_search": rent_popular_search,
    "rent_footer_navigation": rent_footer_navigation,
    "rent_research_category_nav": rent_research_category_nav,
    "rent_research_searchbox": rent_research_searchbox,
    "rent_research_report_open": rent_research_report_open,
    "rent_research_city_report": rent_research_city_report,
    "rent_research_see_more": rent_research_see_more,
    "rent_interactive_chart": rent_interactive_chart,
    "rent_contact_form_valid": rent_contact_form_valid,
    "rent_contact_form_invalid": rent_contact_form_invalid,
    "rent_accessibility_feedback": rent_accessibility_feedback,
    "rent_download_app": rent_download_app,
    "rent_social_media_link": rent_social_media_link,
    "rent_let_us_help_link": rent_let_us_help_link,
    "rent_research_topic_link": rent_research_topic_link,
    "rent_skip_to_content": rent_skip_to_content,
}

def generate_rent_task(task_type: RENT_TASK_TYPES, payload: dict) -> dict:
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
    items = list(RENT_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_rent_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)