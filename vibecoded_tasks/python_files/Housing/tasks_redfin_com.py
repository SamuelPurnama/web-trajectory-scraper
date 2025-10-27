import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

REDFIN_TASK_TYPES = Literal[
    "redfin_property_search",
    "redfin_property_filter",
    "redfin_property_sort",
    "redfin_sell_inquiry",
    "redfin_schedule_consultation",
    "redfin_navigation_menu",
    "redfin_company_info_page",
    "redfin_app_download",
    "redfin_help_center",
    "redfin_legal_link",
    "redfin_social_link",
]

REDFIN_SAMPLING_CONFIG: Dict[REDFIN_TASK_TYPES, int] = {
    "redfin_property_search": 10,
    "redfin_property_filter": 10,
    "redfin_property_sort": 10,
    "redfin_sell_inquiry": 10,
    "redfin_schedule_consultation": 10,
    "redfin_navigation_menu": 10,
    "redfin_company_info_page": 10,
    "redfin_app_download": 10,
    "redfin_help_center": 10,
    "redfin_legal_link": 10,
    "redfin_social_link": 10,
}

CITIES = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
    "Boston, MA", "El Paso, TX", "Nashville, TN", "Detroit, MI", "Oklahoma City, OK",
    "Portland, OR", "Las Vegas, NV", "Memphis, TN", "Louisville, KY", "Baltimore, MD"
]

PROPERTY_TYPES = [
    "House", "Condo", "Townhouse", "Multi-Family", "Land", "Apartment", "Co-op", "Loft",
    "Mobile/Manufactured", "Farm", "Duplex", "Triplex", "Quadruplex", "Cottage", "Bungalow",
    "Cabin", "Villa", "Ranch", "Studio", "Penthouse", "Rowhouse", "Carriage House"
]

PRICE_RANGES = [
    (50000, 100000), (100000, 150000), (150000, 200000), (200000, 250000), (250000, 300000),
    (300000, 350000), (350000, 400000), (400000, 450000), (450000, 500000), (500000, 600000),
    (600000, 700000), (700000, 800000), (800000, 900000), (900000, 1000000), (1000000, 1200000),
    (1200000, 1400000), (1400000, 1600000), (1600000, 1800000), (1800000, 2000000), (2000000, 2500000),
    (2500000, 3000000)
]

BEDROOMS = list(range(1, 8))
BATHROOMS = list(range(1, 6))
SORT_OPTIONS = [
    "Newest Listings", "Price: Low to High", "Price: High to Low", "Beds", "Baths",
    "Square Feet", "Lot Size", "Open Houses", "Recently Sold", "Days on Redfin",
    "Year Built", "HOA Fee", "Walk Score", "Transit Score", "Bike Score",
    "Price Reduced", "Pending", "Foreclosures", "Fixer-Uppers", "Luxury", "Affordable"
]

SELL_INQUIRY_ADDRESSES = [
    "123 Main St, Anytown, NY", "456 Oak Ave, Los Angeles, CA", "789 Pine Rd, Chicago, IL",
    "101 Maple Dr, Houston, TX", "202 Elm St, Phoenix, AZ", "303 Cedar Ln, Philadelphia, PA",
    "404 Birch Blvd, San Antonio, TX", "505 Spruce Ct, San Diego, CA", "606 Walnut Pl, Dallas, TX",
    "707 Chestnut St, San Jose, CA", "808 Willow Ave, Austin, TX", "909 Aspen Rd, Jacksonville, FL",
    "111 Magnolia St, Fort Worth, TX", "222 Sycamore Dr, Columbus, OH", "333 Redwood Ln, Charlotte, NC",
    "444 Hickory Ct, San Francisco, CA", "555 Dogwood Pl, Indianapolis, IN", "666 Poplar St, Seattle, WA",
    "777 Palm Ave, Denver, CO", "888 Cypress Rd, Washington, DC", "999 Olive St, Boston, MA"
]

COMPANY_INFO_PAGES = [
    ("Why Redfin?", "/why-redfin"),
    ("Community Impact", "/impact"),
    ("Diversity & Inclusion", "/diversity-inclusion"),
    ("Life at Redfin", "/life-at-redfin"),
    ("Press", "/press"),
    ("Investors", "/investors"),
    ("Blog", "/blog"),
    ("Real Estate News", "/news"),
    ("Our Agents", "/real-estate-agents"),
    ("Buy with Redfin", "/buy"),
    ("Sell with Redfin", "/sell"),
    ("Contact Us", "/contact-us"),
    ("Help Center", "/help"),
    ("Careers", "/careers"),
    ("Advertise", "/advertise"),
    ("Get referrals", "/referrals"),
    ("Become an Agent", "/join"),
    ("Rocket Mortgage", "https://www.rocketmortgage.com/"),
    ("Rocket Close", "https://www.rocketclose.com/"),
    ("Rent.", "https://www.rent.com/"),
    ("ApartmentGuide", "https://www.apartmentguide.com/")
]

