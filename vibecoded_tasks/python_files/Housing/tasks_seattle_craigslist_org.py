import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

CRAIGSLIST_TASK_TYPES = Literal[
    "craigslist_search_category",
    "craigslist_filter_price_range",
    "craigslist_search_keyword",
    "craigslist_browse_nearby_city",
    "craigslist_view_posting_details",
    "craigslist_language_switch",
    "craigslist_navigate_help_topic",
    "craigslist_browse_event_calendar",
    "craigslist_browse_discussion_forum",
    "craigslist_browse_subcategory",
]

CRAIGSLIST_SAMPLING_CONFIG: Dict[CRAIGSLIST_TASK_TYPES, int] = {
    "craigslist_search_category": 10,
    "craigslist_filter_price_range": 10,
    "craigslist_search_keyword": 10,
    "craigslist_browse_nearby_city": 10,
    "craigslist_view_posting_details": 10,
    "craigslist_language_switch": 10,
    "craigslist_navigate_help_topic": 10,
    "craigslist_browse_event_calendar": 10,
    "craigslist_browse_discussion_forum": 10,
    "craigslist_browse_subcategory": 10,
}

CATEGORIES = [
    "housing", "jobs", "for sale", "services", "community", "gigs", "resumes",
    "apts / housing", "rooms / shared", "real estate for sale", "parking / storage",
    "office / commercial", "housing swap", "housing wanted", "sublets / temporary",
    "vacation rentals", "antiques", "appliances", "arts+crafts", "atv/utv/sno",
    "auto parts", "aviation", "baby+kid", "barter", "beauty+hlth", "bike parts",
    "bikes", "boat parts", "boats", "books", "business", "cars+trucks", "cds/dvd/vhs",
    "cell phones", "clothes+acc", "collectibles", "computer parts", "computers",
    "electronics", "farm+garden", "free", "furniture", "garage sale", "general",
    "heavy equip", "household", "jewelry", "materials", "motorcycle parts",
    "motorcycles", "music instr", "photo+video", "rvs+camp", "sporting", "tickets",
    "tools", "toys+games", "trailers", "video gaming", "wanted", "wheels+tires"
][:30]

PRICE_RANGES = [
    (0, 50), (50, 100), (100, 200), (200, 300), (300, 400), (400, 500), (500, 600),
    (600, 700), (700, 800), (800, 900), (900, 1000), (1000, 1200), (1200, 1500),
    (1500, 2000), (2000, 2500), (2500, 3000), (3000, 4000), (4000, 5000), (5000, 7500),
    (7500, 10000), (10000, 20000), (20000, 50000)
][:22]

KEYWORDS = [
    "bicycle", "sofa", "apartment", "dog", "laptop", "desk", "roommate", "car",
    "guitar", "printer", "garden", "kayak", "tickets", "job", "babysitter", "moving",
    "camera", "washer", "dryer", "table", "cat", "motorcycle", "boat", "books",
    "tools", "tv", "refrigerator", "wedding", "event", "volunteer"
][:30]

NEARBY_CITIES = [
    "bellingham", "bend", "boise", "butte", "corvallis", "east oregon", "eugene",
    "great falls", "helena", "humboldt", "kalispell", "klamath falls", "lewiston",
    "medford", "missoula", "moses lake", "olympic pen", "oregon coast", "portland",
    "pullman-moscow", "redding", "roseburg", "salem", "siskiyou co", "skagit",
    "spokane", "susanville", "tri-cities", "wenatchee", "yakima"
][:28]

LANGUAGES = [
    "dansk", "deutsch", "english", "español", "français", "italiano", "português",
    "suomi", "svenska", "tiếng việt", "türkçe", "русский", "中文", "日本語", "한국말"
][:15]

HELP_TOPICS = [
    "help, faq, abuse, legal", "avoid scams & fraud", "personal safety tips",
    "about craigslist", "best-of-craigslist", "craigslist is hiring", "what's new",
    "system status", "craigslist charitable", "craig newmark philanthropies",
    "privacy", "terms", "app", "sitemap", "safety"
][:15]

EVENT_DAYS = [
    "24", "25", "26", "27", "28", "29", "30", "31", "1", "2", "3", "4", "5", "6",
    "7", "8", "9", "10", "11", "12", "13", "14", "15"
][:22]

