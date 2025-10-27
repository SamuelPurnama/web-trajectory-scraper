import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

CRAIGSLIST_TASK_TYPES = Literal[
    "cl_search_category",
    "cl_filter_price_range",
    "cl_browse_city_site",
    "cl_language_switch",
    "cl_browse_event_calendar",
    "cl_browse_help_topic",
    "cl_browse_discussion_forum",
    "cl_browse_nearby_city",
    "cl_browse_jobs_category",
    "cl_browse_housing_category",
    "cl_browse_for_sale_category",
]

CRAIGSLIST_SAMPLING_CONFIG: Dict[CRAIGSLIST_TASK_TYPES, int] = {
    "cl_search_category": 10,
    "cl_filter_price_range": 10,
    "cl_browse_city_site": 10,
    "cl_language_switch": 10,
    "cl_browse_event_calendar": 10,
    "cl_browse_help_topic": 10,
    "cl_browse_discussion_forum": 10,
    "cl_browse_nearby_city": 10,
    "cl_browse_jobs_category": 10,
    "cl_browse_housing_category": 10,
    "cl_browse_for_sale_category": 10,
}

CL_CITIES = [
    "new york", "los angeles", "chicago", "houston", "phoenix", "philadelphia", "san antonio",
    "san diego", "dallas", "san jose", "austin", "jacksonville", "fort worth", "columbus",
    "charlotte", "san francisco", "indianapolis", "seattle", "denver", "washington dc",
    "boston", "el paso", "nashville", "detroit", "oklahoma city", "portland", "las vegas",
    "memphis", "louisville", "baltimore"
]

CL_NEARBY_CITIES = [
    "bellingham", "bend", "boise", "butte", "corvallis", "east oregon", "eugene", "great falls",
    "helena", "humboldt", "kalispell", "klamath falls", "lewiston", "medford", "missoula",
    "moses lake", "olympic pen", "oregon coast", "portland", "pullman-moscow", "redding",
    "roseburg", "salem", "siskiyou co", "skagit", "spokane", "susanville", "tri-cities",
    "wenatchee", "yakima"
]

CL_LANGUAGES = [
    "english", "dansk", "deutsch", "español", "français", "italiano", "português", "suomi",
    "svenska", "tiếng việt", "türkçe", "русский", "中文", "日本語", "한국말"
]

CL_CATEGORIES = [
    "housing", "jobs", "for sale", "services", "community", "gigs", "resumes", "discussion forums",
    "apts / housing", "housing swap", "housing wanted", "office / commercial", "parking / storage",
    "real estate for sale", "rooms / shared", "rooms wanted", "sublets / temporary", "vacation rentals",
    "antiques", "appliances", "arts+crafts", "atv/utv/sno", "auto parts", "aviation", "baby+kid",
    "barter", "beauty+hlth", "bike parts", "bikes", "boat parts", "boats", "books", "business",
    "cars+trucks", "cds/dvd/vhs", "cell phones", "clothes+acc", "collectibles", "computer parts",
    "computers", "electronics", "farm+garden", "free", "furniture", "garage sale", "general",
    "heavy equip", "household", "jewelry", "materials", "motorcycle parts", "motorcycles",
    "music instr", "photo+video", "rvs+camp", "sporting", "tickets", "tools", "toys+games",
    "trailers", "video gaming", "wanted", "wheels+tires"
]

CL_FORUMS = [
    "apple", "arts", "atheist", "autos", "beauty", "bikes", "celebs", "comp", "cosmos", "diet",
    "divorce", "dying", "eco", "feedbk", "film", "fixit", "food", "frugal", "gaming", "garden",
    "haiku", "help", "history", "housing", "jobs", "jokes", "legal", "manners", "marriage",
    "money", "music", "open", "parent", "pets", "philos", "photo", "politics", "psych", "recover",
    "religion", "rofo", "science", "spirit", "sports", "super", "tax", "travel", "tv", "vegan",
    "words", "writing"
]