LEGAL_LINKS = [
    ("Terms of Use", "/terms-of-use"),
    ("Privacy Policy", "/privacy"),
    ("Do not sell or share my personal information", "/privacy#donotsell"),
    ("NY Standard Operating Procedures", "/ny-standard-operating-procedures"),
    ("New Mexico Real Estate Licenses", "/nm-real-estate-licenses"),
    ("Info About Brokerage Services", "/info-about-brokerage-services"),
    ("Consumer Protection Notice", "/consumer-protection-notice"),
    ("www.NMLSConsumerAccess.org", "https://www.nmlsconsumeraccess.org/"),
    ("Licensed in 50 states", "/licensed-in-50-states"),
    ("Equal Housing Opportunity", "/equal-housing-opportunity"),
    ("FAIR HOUSING POLICY", "/fair-housing-policy"),
    ("NEW YORK STATE FAIR HOUSING NOTICE", "/ny-fair-housing-notice"),
    ("1-844-759-7732", "tel:1-844-759-7732"),
]

SOCIAL_LINKS = [
    ("Redfin Facebook", "https://www.facebook.com/redfin"),
    ("Redfin Twitter", "https://twitter.com/redfin"),
    ("Redfin TikTok", "https://www.tiktok.com/@redfin"),
    ("Redfin Instagram", "https://www.instagram.com/redfin"),
]

APP_DOWNLOAD_LINKS = [
    ("Download the Redfin App on the Apple App Store", "https://apps.apple.com/app/redfin/id327962480"),
    ("Download the Redfin App from the Google Play Store", "https://play.google.com/store/apps/details?id=com.redfin.android"),
]

HELP_TOPICS = [
    ("Buying a Home", "/help/buying"),
    ("Selling a Home", "/help/selling"),
    ("Redfin App", "/help/app"),
    ("Mortgage", "/help/mortgage"),
    ("Account & Sign In", "/help/account"),
    ("Privacy & Security", "/help/privacy"),
    ("Contact Support", "/help/contact"),
    ("Home Value Estimates", "/help/home-value"),
    ("Touring Homes", "/help/tour"),
    ("Making Offers", "/help/offer"),
    ("Closing Process", "/help/closing"),
    ("Redfin Agents", "/help/agents"),
    ("Listing Your Home", "/help/listing"),
    ("Open Houses", "/help/open-house"),
    ("Foreclosures", "/help/foreclosure"),
    ("HOA Info", "/help/hoa"),
    ("Neighborhood Info", "/help/neighborhood"),
    ("School Info", "/help/schools"),
    ("Accessibility", "/help/accessibility"),
    ("International Buyers", "/help/international"),
    ("Moving & Relocation", "/help/moving"),
    ("Legal & Compliance", "/help/legal"),
]

def _rand_date(start_days=1, end_days=60) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, newsletter).",
        "Do not sign in, purchase, or submit personal information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Redfin", steps).model_dump()

def redfin_property_search(_: dict) -> dict:
    city = random.choice(CITIES)
    steps = [
        "Go to url 'https://www.redfin.com'.",
        *_ui_hygiene(),
        "Locate the searchbox labeled 'Search for properties'.",
        f"Enter '{city}' into the searchbox.",
        "Select the correct autocomplete suggestion for the city.",
        "Click the 'submit search' button.",
        "Wait for the results page to load.",
        f"Assert that listings for '{city.split(',')[0]}' are shown on the page.",
        "Assert that the URL contains the city or region name.",
    ]
    return {
        "task_type": "redfin_property_search",
        "city": city,
        "steps": steps,
        "assertions": [
            f"At least one property listing is displayed for '{city.split(',')[0]}'.",
            "URL contains the city or region name."
        ]
    }

def redfin_property_filter(_: dict) -> dict:
    city = random.choice(CITIES)
    property_type = random.choice(PROPERTY_TYPES)
    price_min, price_max = random.choice(PRICE_RANGES)
    beds = random.choice(BEDROOMS)
    baths = random.choice(BATHROOMS)
    steps = [
        "Go to url 'https://www.redfin.com'.",
        *_ui_hygiene(),
        "Locate the searchbox labeled 'Search for properties'.",
        f"Enter '{city}' and select the autocomplete suggestion.",
        "Click the 'submit search' button.",
        "Wait for the results page to load.",
        "Open the filters panel.",
        f"Set property type to '{property_type}'.",
        f"Set minimum price to ${price_min:,} and maximum price to ${price_max:,}.",
        f"Set bedrooms to '{beds}+' and bathrooms to '{baths}+'.",
        "Apply filters.",
        "Wait for filtered results to load.",
        "Assert that all visible listings match the selected property type and filters.",
        "Assert that the filter chips/tags reflect the selections.",
    ]
    return {
        "task_type": "redfin_property_filter",
        "city": city,
        "property_type": property_type,
        "price_min": price_min,
        "price_max": price_max,
        "bedrooms": beds,
        "bathrooms": baths,
        "steps": steps,
        "assertions": [
            "Listings match selected property type and filter criteria.",
            "Filter tags reflect the selected filters."
        ]
    }