FORUMS = [
    "apple", "arts", "atheist", "autos", "beauty", "bikes", "celebs", "comp",
    "cosmos", "diet", "divorce", "dying", "eco", "feedbk", "film", "fixit", "food",
    "frugal", "gaming", "garden", "haiku", "help", "history", "housing", "jobs",
    "jokes", "legal", "manners", "marriage", "money", "music", "open", "parent",
    "pets", "philos", "photo", "politics", "psych", "recover", "religion", "rofo",
    "science", "spirit", "sports", "super", "tax", "travel", "tv", "vegan", "words",
    "writing"
][:50]

SUBCATEGORIES = [
    "apts / housing", "housing swap", "housing wanted", "office / commercial",
    "parking / storage", "real estate for sale", "rooms / shared", "rooms wanted",
    "sublets / temporary", "vacation rentals", "antiques", "appliances", "arts+crafts",
    "atv/utv/sno", "auto parts", "aviation", "baby+kid", "barter", "beauty+hlth",
    "bike parts", "bikes", "boat parts", "boats", "books", "business", "cars+trucks",
    "cds/dvd/vhs", "cell phones", "clothes+acc", "collectibles"
][:30]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie notices, alerts).",
        "Do not submit or post any real information; only view or search.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Craigslist", steps).model_dump()

def craigslist_search_category(_: dict) -> dict:
    category = random.choice(CATEGORIES)
    steps = [
        "Go to url 'https://seattle.craigslist.org'.",
        *_ui_hygiene(),
        f"Locate and click the '{category}' category link.",
        "Verify the category page loads and displays a list of postings.",
        "Assert the URL contains the category name or abbreviation.",
    ]
    return {
        "task_type": "craigslist_search_category",
        "category": category,
        "steps": steps,
        "assertion": f"Page shows postings for '{category}' and URL contains '{category.split()[0].replace('/', '').replace(' ', '')}'."
    }

def craigslist_filter_price_range(_: dict) -> dict:
    category = random.choice(CATEGORIES)
    price_min, price_max = random.choice(PRICE_RANGES)
    steps = [
        "Go to url 'https://seattle.craigslist.org'.",
        *_ui_hygiene(),
        f"Click the '{category}' category link.",
        "Locate the price filter fields on the category page.",
        f"Enter minimum price '{price_min}' and maximum price '{price_max}'.",
        "Apply the price filter.",
        "Verify that all visible postings have prices within the specified range.",
        "Assert that at least one posting is shown, or a 'no results' message is displayed.",
    ]
    return {
        "task_type": "craigslist_filter_price_range",
        "category": category,
        "price_min": price_min,
        "price_max": price_max,
        "steps": steps,
        "assertion": f"All postings shown are between ${price_min} and ${price_max}, or 'no results' is displayed."
    }

def craigslist_search_keyword(_: dict) -> dict:
    keyword = random.choice(KEYWORDS)
    steps = [
        "Go to url 'https://seattle.craigslist.org'.",
        *_ui_hygiene(),
        "Focus the 'search craigslist' textbox.",
        f"Type '{keyword}' and press Enter.",
        "Verify the search results page loads.",
        f"Assert that at least one result contains '{keyword}' in the title or description, or 'no results' is displayed.",
    ]
    return {
        "task_type": "craigslist_search_keyword",
        "keyword": keyword,
        "steps": steps,
        "assertion": f"Results contain '{keyword}' or show a 'no results' message."
    }

def craigslist_browse_nearby_city(_: dict) -> dict:
    city = random.choice(NEARBY_CITIES)
    steps = [
        "Go to url 'https://seattle.craigslist.org'.",
        *_ui_hygiene(),
        "Scroll to the 'nearby cl' section.",
        f"Click the link for '{city}'.",
        "Verify that the new page loads for the selected city.",
        "Assert the URL contains the city's name or abbreviation.",
    ]
    return {
        "task_type": "craigslist_browse_nearby_city",
        "city": city,
        "steps": steps,
        "assertion": f"URL contains '{city.replace(' ', '').replace('-', '')}'."
    }

def craigslist_view_posting_details(_: dict) -> dict:
    category = random.choice(CATEGORIES)
    steps = [
        "Go to url 'https://seattle.craigslist.org'.",
        *_ui_hygiene(),
        f"Click the '{category}' category link.",
        "Wait for the list of postings to load.",
        "Click the first posting in the list.",
        "Verify the posting details page loads.",
        "Assert that the page shows a title, description, and at least one contact or reply option.",
    ]
    return {
        "task_type": "craigslist_view_posting_details",
        "category": category,
        "steps": steps,
        "assertion": "Posting details page shows a title, description, and contact/reply option."
    }

