import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

CRAIGSLIST_TASK_TYPES = Literal[
    "craigslist_category_browse",
    "craigslist_search_keyword",
    "craigslist_filter_price_range",
    "craigslist_filter_neighborhood",
    "craigslist_posting_flow",
    "craigslist_help_center_topic",
    "craigslist_language_switch",
    "craigslist_nearby_site_navigation",
    "craigslist_event_calendar_browse",
    "craigslist_forum_browse",
    "craigslist_jobs_category_browse",
    "craigslist_services_category_browse",
    "craigslist_for_sale_category_browse"
]

CRAIGSLIST_SAMPLING_CONFIG: Dict[CRAIGSLIST_TASK_TYPES, int] = {
    "craigslist_category_browse": 10,
    "craigslist_search_keyword": 10,
    "craigslist_filter_price_range": 10,
    "craigslist_filter_neighborhood": 10,
    "craigslist_posting_flow": 10,
    "craigslist_help_center_topic": 10,
    "craigslist_language_switch": 10,
    "craigslist_nearby_site_navigation": 10,
    "craigslist_event_calendar_browse": 10,
    "craigslist_forum_browse": 10,
    "craigslist_jobs_category_browse": 10,
    "craigslist_services_category_browse": 10,
    "craigslist_for_sale_category_browse": 10,
}

CATEGORIES = [
    "housing", "jobs", "for sale", "services", "community", "gigs", "resumes",
    "apts / housing", "housing swap", "housing wanted", "office / commercial", "parking / storage",
    "real estate for sale", "rooms / shared", "rooms wanted", "sublets / temporary", "vacation rentals",
    "antiques", "appliances", "arts+crafts", "atv/utv/sno", "auto parts", "aviation", "baby+kid",
    "barter", "beauty+hlth", "bike parts", "bikes", "boat parts", "boats", "books", "business",
    "cars+trucks", "cds/dvd/vhs", "cell phones", "clothes+acc", "collectibles", "computer parts",
    "computers", "electronics", "farm+garden", "free", "furniture", "garage sale", "general",
    "heavy equip", "household", "jewelry", "materials", "motorcycle parts", "motorcycles",
    "music instr", "photo+video", "rvs+camp", "sporting", "tickets", "tools", "toys+games",
    "trailers", "video gaming", "wanted", "wheels+tires"
][:30]

SEARCH_TERMS = [
    "sofa", "bike", "apartment", "dog walker", "graphic designer", "roommate", "used car", "desk",
    "refrigerator", "guitar", "cat", "printer", "moving boxes", "air conditioner", "sublet",
    "babysitter", "lawn mower", "laptop", "wedding dress", "tickets", "kayak", "camera", "bookshelf",
    "washer", "dryer", "coffee table", "tv", "cell phone", "rug", "microwave"
][:30]

PRICE_RANGES = [
    (0, 50), (50, 100), (100, 200), (200, 300), (300, 400), (400, 500), (500, 600), (600, 700),
    (700, 800), (800, 900), (900, 1000), (1000, 1200), (1200, 1500), (1500, 2000), (2000, 2500),
    (2500, 3000), (3000, 4000), (4000, 5000), (5000, 7500), (7500, 10000), (10000, 15000), (15000, 20000)
][:22]

NEIGHBORHOODS = [
    "Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island", "Harlem", "Upper East Side",
    "Upper West Side", "Midtown", "Chelsea", "Greenwich Village", "East Village", "Lower East Side",
    "Williamsburg", "Bushwick", "Astoria", "Flushing", "Long Island City", "Park Slope", "Bedford-Stuyvesant",
    "Crown Heights", "Jackson Heights", "Forest Hills", "Riverdale", "SoHo", "Tribeca", "Chinatown",
    "Financial District", "DUMBO", "Sunset Park"
][:30]

LANGUAGES = [
    "english", "español", "français", "deutsch", "italiano", "português", "svenska", "suomi",
    "dansk", "русский", "中文", "日本語", "한국말", "tiếng việt", "türkçe"
][:15]

NEARBY_SITES = [
    "albany", "allentown", "baltimore", "binghamton", "catskills", "central nj", "delaware",
    "eastern ct", "eastern shore", "harrisburg", "hartford", "hudson valley", "jersey shore",
    "lancaster", "long island", "new haven", "north jersey", "northwest ct", "oneonta",
    "philadelphia", "poconos", "reading", "rhode island", "scranton", "south coast",
    "south jersey", "western mass", "williamsport", "worcester", "york"
][:30]

HELP_TOPICS = [
    "help, faq, abuse, legal", "avoid scams & fraud", "personal safety tips", "about craigslist",
    "best-of-craigslist", "craigslist is hiring", "what's new", "system status", "craigslist charitable",
    "craig newmark philanthropies", "privacy", "terms", "app", "sitemap", "safety"
][:15]

EVENT_DAYS = [
    "24", "25", "26", "27", "28", "29", "30", "31", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"
][:23]