def redfin_property_sort(_: dict) -> dict:
    city = random.choice(CITIES)
    sort_option = random.choice(SORT_OPTIONS)
    steps = [
        "Go to url 'https://www.redfin.com'.",
        *_ui_hygiene(),
        "Locate the searchbox labeled 'Search for properties'.",
        f"Enter '{city}' and select the autocomplete suggestion.",
        "Click the 'submit search' button.",
        "Wait for the results page to load.",
        "Locate the sort dropdown.",
        f"Select the sort option '{sort_option}'.",
        "Wait for the results to update.",
        f"Assert that the listings are sorted by '{sort_option}'.",
        "Check that the sort dropdown displays the selected option.",
    ]
    return {
        "task_type": "redfin_property_sort",
        "city": city,
        "sort_option": sort_option,
        "steps": steps,
        "assertions": [
            f"Listings are sorted by '{sort_option}'.",
            "Sort dropdown shows the selected option."
        ]
    }

def redfin_sell_inquiry(_: dict) -> dict:
    address = random.choice(SELL_INQUIRY_ADDRESSES)
    steps = [
        "Go to url 'https://www.redfin.com/sell'.",
        *_ui_hygiene(),
        "Locate the searchbox labeled 'Enter your street address'.",
        f"Enter '{address}' into the address field.",
        "Wait for the autocomplete to suggest the full address.",
        "Select the correct address suggestion.",
        "Click the button to proceed (e.g., 'Get started' or similar).",
        "Wait for the valuation or next step to appear.",
        "Assert that a home value estimate or next-step prompt is displayed.",
        "Assert that the address is shown on the page.",
    ]
    return {
        "task_type": "redfin_sell_inquiry",
        "address": address,
        "steps": steps,
        "assertions": [
            "Home value estimate or next-step prompt is visible.",
            "Entered address appears on the page."
        ]
    }

def redfin_schedule_consultation(_: dict) -> dict:
    address = random.choice(SELL_INQUIRY_ADDRESSES)
    steps = [
        "Go to url 'https://www.redfin.com/sell'.",
        *_ui_hygiene(),
        "Locate and click the button labeled 'Schedule a consultation'.",
        "Wait for the consultation scheduling form or modal to appear.",
        f"Enter '{address}' in the address field if prompted.",
        "Select a date at least 7 days from today.",
        "Select a time slot if available.",
        "Fill in any required non-personal fields (e.g., property type).",
        "Do not submit any personal contact information.",
        "Assert that the 'Next' or 'Continue' button is enabled.",
        "Assert that a confirmation or summary is shown after proceeding (if possible without personal info).",
    ]
    return {
        "task_type": "redfin_schedule_consultation",
        "address": address,
        "steps": steps,
        "assertions": [
            "'Next' or 'Continue' button is enabled after required fields.",
            "Consultation summary or confirmation is shown (if possible)."
        ]
    }

def redfin_navigation_menu(_: dict) -> dict:
    menu = random.choice([
        "Buy ▾", "Rent ▾", "Sell ▾", "Mortgage ▾", "Real Estate Agents ▾"
    ])
    menu_to_url = {
        "Buy ▾": "/buy",
        "Rent ▾": "/rent",
        "Sell ▾": "/sell",
        "Mortgage ▾": "/mortgage",
        "Real Estate Agents ▾": "/real-estate-agents"
    }
    steps = [
        "Go to url 'https://www.redfin.com'.",
        *_ui_hygiene(),
        f"Locate and click the navigation button labeled '{menu}'.",
        "Wait for the dropdown or menu to open.",
        "Click the first link in the dropdown.",
        "Wait for the target page to load.",
        f"Assert that the URL contains '{menu_to_url[menu]}'.",
        "Assert that the page heading or title matches the section.",
    ]
    return {
        "task_type": "redfin_navigation_menu",
        "menu": menu,
        "steps": steps,
        "assertions": [
            f"URL contains '{menu_to_url[menu]}'.",
            "Page heading matches the selected menu."
        ]
    }

