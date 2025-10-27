import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

CRAIGSLIST_CATEGORIES = [
    "apts / housing", "housing swap", "housing wanted", "office / commercial", "parking / storage", "real estate for sale", "rooms / shared", "rooms wanted", "sublets / temporary", "vacation rentals",
    "antiques", "appliances", "arts+crafts", "atv/utv/sno", "auto parts", "aviation", "baby+kid", "barter", "beauty+hlth", "bike parts", "bikes", "boat parts", "boats", "books", "business", "cars+trucks",
    "cds/dvd/vhs", "cell phones", "clothes+acc", "collectibles", "computer parts", "computers", "electronics", "farm+garden", "free", "furniture", "garage sale", "general", "heavy equip", "household",
    "jewelry", "materials", "motorcycle parts", "motorcycles", "music instr", "photo+video", "rvs+camp", "sporting", "tickets", "tools", "toys+games", "trailers", "video gaming", "wanted", "wheels+tires"
]
CRAIGSLIST_JOBS = [
    "accounting+finance", "admin / office", "arch / engineering", "art / media / design", "biotech / science", "business / mgmt", "customer service", "education", "etc / misc", "food / bev / hosp",
    "general labor", "government", "human resources", "legal / paralegal", "manufacturing", "marketing / pr / ad", "medical / health", "nonprofit sector", "real estate", "retail / wholesale",
    "sales / biz dev", "salon / spa / fitness", "security", "skilled trade / craft", "software / qa / dba", "systems / network", "technical support", "transport", "tv / film / video", "web / info design",
    "writing / editing"
]
CRAIGSLIST_SERVICES = [
    "automotive", "beauty", "cell/mobile", "computer", "creative", "cycle", "event", "farm+garden", "financial", "health/well", "household", "labor/move", "legal", "lessons", "marine", "pet",
    "real estate", "skilled trade", "sm biz ads", "travel/vac", "write/ed/tran"
]
CRAIGSLIST_COMMUNITY = [
    "activities", "artists", "childcare", "classes", "events", "general", "groups", "local news", "lost+found", "missed connections", "musicians", "pets", "politics", "rants & raves", "rideshare", "volunteers"
]
CRAIGSLIST_FORUMS = [
    "apple", "arts", "atheist", "autos", "beauty", "bikes", "celebs", "comp", "cosmos", "diet", "divorce", "dying", "eco", "feedbk", "film", "fixit", "food", "frugal", "gaming", "garden", "haiku", "help",
    "history", "housing", "jobs", "jokes", "legal", "manners", "marriage", "money", "music", "open", "parent", "pets", "philos", "photo", "politics", "psych", "recover", "religion", "rofo", "science",
    "spirit", "sports", "super", "tax", "travel", "tv", "vegan", "words", "writing"
]
CRAIGSLIST_GIGS = [
    "computer", "creative", "crew", "domestic", "event", "labor", "talent", "writing"
]
CRAIGSLIST_LANGUAGES = [
    "dansk", "deutsch", "english", "español", "français", "italiano", "português", "suomi", "svenska", "tiếng việt", "türkçe", "русский", "中文", "日本語", "한국말"
]
CRAIGSLIST_NEARBY_CL = [
    "bakersfield", "chico", "fresno", "gold country", "hanford", "humboldt", "inland empire", "klamath falls", "las vegas", "los angeles", "medford", "mendocino co", "merced", "modesto", "monterey",
    "orange co", "palm springs", "redding", "reno", "roseburg", "sacramento", "san luis obispo", "santa barbara", "santa maria", "siskiyou co", "stockton", "susanville", "ventura", "visalia-tulare", "yuba-sutter"
]
CRAIGSLIST_SEARCH_TERMS = [
    "bicycle", "sofa", "laptop", "roommate", "dog", "car", "desk", "guitar", "printer", "camera", "table", "bed", "apartment", "house", "job", "event", "tickets", "garden", "tools", "books", "music", "tv",
    "refrigerator", "washer", "dryer", "motorcycle", "boat", "free", "collectibles", "art", "plants"
]
CRAIGSLIST_PRICE_RANGES = [
    (0, 50), (50, 100), (100, 200), (200, 300), (300, 400), (400, 500), (500, 600), (600, 700), (700, 800), (800, 900), (900, 1000), (1000, 1200), (1200, 1500), (1500, 1800), (1800, 2000),
    (2000, 2500), (2500, 3000), (3000, 4000), (4000, 5000), (5000, 10000)
]
CRAIGSLIST_SORT_ORDERS = ["newest", "price_asc", "price_desc", "relevance"]
CRAIGSLIST_REGIONS = ["sfc", "eby", "sby", "nby", "pen", "scz"]
CRAIGSLIST_CALENDAR_DAYS = [str(i) for i in range(1, 32)]
CRAIGSLIST_FAQS = [
    "help, faq, abuse, legal", "avoid scams & fraud", "personal safety tips", "about craigslist", "best-of-craigslist", "craigslist is hiring", "what's new", "system status", "craigslist charitable",
    "craig newmark philanthropies"
]