def craigslist_language_switch(_: dict) -> dict:
    language = random.choice(LANGUAGES)
    steps = [
        "Go to url 'https://seattle.craigslist.org'.",
        *_ui_hygiene(),
        "Locate the language dropdown (combobox) at the bottom of the page.",
        f"Select '{language}' from the dropdown.",
        "Verify that the site interface updates to the selected language.",
        "Assert that navigation labels or footer text appear in the chosen language.",
    ]
    return {
        "task_type": "craigslist_language_switch",
        "language": language,
        "steps": steps,
        "assertion": f"Site interface updates to '{language}'."
    }

def craigslist_navigate_help_topic(_: dict) -> dict:
    topic = random.choice(HELP_TOPICS)
    steps = [
        "Go to url 'https://seattle.craigslist.org'.",
        *_ui_hygiene(),
        "Scroll to the bottom of the page.",
        f"Click the '{topic}' link.",
        "Verify the help or info page loads.",
        "Assert that the page contains relevant information or FAQ for the selected topic.",
    ]
    return {
        "task_type": "craigslist_navigate_help_topic",
        "topic": topic,
        "steps": steps,
        "assertion": f"Help/info page for '{topic}' is shown."
    }

def craigslist_browse_event_calendar(_: dict) -> dict:
    day = random.choice(EVENT_DAYS)
    steps = [
        "Go to url 'https://seattle.craigslist.org'.",
        *_ui_hygiene(),
        "Locate and click the 'event calendar' link.",
        "Wait for the calendar page to load.",
        f"Click on the date '{day}' in the calendar.",
        "Verify that events for the selected date are displayed, or a 'no events' message appears.",
        "Assert that events are listed for the chosen date, or 'no events' is shown.",
    ]
    return {
        "task_type": "craigslist_browse_event_calendar",
        "day": day,
        "steps": steps,
        "assertion": f"Events or 'no events' message for day '{day}' are shown."
    }

def craigslist_browse_discussion_forum(_: dict) -> dict:
    forum = random.choice(FORUMS)
    steps = [
        "Go to url 'https://seattle.craigslist.org'.",
        *_ui_hygiene(),
        "Locate and click the 'discussion forums' link.",
        f"Select the '{forum}' forum from the list.",
        "Verify that the forum page loads and displays threads.",
        "Assert that at least one thread is visible, or a 'no threads' message appears.",
    ]
    return {
        "task_type": "craigslist_browse_discussion_forum",
        "forum": forum,
        "steps": steps,
        "assertion": f"Forum '{forum}' page shows threads or 'no threads' message."
    }

def craigslist_browse_subcategory(_: dict) -> dict:
    subcategory = random.choice(SUBCATEGORIES)
    steps = [
        "Go to url 'https://seattle.craigslist.org'.",
        *_ui_hygiene(),
        f"Locate and click the '{subcategory}' subcategory link.",
        "Verify the subcategory page loads and displays a list of postings.",
        "Assert the URL contains the subcategory's abbreviation or name.",
    ]
    return {
        "task_type": "craigslist_browse_subcategory",
        "subcategory": subcategory,
        "steps": steps,
        "assertion": f"URL contains '{subcategory.split()[0].replace('/', '').replace(' ', '')}'."
    }

_TASK_GENERATORS: Dict[CRAIGSLIST_TASK_TYPES, Callable[[dict], dict]] = {
    "craigslist_search_category": craigslist_search_category,
    "craigslist_filter_price_range": craigslist_filter_price_range,
    "craigslist_search_keyword": craigslist_search_keyword,
    "craigslist_browse_nearby_city": craigslist_browse_nearby_city,
    "craigslist_view_posting_details": craigslist_view_posting_details,
    "craigslist_language_switch": craigslist_language_switch,
    "craigslist_navigate_help_topic": craigslist_navigate_help_topic,
    "craigslist_browse_event_calendar": craigslist_browse_event_calendar,
    "craigslist_browse_discussion_forum": craigslist_browse_discussion_forum,
    "craigslist_browse_subcategory": craigslist_browse_subcategory,
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