FORUMS = [
    "apple", "arts", "atheist", "autos", "beauty", "bikes", "celebs", "comp", "cosmos", "diet",
    "divorce", "dying", "eco", "feedbk", "film", "fixit", "food", "frugal", "gaming", "garden",
    "haiku", "help", "history", "housing", "jobs", "jokes", "legal", "manners", "marriage", "money"
][:30]

JOBS_CATEGORIES = [
    "accounting+finance", "admin / office", "arch / engineering", "art / media / design", "biotech / science",
    "business / mgmt", "customer service", "education", "etc / misc", "food / bev / hosp", "general labor",
    "government", "human resources", "legal / paralegal", "manufacturing", "marketing / pr / ad",
    "medical / health", "nonprofit sector", "real estate", "retail / wholesale", "sales / biz dev",
    "salon / spa / fitness", "security", "skilled trade / craft", "software / qa / dba", "systems / network",
    "technical support", "transport", "tv / film / video", "web / info design", "writing / editing"
][:30]

SERVICES_CATEGORIES = [
    "automotive", "beauty", "cell/mobile", "computer", "creative", "cycle", "event", "farm+garden",
    "financial", "health/well", "household", "labor/move", "legal", "lessons", "marine", "pet",
    "real estate", "skilled trade", "sm biz ads", "travel/vac", "write/ed/tran"
][:21]

FOR_SALE_CATEGORIES = [
    "antiques", "appliances", "arts+crafts", "atv/utv/sno", "auto parts", "aviation", "baby+kid",
    "barter", "beauty+hlth", "bike parts", "bikes", "boat parts", "boats", "books", "business",
    "cars+trucks", "cds/dvd/vhs", "cell phones", "clothes+acc", "collectibles", "computer parts",
    "computers", "electronics", "farm+garden", "free", "furniture", "garage sale", "general",
    "heavy equip", "household", "jewelry"
][:30]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners if present (e.g., cookie consent, location prompts).",
        "Do not submit any personal or payment information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Craigslist", steps).model_dump()

def craigslist_category_browse(_: dict) -> dict:
    cat = random.choice(CATEGORIES)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        f"Click the '{cat}' link in the main navigation.",
        "Wait for the category page to load.",
        "Verify at least one listing is visible.",
        "Assert the page heading or breadcrumb includes the category name.",
    ]
    return {"task_type": "craigslist_category_browse", "category": cat, "steps": steps}

def craigslist_search_keyword(_: dict) -> dict:
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        "Focus the 'search craigslist' textbox.",
        f"Type '{term}' and press Enter.",
        "Wait for search results to appear.",
        "Verify at least one result contains the search term (case-insensitive).",
        "Assert the search term is reflected in the page title or URL.",
    ]
    return {"task_type": "craigslist_search_keyword", "search_term": term, "steps": steps}

def craigslist_filter_price_range(_: dict) -> dict:
    cat = random.choice(CATEGORIES)
    price_min, price_max = random.choice(PRICE_RANGES)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        f"Click the '{cat}' link in the main navigation.",
        "Wait for the category page to load.",
        "Locate the price filter inputs.",
        f"Set minimum price to '{price_min}' and maximum price to '{price_max}'.",
        "Apply the price filter.",
        "Verify all visible results have prices within the specified range.",
        "Assert the filter is reflected in the URL or filter summary.",
    ]
    return {"task_type": "craigslist_filter_price_range", "category": cat, "min_price": price_min, "max_price": price_max, "steps": steps}

def craigslist_filter_neighborhood(_: dict) -> dict:
    cat = random.choice(CATEGORIES)
    hood = random.choice(NEIGHBORHOODS)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        f"Click the '{cat}' link in the main navigation.",
        "Wait for the category page to load.",
        "Locate the neighborhood filter dropdown or list.",
        f"Select the neighborhood '{hood}'.",
        "Apply the filter.",
        "Verify all visible results are located in the selected neighborhood.",
        "Assert the filter is reflected in the URL or filter summary.",
    ]
    return {"task_type": "craigslist_filter_neighborhood", "category": cat, "neighborhood": hood, "steps": steps}

def craigslist_posting_flow(_: dict) -> dict:
    cat = random.choice(CATEGORIES)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        "Click the 'post' link in the header.",
        "Wait for the posting flow to begin.",
        f"Select '{cat}' as the posting category.",
        "Proceed to the next step.",
        "Verify the category is shown in the posting breadcrumb or summary.",
        "Do not submit any real information or complete the posting.",
    ]
    return {"task_type": "craigslist_posting_flow", "category": cat, "steps": steps}

def craigslist_help_center_topic(_: dict) -> dict:
    topic = random.choice(HELP_TOPICS)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        "Scroll to the bottom of the page.",
        f"Click the '{topic}' link.",
        "Wait for the help or FAQ page to load.",
        "Verify the page heading or content matches the selected topic.",
        "Assert at least one help article or section is visible.",
    ]
    return {"task_type": "craigslist_help_center_topic", "help_topic": topic, "steps": steps}