def redfin_company_info_page(_: dict) -> dict:
    label, url = random.choice(COMPANY_INFO_PAGES)
    full_url = url if url.startswith("http") else f"https://www.redfin.com{url}"
    steps = [
        "Go to url 'https://www.redfin.com'.",
        *_ui_hygiene(),
        f"Scroll to the footer or navigation area.",
        f"Locate and click the link labeled '{label}'.",
        "Wait for the page to load.",
        f"Assert that the URL is '{full_url}' or contains the expected path.",
        f"Assert that the page heading or banner includes '{label.split()[0]}'.",
    ]
    return {
        "task_type": "redfin_company_info_page",
        "info_label": label,
        "info_url": full_url,
        "steps": steps,
        "assertions": [
            f"URL is '{full_url}' or contains the expected path.",
            f"Page heading/banner includes '{label.split()[0]}'."
        ]
    }

def redfin_app_download(_: dict) -> dict:
    label, url = random.choice(APP_DOWNLOAD_LINKS)
    steps = [
        "Go to url 'https://www.redfin.com'.",
        *_ui_hygiene(),
        "Scroll to the footer or app section.",
        f"Locate and click the link labeled '{label}'.",
        "Wait for the external app store page to open.",
        f"Assert that the new page URL starts with '{url.split('/')[0]}//{url.split('/')[2]}'.",
        f"Assert that the app name or Redfin branding is visible.",
    ]
    return {
        "task_type": "redfin_app_download",
        "app_label": label,
        "app_url": url,
        "steps": steps,
        "assertions": [
            f"External page URL starts with '{url.split('/')[0]}//{url.split('/')[2]}'.",
            "Redfin branding is visible on the app store page."
        ]
    }

def redfin_help_center(_: dict) -> dict:
    topic, url = random.choice(HELP_TOPICS)
    full_url = f"https://www.redfin.com{url}"
    steps = [
        "Go to url 'https://www.redfin.com/help'.",
        *_ui_hygiene(),
        f"Locate and click the help topic labeled '{topic}'.",
        "Wait for the help topic page to load.",
        f"Assert that the URL contains '{url}'.",
        f"Assert that the page heading or first paragraph includes '{topic.split()[0]}'.",
    ]
    return {
        "task_type": "redfin_help_center",
        "help_topic": topic,
        "help_url": full_url,
        "steps": steps,
        "assertions": [
            f"URL contains '{url}'.",
            f"Page heading or content includes '{topic.split()[0]}'."
        ]
    }

def redfin_legal_link(_: dict) -> dict:
    label, url = random.choice(LEGAL_LINKS)
    full_url = url if url.startswith("http") or url.startswith("tel:") else f"https://www.redfin.com{url}"
    steps = [
        "Go to url 'https://www.redfin.com'.",
        *_ui_hygiene(),
        "Scroll to the footer or legal section.",
        f"Locate and click the link labeled '{label}'.",
        "Wait for the legal or external page to load.",
        f"Assert that the URL is '{full_url}' or contains the expected path.",
        f"Assert that the page heading or content includes '{label.split()[0]}'.",
    ]
    return {
        "task_type": "redfin_legal_link",
        "legal_label": label,
        "legal_url": full_url,
        "steps": steps,
        "assertions": [
            f"URL is '{full_url}' or contains the expected path.",
            f"Page heading/content includes '{label.split()[0]}'."
        ]
    }

def redfin_social_link(_: dict) -> dict:
    label, url = random.choice(SOCIAL_LINKS)
    steps = [
        "Go to url 'https://www.redfin.com'.",
        *_ui_hygiene(),
        "Scroll to the footer or social media section.",
        f"Locate and click the link labeled '{label}'.",
        "Wait for the external social media page to load.",
        f"Assert that the new page URL starts with '{url.split('/')[0]}//{url.split('/')[2]}'.",
        f"Assert that the Redfin branding or profile is visible.",
    ]
    return {
        "task_type": "redfin_social_link",
        "social_label": label,
        "social_url": url,
        "steps": steps,
        "assertions": [
            f"External page URL starts with '{url.split('/')[0]}//{url.split('/')[2]}'.",
            "Redfin branding/profile is visible on the social page."
        ]
    }

_TASK_GENERATORS: Dict[REDFIN_TASK_TYPES, Callable[[dict], dict]] = {
    "redfin_property_search": redfin_property_search,
    "redfin_property_filter": redfin_property_filter,
    "redfin_property_sort": redfin_property_sort,
    "redfin_sell_inquiry": redfin_sell_inquiry,
    "redfin_schedule_consultation": redfin_schedule_consultation,
    "redfin_navigation_menu": redfin_navigation_menu,
    "redfin_company_info_page": redfin_company_info_page,
    "redfin_app_download": redfin_app_download,
    "redfin_help_center": redfin_help_center,
    "redfin_legal_link": redfin_legal_link,
    "redfin_social_link": redfin_social_link,
}

def generate_redfin_task(task_type: REDFIN_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = _instr(task["steps"])
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list):
        payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(REDFIN_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_redfin_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try:
                out.append(fut.result(timeout=timeout))
            except Exception:
                pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)