CRAIGSLIST_TASK_TYPES = Literal[
    "craigslist_category_search",
    "craigslist_job_search",
    "craigslist_post_to_category",
    "craigslist_filter_price_range",
    "craigslist_sort_results",
    "craigslist_language_switch",
    "craigslist_nearby_cl_navigation",
    "craigslist_calendar_event_navigation",
    "craigslist_faq_help_navigation",
    "craigslist_gigs_search"
]

CRAIGSLIST_SAMPLING_CONFIG: Dict[CRAIGSLIST_TASK_TYPES, int] = {
    "craigslist_category_search": 10,
    "craigslist_job_search": 10,
    "craigslist_post_to_category": 10,
    "craigslist_filter_price_range": 10,
    "craigslist_sort_results": 10,
    "craigslist_language_switch": 10,
    "craigslist_nearby_cl_navigation": 10,
    "craigslist_calendar_event_navigation": 10,
    "craigslist_faq_help_navigation": 10,
    "craigslist_gigs_search": 10,
}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, location prompts) if present.",
        "Do not submit any real personal information or complete any purchase.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Craigslist", steps).model_dump()

def craigslist_category_search(_: dict) -> dict:
    category = random.choice(CRAIGSLIST_CATEGORIES)
    search_term = random.choice(CRAIGSLIST_SEARCH_TERMS)
    region = random.choice(CRAIGSLIST_REGIONS)
    steps = [
        "Go to url 'https://sfbay.craigslist.org'.",
        *_ui_hygiene(),
        f"Click the region button labeled '{region}' if not already selected.",
        f"Click the category link labeled '{category}'.",
        f"In the search box labeled 'search craigslist', type '{search_term}'.",
        "Press Enter or click the search button.",
        "Wait for results to load.",
        f"Verify that the results page shows listings relevant to '{search_term}' in '{category}'.",
        "Assert that at least one result is shown.",
        "Do not contact any posters or submit forms.",
    ]
    return {
        "task_type": "craigslist_category_search",
        "category": category,
        "search_term": search_term,
        "region": region,
        "steps": steps
    }

def craigslist_job_search(_: dict) -> dict:
    job_cat = random.choice(CRAIGSLIST_JOBS)
    search_term = random.choice(CRAIGSLIST_SEARCH_TERMS)
    region = random.choice(CRAIGSLIST_REGIONS)
    steps = [
        "Go to url 'https://sfbay.craigslist.org'.",
        *_ui_hygiene(),
        f"Click the region button labeled '{region}' if not already selected.",
        "Click the 'jobs' link.",
        f"Click the job category link labeled '{job_cat}'.",
        f"In the search box labeled 'search craigslist', type '{search_term}'.",
        "Press Enter or click the search button.",
        "Wait for results to load.",
        f"Verify that the results page shows job listings relevant to '{search_term}' in '{job_cat}'.",
        "Assert that at least one job result is shown.",
        "Do not apply or submit any information.",
    ]
    return {
        "task_type": "craigslist_job_search",
        "job_category": job_cat,
        "search_term": search_term,
        "region": region,
        "steps": steps
    }

def craigslist_post_to_category(_: dict) -> dict:
    category = random.choice(CRAIGSLIST_CATEGORIES)
    region = random.choice(CRAIGSLIST_REGIONS)
    steps = [
        "Go to url 'https://sfbay.craigslist.org'.",
        *_ui_hygiene(),
        f"Click the region button labeled '{region}' if not already selected.",
        "Click the 'post' link (icon or text).",
        f"Select the category '{category}' from the list.",
        "Verify that the posting form loads for the selected category.",
        "Do not enter any real data or submit the form.",
        "Assert that the form fields for title, description, and price (if applicable) are present.",
    ]
    return {
        "task_type": "craigslist_post_to_category",
        "category": category,
        "region": region,
        "steps": steps
    }

def craigslist_filter_price_range(_: dict) -> dict:
    category = random.choice(CRAIGSLIST_CATEGORIES)
    region = random.choice(CRAIGSLIST_REGIONS)
    price_min, price_max = random.choice(CRAIGSLIST_PRICE_RANGES)
    steps = [
        "Go to url 'https://sfbay.craigslist.org'.",
        *_ui_hygiene(),
        f"Click the region button labeled '{region}' if not already selected.",
        f"Click the category link labeled '{category}'.",
        "Wait for the category page to load.",
        f"Locate and use the price filter to set minimum price to '{price_min}' and maximum price to '{price_max}'.",
        "Apply the filter.",
        "Wait for results to update.",
        f"Verify that all shown listings have prices within the range ${price_min} - ${price_max}.",
        "Assert that at least one result is shown.",
    ]
    return {
        "task_type": "craigslist_filter_price_range",
        "category": category,
        "region": region,
        "price_min": price_min,
        "price_max": price_max,
        "steps": steps
    }