CL_JOBS_CATEGORIES = [
    "accounting+finance", "admin / office", "arch / engineering", "art / media / design",
    "biotech / science", "business / mgmt", "customer service", "education", "etc / misc",
    "food / bev / hosp", "general labor", "government", "human resources", "legal / paralegal",
    "manufacturing", "marketing / pr / ad", "medical / health", "nonprofit sector", "real estate",
    "retail / wholesale", "sales / biz dev", "salon / spa / fitness", "security",
    "skilled trade / craft", "software / qa / dba", "systems / network", "technical support",
    "transport", "tv / film / video", "web / info design", "writing / editing"
]

CL_HOUSING_CATEGORIES = [
    "apts / housing", "housing swap", "housing wanted", "office / commercial", "parking / storage",
    "real estate for sale", "rooms / shared", "rooms wanted", "sublets / temporary", "vacation rentals"
]

CL_FOR_SALE_CATEGORIES = [
    "antiques", "appliances", "arts+crafts", "atv/utv/sno", "auto parts", "aviation", "baby+kid",
    "barter", "beauty+hlth", "bike parts", "bikes", "boat parts", "boats", "books", "business",
    "cars+trucks", "cds/dvd/vhs", "cell phones", "clothes+acc", "collectibles", "computer parts",
    "computers", "electronics", "farm+garden", "free", "furniture", "garage sale", "general",
    "heavy equip", "household", "jewelry", "materials", "motorcycle parts", "motorcycles",
    "music instr", "photo+video", "rvs+camp", "sporting", "tickets", "tools", "toys+games",
    "trailers", "video gaming", "wanted", "wheels+tires"
]

CL_PRICE_RANGES = [
    (0, 10), (10, 25), (25, 50), (50, 75), (75, 100), (100, 150), (150, 200), (200, 250),
    (250, 300), (300, 400), (400, 500), (500, 600), (600, 700), (700, 800), (800, 900),
    (900, 1000), (1000, 1500), (1500, 2000), (2000, 2500), (2500, 3000), (3000, 5000)
]

CL_SEARCH_TERMS = [
    "bike", "sofa", "apartment", "laptop", "desk", "car", "room", "dog", "cat", "table", "chair",
    "guitar", "camera", "printer", "washer", "dryer", "bed", "tv", "refrigerator", "books",
    "tickets", "tools", "motorcycle", "boat", "house", "job", "event", "concert", "garden", "lamp"
]

CL_EVENT_DAYS = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31
]

CL_HELP_TOPICS = [
    "help, faq, abuse, legal", "avoid scams & fraud", "personal safety tips", "about craigslist",
    "best-of-craigslist", "craigslist is hiring", "what's new", "system status", "craigslist charitable",
    "craig newmark philanthropies", "privacy", "terms", "safety", "app", "sitemap"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners if present.",
        "Do not submit any forms or post ads.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Craigslist", steps).model_dump()

def cl_search_category(_: dict) -> dict:
    term = random.choice(CL_SEARCH_TERMS)
    steps = [
        "Go to url 'https://craigslist.org/'.",
        *_ui_hygiene(),
        "Locate the search box labeled 'search craigslist'.",
        f"Type '{term}' and press Enter.",
        "Wait for the search results page to load.",
        f"Verify that the results page contains listings related to '{term}'.",
        "Assert that at least one result is shown.",
    ]
    return {
        "task_type": "cl_search_category",
        "search_term": term,
        "steps": steps,
        "assertion": f"Listings related to '{term}' are present in results.",
        "instruction": _instr(steps)
    }