def craigslist_language_switch(_: dict) -> dict:
    lang = random.choice(LANGUAGES)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        "Locate the language selector combobox.",
        f"Select '{lang}' from the language dropdown.",
        "Wait for the page to reload or update.",
        "Verify that key navigation or headings are now in the selected language.",
        "Assert the language is reflected in the combobox value.",
    ]
    return {"task_type": "craigslist_language_switch", "language": lang, "steps": steps}

def craigslist_nearby_site_navigation(_: dict) -> dict:
    site = random.choice(NEARBY_SITES)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        "Scroll to the 'nearby cl' section.",
        f"Click the '{site}' link.",
        "Wait for the new craigslist site to load.",
        "Verify the URL and page heading reflect the selected nearby city.",
        "Assert at least one listing or navigation element is present.",
    ]
    return {"task_type": "craigslist_nearby_site_navigation", "nearby_site": site, "steps": steps}

def craigslist_event_calendar_browse(_: dict) -> dict:
    day = random.choice(EVENT_DAYS)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        "Locate and click the 'event calendar' link.",
        "Wait for the calendar page to load.",
        f"Click the day '{day}' in the calendar.",
        "Verify that events for the selected day are shown (if any).",
        "Assert the selected date is highlighted or reflected in the event list.",
    ]
    return {"task_type": "craigslist_event_calendar_browse", "calendar_day": day, "steps": steps}

def craigslist_forum_browse(_: dict) -> dict:
    forum = random.choice(FORUMS)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        "Scroll to the 'discussion forums' section.",
        f"Click the '{forum}' forum link.",
        "Wait for the forum page to load.",
        "Verify at least one discussion thread or post is visible.",
        "Assert the forum name is present in the page heading or breadcrumb.",
    ]
    return {"task_type": "craigslist_forum_browse", "forum": forum, "steps": steps}

def craigslist_jobs_category_browse(_: dict) -> dict:
    jobcat = random.choice(JOBS_CATEGORIES)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        "Click the 'jobs' link in the main navigation.",
        "Wait for the jobs page to load.",
        f"Click the '{jobcat}' subcategory link.",
        "Wait for the subcategory page to load.",
        "Verify at least one job listing is visible.",
        "Assert the subcategory name is present in the page heading or breadcrumb.",
    ]
    return {"task_type": "craigslist_jobs_category_browse", "job_category": jobcat, "steps": steps}

def craigslist_services_category_browse(_: dict) -> dict:
    svc = random.choice(SERVICES_CATEGORIES)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        "Click the 'services' link in the main navigation.",
        "Wait for the services page to load.",
        f"Click the '{svc}' subcategory link.",
        "Wait for the subcategory page to load.",
        "Verify at least one service listing is visible.",
        "Assert the subcategory name is present in the page heading or breadcrumb.",
    ]
    return {"task_type": "craigslist_services_category_browse", "service_category": svc, "steps": steps}

def craigslist_for_sale_category_browse(_: dict) -> dict:
    sale = random.choice(FOR_SALE_CATEGORIES)
    steps = [
        "Go to url 'https://newyork.craigslist.org'.",
        *_ui_hygiene(),
        "Click the 'for sale' link in the main navigation.",
        "Wait for the for sale page to load.",
        f"Click the '{sale}' subcategory link.",
        "Wait for the subcategory page to load.",
        "Verify at least one item listing is visible.",
        "Assert the subcategory name is present in the page heading or breadcrumb.",
    ]
    return {"task_type": "craigslist_for_sale_category_browse", "for_sale_category": sale, "steps": steps}

_TASK_GENERATORS: Dict[CRAIGSLIST_TASK_TYPES, Callable[[dict], dict]] = {
    "craigslist_category_browse": craigslist_category_browse,
    "craigslist_search_keyword": craigslist_search_keyword,
    "craigslist_filter_price_range": craigslist_filter_price_range,
    "craigslist_filter_neighborhood": craigslist_filter_neighborhood,
    "craigslist_posting_flow": craigslist_posting_flow,
    "craigslist_help_center_topic": craigslist_help_center_topic,
    "craigslist_language_switch": craigslist_language_switch,
    "craigslist_nearby_site_navigation": craigslist_nearby_site_navigation,
    "craigslist_event_calendar_browse": craigslist_event_calendar_browse,
    "craigslist_forum_browse": craigslist_forum_browse,
    "craigslist_jobs_category_browse": craigslist_jobs_category_browse,
    "craigslist_services_category_browse": craigslist_services_category_browse,
    "craigslist_for_sale_category_browse": craigslist_for_sale_category_browse,
}

def generate_craigslist_task(task_type: CRAIGSLIST_TASK_TYPES, payload: dict) -> dict:
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
    items = list(CRAIGSLIST_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_craigslist_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)