def craigslist_sort_results(_: dict) -> dict:
    category = random.choice(CRAIGSLIST_CATEGORIES)
    region = random.choice(CRAIGSLIST_REGIONS)
    sort_order = random.choice(CRAIGSLIST_SORT_ORDERS)
    steps = [
        "Go to url 'https://sfbay.craigslist.org'.",
        *_ui_hygiene(),
        f"Click the region button labeled '{region}' if not already selected.",
        f"Click the category link labeled '{category}'.",
        "Wait for the category page to load.",
        f"Locate and use the sort dropdown to select '{sort_order}'.",
        "Wait for results to update.",
        f"Verify that the results are sorted by '{sort_order}'.",
        "Assert that at least one result is shown.",
    ]
    return {
        "task_type": "craigslist_sort_results",
        "category": category,
        "region": region,
        "sort_order": sort_order,
        "steps": steps
    }

def craigslist_language_switch(_: dict) -> dict:
    language = random.choice(CRAIGSLIST_LANGUAGES)
    steps = [
        "Go to url 'https://sfbay.craigslist.org'.",
        *_ui_hygiene(),
        "Locate the language combobox (dropdown) at the bottom or top of the page.",
        f"Select the language '{language}' from the dropdown.",
        "Wait for the page to reload or update.",
        f"Verify that the interface language has changed to '{language}'.",
        "Assert that at least one major UI label (e.g., 'search craigslist') is translated.",
    ]
    return {
        "task_type": "craigslist_language_switch",
        "language": language,
        "steps": steps
    }

def craigslist_nearby_cl_navigation(_: dict) -> dict:
    nearby = random.choice(CRAIGSLIST_NEARBY_CL)
    steps = [
        "Go to url 'https://sfbay.craigslist.org'.",
        *_ui_hygiene(),
        "Scroll to the 'nearby cl' section.",
        f"Click the link labeled '{nearby}'.",
        "Wait for the new craigslist region page to load.",
        f"Verify that the page title or header includes '{nearby}'.",
        "Assert that the URL contains the region code or name for '{nearby}'.",
    ]
    return {
        "task_type": "craigslist_nearby_cl_navigation",
        "nearby_cl": nearby,
        "steps": steps
    }

def craigslist_calendar_event_navigation(_: dict) -> dict:
    day = random.choice(CRAIGSLIST_CALENDAR_DAYS)
    steps = [
        "Go to url 'https://sfbay.craigslist.org'.",
        *_ui_hygiene(),
        "Locate the calendar widget on the main page.",
        f"Click the link for the day '{day}'.",
        "Wait for the event listings for that day to load.",
        f"Verify that the results page or section shows events for day '{day}'.",
        "Assert that at least one event is listed, or a 'no events' message is displayed.",
    ]
    return {
        "task_type": "craigslist_calendar_event_navigation",
        "calendar_day": day,
        "steps": steps
    }

def craigslist_faq_help_navigation(_: dict) -> dict:
    faq = random.choice(CRAIGSLIST_FAQS)
    steps = [
        "Go to url 'https://sfbay.craigslist.org'.",
        *_ui_hygiene(),
        f"Scroll to or locate the link labeled '{faq}'.",
        f"Click the link labeled '{faq}'.",
        "Wait for the help/FAQ page to load.",
        f"Verify that the page contains information or content about '{faq}'.",
        "Assert that at least one FAQ or help article is visible.",
    ]
    return {
        "task_type": "craigslist_faq_help_navigation",
        "faq": faq,
        "steps": steps
    }

def craigslist_gigs_search(_: dict) -> dict:
    gig_cat = random.choice(CRAIGSLIST_GIGS)
    search_term = random.choice(CRAIGSLIST_SEARCH_TERMS)
    region = random.choice(CRAIGSLIST_REGIONS)
    steps = [
        "Go to url 'https://sfbay.craigslist.org'.",
        *_ui_hygiene(),
        f"Click the region button labeled '{region}' if not already selected.",
        "Click the 'gigs' link.",
        f"Click the gig category link labeled '{gig_cat}'.",
        f"In the search box labeled 'search craigslist', type '{search_term}'.",
        "Press Enter or click the search button.",
        "Wait for results to load.",
        f"Verify that the results page shows gig listings relevant to '{search_term}' in '{gig_cat}'.",
        "Assert that at least one gig result is shown.",
        "Do not apply or submit any information.",
    ]
    return {
        "task_type": "craigslist_gigs_search",
        "gig_category": gig_cat,
        "search_term": search_term,
        "region": region,
        "steps": steps
    }

_TASK_GENERATORS: Dict[CRAIGSLIST_TASK_TYPES, Callable[[dict], dict]] = {
    "craigslist_category_search": craigslist_category_search,
    "craigslist_job_search": craigslist_job_search,
    "craigslist_post_to_category": craigslist_post_to_category,
    "craigslist_filter_price_range": craigslist_filter_price_range,
    "craigslist_sort_results": craigslist_sort_results,
    "craigslist_language_switch": craigslist_language_switch,
    "craigslist_nearby_cl_navigation": craigslist_nearby_cl_navigation,
    "craigslist_calendar_event_navigation": craigslist_calendar_event_navigation,
    "craigslist_faq_help_navigation": craigslist_faq_help_navigation,
    "craigslist_gigs_search": craigslist_gigs_search,
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