def cl_filter_price_range(_: dict) -> dict:
    cat = random.choice(CL_FOR_SALE_CATEGORIES)
    minp, maxp = random.choice(CL_PRICE_RANGES)
    steps = [
        "Go to url 'https://craigslist.org/'.",
        *_ui_hygiene(),
        f"Click the 'for sale' link, then select '{cat}'.",
        "Wait for the category results page to load.",
        f"Locate and open the price filter.",
        f"Set minimum price to '{minp}' and maximum price to '{maxp}'.",
        "Apply the filter and wait for the page to refresh.",
        f"Verify that all visible listings have prices between ${minp} and ${maxp}.",
        "Assert that at least one filtered result is shown.",
    ]
    return {
        "task_type": "cl_filter_price_range",
        "category": cat,
        "min_price": minp,
        "max_price": maxp,
        "steps": steps,
        "assertion": f"All results are in the price range ${minp}-${maxp}.",
        "instruction": _instr(steps)
    }

def cl_browse_city_site(_: dict) -> dict:
    city = random.choice(CL_CITIES)
    steps = [
        "Go to url 'https://www.craigslist.org/about/sites'.",
        *_ui_hygiene(),
        f"Scroll to or search for the city link labeled '{city}'.",
        f"Click the '{city}' link.",
        "Wait for the local Craigslist site for that city to load.",
        f"Verify that the page header or title mentions '{city}'.",
    ]
    return {
        "task_type": "cl_browse_city_site",
        "city": city,
        "steps": steps,
        "assertion": f"Page title or header includes '{city}'.",
        "instruction": _instr(steps)
    }

def cl_language_switch(_: dict) -> dict:
    lang = random.choice(CL_LANGUAGES)
    steps = [
        "Go to url 'https://craigslist.org/'.",
        *_ui_hygiene(),
        "Locate the language dropdown (combobox) at the bottom or top of the page.",
        f"Open the dropdown and select '{lang}'.",
        "Wait for the page to reload or update.",
        f"Verify that the page interface is now displayed in '{lang}' (e.g., navigation or labels change).",
    ]
    return {
        "task_type": "cl_language_switch",
        "language": lang,
        "steps": steps,
        "assertion": f"UI text is updated to '{lang}'.",
        "instruction": _instr(steps)
    }

def cl_browse_event_calendar(_: dict) -> dict:
    day = random.choice(CL_EVENT_DAYS)
    steps = [
        "Go to url 'https://craigslist.org/'.",
        *_ui_hygiene(),
        "Locate and click the 'event calendar' link.",
        "Wait for the event calendar page to load.",
        f"Find and click the date '{day}' in the calendar.",
        "Wait for the events for that day to display.",
        f"Verify that events for the {day}th are shown or a message indicates no events.",
    ]
    return {
        "task_type": "cl_browse_event_calendar",
        "calendar_day": day,
        "steps": steps,
        "assertion": f"Events for day {day} are shown or 'no events' message appears.",
        "instruction": _instr(steps)
    }

def cl_browse_help_topic(_: dict) -> dict:
    topic = random.choice(CL_HELP_TOPICS)
    steps = [
        "Go to url 'https://craigslist.org/'.",
        *_ui_hygiene(),
        f"Scroll to the bottom or help section.",
        f"Click the link labeled '{topic}'.",
        "Wait for the help or info page to load.",
        f"Verify that the help page contains information about '{topic}'.",
    ]
    return {
        "task_type": "cl_browse_help_topic",
        "help_topic": topic,
        "steps": steps,
        "assertion": f"Help page includes info about '{topic}'.",
        "instruction": _instr(steps)
    }

def cl_browse_discussion_forum(_: dict) -> dict:
    forum = random.choice(CL_FORUMS)
    steps = [
        "Go to url 'https://craigslist.org/'.",
        *_ui_hygiene(),
        "Locate and click the 'discussion forums' link.",
        "Wait for the forums page to load.",
        f"Find and click the forum labeled '{forum}'.",
        "Wait for the forum thread list to load.",
        f"Verify that the forum page title or header includes '{forum}'.",
    ]
    return {
        "task_type": "cl_browse_discussion_forum",
        "forum": forum,
        "steps": steps,
        "assertion": f"Forum page header includes '{forum}'.",
        "instruction": _instr(steps)
    }

def cl_browse_nearby_city(_: dict) -> dict:
    city = random.choice(CL_NEARBY_CITIES)
    steps = [
        "Go to url 'https://craigslist.org/'.",
        *_ui_hygiene(),
        "Scroll to the 'nearby cl' section.",
        f"Click the link labeled '{city}'.",
        "Wait for the Craigslist site for that nearby city to load.",
        f"Verify that the page header or title mentions '{city}'.",
    ]
    return {
        "task_type": "cl_browse_nearby_city",
        "nearby_city": city,
        "steps": steps,
        "assertion": f"Page title or header includes '{city}'.",
        "instruction": _instr(steps)
    }

def cl_browse_jobs_category(_: dict) -> dict:
    job_cat = random.choice(CL_JOBS_CATEGORIES)
    steps = [
        "Go to url 'https://craigslist.org/'.",
        *_ui_hygiene(),
        "Locate and click the 'jobs' link.",
        f"On the jobs page, click the category '{job_cat}'.",
        "Wait for the job listings to load.",
        f"Verify that the category header or breadcrumbs include '{job_cat}'.",
        "Assert that at least one job listing is shown.",
    ]
    return {
        "task_type": "cl_browse_jobs_category",
        "jobs_category": job_cat,
        "steps": steps,
        "assertion": f"Header/breadcrumbs include '{job_cat}' and at least one listing is shown.",
        "instruction": _instr(steps)
    }

def cl_browse_housing_category(_: dict) -> dict:
    housing_cat = random.choice(CL_HOUSING_CATEGORIES)
    steps = [
        "Go to url 'https://craigslist.org/'.",
        *_ui_hygiene(),
        "Locate and click the 'housing' link.",
        f"On the housing page, click the category '{housing_cat}'.",
        "Wait for the listings to load.",
        f"Verify that the category header or breadcrumbs include '{housing_cat}'.",
        "Assert that at least one housing listing is shown.",
    ]
    return {
        "task_type": "cl_browse_housing_category",
        "housing_category": housing_cat,
        "steps": steps,
        "assertion": f"Header/breadcrumbs include '{housing_cat}' and at least one listing is shown.",
        "instruction": _instr(steps)
    }

def cl_browse_for_sale_category(_: dict) -> dict:
    sale_cat = random.choice(CL_FOR_SALE_CATEGORIES)
    steps = [
        "Go to url 'https://craigslist.org/'.",
        *_ui_hygiene(),
        "Locate and click the 'for sale' link.",
        f"On the for sale page, click the category '{sale_cat}'.",
        "Wait for the listings to load.",
        f"Verify that the category header or breadcrumbs include '{sale_cat}'.",
        "Assert that at least one for sale listing is shown.",
    ]
    return {
        "task_type": "cl_browse_for_sale_category",
        "for_sale_category": sale_cat,
        "steps": steps,
        "assertion": f"Header/breadcrumbs include '{sale_cat}' and at least one listing is shown.",
        "instruction": _instr(steps)
    }

_TASK_GENERATORS: Dict[CRAIGSLIST_TASK_TYPES, Callable[[dict], dict]] = {
    "cl_search_category": cl_search_category,
    "cl_filter_price_range": cl_filter_price_range,
    "cl_browse_city_site": cl_browse_city_site,
    "cl_language_switch": cl_language_switch,
    "cl_browse_event_calendar": cl_browse_event_calendar,
    "cl_browse_help_topic": cl_browse_help_topic,
    "cl_browse_discussion_forum": cl_browse_discussion_forum,
    "cl_browse_nearby_city": cl_browse_nearby_city,
    "cl_browse_jobs_category": cl_browse_jobs_category,
    "cl_browse_housing_category": cl_browse_housing_category,
    "cl_browse_for_sale_category": cl_browse_for_sale_category,
}

def generate_cl_task(task_type: CRAIGSLIST_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
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
                futures.append(ex.submit(generate_cl_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)