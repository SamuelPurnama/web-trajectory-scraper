import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

FOM_CATEGORIES = [
    "FILM NEWS", "CUTTING ROOM FLOOR", "FEATURES", "NEW REVIEWS", "CLASSIC FILM",
    "INTERVIEWS", "LISTS", "RANKING", "FILM OPINION", "FROM THE VAULT", "TRENDING STORIES",
    "MUSIC", "TRAVEL", "ART", "SHOP", "MAILING LIST", "REVIEWS", "NEWS", "CULTURE",
    "LIVE", "ALBUMS", "SINGLES", "GIGS", "INTERVIEWS (MUSIC)", "OPINION", "COLUMNS"
][:20]

FOM_SEARCH_TERMS = [
    "David Bowie", "Quentin Tarantino", "Sophie Turner", "Steve Coogan", "The Beatles",
    "Oscar winners", "Psychedelic rock", "Classic horror", "Film soundtracks", "Indie cinema",
    "Art exhibitions", "Travel guides", "Vinyl records", "Music festivals", "British actors",
    "Movie reviews", "Director interviews", "Album reviews", "Film rankings", "Music opinion",
    "Cult classics", "New releases", "Retro films", "Live performances", "Soundtrack reviews"
][:24]

FOM_PERSONS = [
    "Quentin Tarantino", "Sophie Turner", "Steve Coogan", "David Bowie", "Paul McCartney",
    "John Lennon", "Ringo Starr", "George Harrison", "Brooke H Cellars", "Athina Rachel Tsangari",
    "Jaclyn Martinez", "Yeo Siew Hua", "Martin Scorsese", "Christopher Nolan", "Greta Gerwig",
    "Florence Pugh", "Daniel Kaluuya", "Tilda Swinton", "Olivia Colman", "Cillian Murphy",
    "Phoebe Waller-Bridge", "Sam Mendes", "Billie Eilish", "Mark Ronson", "Hildur Guðnadóttir"
][:25]

FOM_FEATURES = [
    "The 10 best opening songs in movies", "Keeping Score: How ‘The Omen’ reinvented the horror movie soundtrack",
    "Five brilliant and brutal old thrillers you’ve never seen", "Oscars Ranked",
    "Anatomy of a Scene", "Who was the first British actor to win an Oscar for playing an American?",
    "The Beatles 1968 press photo", "Best debut albums", "Greatest live performances",
    "Top 20 cult films", "Iconic music videos", "Most influential directors",
    "Classic album covers", "Underrated soundtracks", "Best travel destinations for music lovers",
    "Art movements that changed music", "Hidden gems: films", "Women in music",
    "Punk rock history", "Jazz in cinema", "Experimental film features", "Indie film spotlights"
][:22]

FOM_REVIEWS = [
    "Stranger Eyes - Yeo Siew Hua - 2024", "The Cramps - A Period Piece - 2025 - Brooke H Cellars",
    "Harvest - 2025 - Jaclyn-Martinez", "The Lighthouse - 2019 - Robert Eggers",
    "Parasite - 2019 - Bong Joon-ho", "Nomadland - 2020 - Chloé Zhao", "1917 - 2019 - Sam Mendes",
    "Soul - 2020 - Pete Docter", "The Power of the Dog - 2021 - Jane Campion",
    "Dune - 2021 - Denis Villeneuve", "Licorice Pizza - 2021 - Paul Thomas Anderson",
    "Minari - 2020 - Lee Isaac Chung", "Promising Young Woman - 2020 - Emerald Fennell",
    "Sound of Metal - 2019 - Darius Marder", "Another Round - 2020 - Thomas Vinterberg",
    "Jojo Rabbit - 2019 - Taika Waititi", "Roma - 2018 - Alfonso Cuarón",
    "La La Land - 2016 - Damien Chazelle", "Moonlight - 2016 - Barry Jenkins",
    "Manchester by the Sea - 2016 - Kenneth Lonergan", "Lady Bird - 2017 - Greta Gerwig"
][:21]

FOM_SECTION_MORE = [
    "More New Reviews", "More Film News", "More Features", "More Classic Film", "More Trending Stories",
    "More Interviews", "More Lists", "More Rankings", "More Film Opinion", "More From the Vault",
    "More Music", "More Travel", "More Art", "More Shop", "More Mailing List", "More Reviews",
    "More News", "More Culture", "More Live", "More Albums", "More Singles"
][:21]

FOM_NAV_LINKS = [
    "Far Out Magazine", "MUSIC", "FILM", "TRAVEL", "ART", "SHOP", "MAILING LIST"
]

FOM_SHOP_CATEGORIES = [
    "Vinyl", "T-Shirts", "Posters", "Books", "Accessories", "Gift Cards", "Hoodies",
    "Mugs", "Tote Bags", "Stickers", "Pins", "Hats", "Socks", "Jackets", "Prints",
    "Calendars", "Notebooks", "Badges", "Magnets", "Phone Cases", "Art Prints"
][:21]

FOM_MAILING_LIST_FIELDS = [
    "Email", "First Name", "Last Name", "Country", "Interests", "Consent Checkbox", "Birthday",
    "Genre Preferences", "Newsletter Frequency", "Mobile Number", "City", "Postcode",
    "Favourite Artist", "Favourite Film", "Subscription Type", "Language", "Privacy Agreement",
    "Receive Offers", "Receive Event Updates", "Receive Shop Promotions", "Unsubscribe Option"
][:21]

FOM_SORT_OPTIONS = [
    "Most Recent", "Oldest", "Most Popular", "Editor's Pick", "Highest Rated", "Lowest Rated",
    "A-Z", "Z-A", "By Author", "By Category", "By Year", "By Month", "By Relevance",
    "By Comment Count", "By Share Count", "By Like Count", "By View Count", "Random", "Featured", "Trending", "Recommended"
][:21]

FOM_ARTICLE_TIME_AGO = [
    "1 HOUR AGO", "2 HOURS AGO", "3 HOURS AGO", "4 HOURS AGO", "5 HOURS AGO",
    "6 HOURS AGO", "7 HOURS AGO", "8 HOURS AGO", "9 HOURS AGO", "10 HOURS AGO",
    "1 DAY AGO", "2 DAYS AGO", "3 DAYS AGO", "4 DAYS AGO", "5 DAYS AGO",
    "6 DAYS AGO", "1 WEEK AGO", "2 WEEKS AGO", "3 WEEKS AGO", "1 MONTH AGO"
][:20]

FOM_FILTER_COMBOS = [
    {"category": cat, "sort": sort}
    for cat in FOM_CATEGORIES for sort in FOM_SORT_OPTIONS
][:30]

FOM_ASSERTIONS = [
    "URL contains expected path",
    "Page contains expected heading",
    "Article body is visible",
    "Profile page shows correct name",
    "Category filter is active",
    "Shop cart is empty",
    "Mailing list form displays confirmation",
    "Search results are shown",
    "No error banners are visible",
    "Correct article time is displayed",
    "Section loads more articles",
    "Sort order is reflected in results",
    "No duplicate articles in list",
    "Correct feature headline is present",
    "Review rating is visible",
    "Shop category page loads",
    "Form validation error shown for invalid email",
    "Newsletter opt-in checkbox is required",
    "No purchase required to proceed",
    "Returned to homepage after navigation"
][:20]

FOM_TASK_TYPES = Literal[
    "fom_navigate_category",
    "fom_search_article",
    "fom_view_person_profile",
    "fom_read_feature_article",
    "fom_read_film_review",
    "fom_load_more_section",
    "fom_navigate_shop_category",
    "fom_signup_mailing_list",
    "fom_sort_category_articles",
    "fom_filter_category_combo"
]

FOM_SAMPLING_CONFIG: Dict[FOM_TASK_TYPES, int] = {
    "fom_navigate_category": 10,
    "fom_search_article": 10,
    "fom_view_person_profile": 10,
    "fom_read_feature_article": 10,
    "fom_read_film_review": 10,
    "fom_load_more_section": 10,
    "fom_navigate_shop_category": 10,
    "fom_signup_mailing_list": 10,
    "fom_sort_category_articles": 10,
    "fom_filter_category_combo": 10,
}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, newsletter signup).",
        "Do not submit any payment or sensitive personal information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Far Out Magazine", steps).model_dump()

def fom_navigate_category(payload: dict) -> dict:
    category = random.choice(FOM_CATEGORIES)
    steps = [
        "Go to url 'https://faroutmagazine.co.uk/'.",
        *_ui_hygiene(),
        f"Locate and click the '{category}' link in the main navigation or section list.",
        f"Wait for the '{category}' page or section to load.",
        f"Assert that the page heading or active tab matches '{category}'."
    ]
    return {
        "task_type": "fom_navigate_category",
        "category": category,
        "steps": steps,
        "assertion": "Page contains expected heading for the selected category."
    }

def fom_search_article(payload: dict) -> dict:
    term = random.choice(FOM_SEARCH_TERMS)
    steps = [
        "Go to url 'https://faroutmagazine.co.uk/'.",
        *_ui_hygiene(),
        "Click the 'Search' button in the header.",
        "Wait for the search input/modal to appear.",
        f"Type '{term}' into the search input and submit.",
        "Wait for search results to load.",
        f"Assert that at least one result contains '{term}' in the title or snippet."
    ]
    return {
        "task_type": "fom_search_article",
        "search_term": term,
        "steps": steps,
        "assertion": "Search results include the query term in at least one result."
    }

def fom_view_person_profile(payload: dict) -> dict:
    person = random.choice(FOM_PERSONS)
    steps = [
        "Go to url 'https://faroutmagazine.co.uk/film/'.",
        *_ui_hygiene(),
        f"Find and click on the link for '{person}' (person/film profile link).",
        f"Wait for the profile or related articles page for '{person}' to load.",
        f"Assert that the page contains '{person}' in the heading or main content."
    ]
    return {
        "task_type": "fom_view_person_profile",
        "person": person,
        "steps": steps,
        "assertion": "Profile or article list for the person is visible."
    }

def fom_read_feature_article(payload: dict) -> dict:
    feature = random.choice(FOM_FEATURES)
    steps = [
        "Go to url 'https://faroutmagazine.co.uk/film/'.",
        *_ui_hygiene(),
        f"Locate and click the feature article link titled '{feature}'.",
        "Wait for the article page to load.",
        f"Assert that the article heading matches '{feature}'.",
        "Assert that the article body/content is visible."
    ]
    return {
        "task_type": "fom_read_feature_article",
        "feature_title": feature,
        "steps": steps,
        "assertion": "Feature article heading and content are present."
    }

def fom_read_film_review(payload: dict) -> dict:
    review = random.choice(FOM_REVIEWS)
    steps = [
        "Go to url 'https://faroutmagazine.co.uk/film/'.",
        *_ui_hygiene(),
        f"Locate and click the film review link '{review}'.",
        "Wait for the review page to load.",
        f"Assert that the review heading includes '{review.split(' - ')[0]}'.",
        "Assert that a review body or rating is visible."
    ]
    return {
        "task_type": "fom_read_film_review",
        "review_title": review,
        "steps": steps,
        "assertion": "Review heading and content are present."
    }

def fom_load_more_section(payload: dict) -> dict:
    section = random.choice(FOM_SECTION_MORE)
    steps = [
        "Go to url 'https://faroutmagazine.co.uk/film/'.",
        *_ui_hygiene(),
        f"Scroll to the section with a '{section}' link/button.",
        f"Click the '{section}' link/button to load more articles.",
        "Wait for additional articles to appear.",
        "Assert that new articles are loaded and visible below the section."
    ]
    return {
        "task_type": "fom_load_more_section",
        "section": section,
        "steps": steps,
        "assertion": "New articles are loaded in the section after clicking 'More'."
    }

def fom_navigate_shop_category(payload: dict) -> dict:
    shop_cat = random.choice(FOM_SHOP_CATEGORIES)
    steps = [
        "Go to url 'https://faroutmagazine.co.uk/'.",
        *_ui_hygiene(),
        "Click the 'SHOP' link in the main navigation.",
        f"On the shop page, locate and click the '{shop_cat}' category.",
        f"Wait for the '{shop_cat}' category page to load.",
        f"Assert that the shop category heading matches '{shop_cat}'."
    ]
    return {
        "task_type": "fom_navigate_shop_category",
        "shop_category": shop_cat,
        "steps": steps,
        "assertion": "Shop category page is displayed with correct heading."
    }

def fom_signup_mailing_list(payload: dict) -> dict:
    field = random.choice(FOM_MAILING_LIST_FIELDS)
    steps = [
        "Go to url 'https://faroutmagazine.co.uk/'.",
        *_ui_hygiene(),
        "Click the 'MAILING LIST' link in the main navigation.",
        "Wait for the mailing list signup form to appear.",
        f"Verify that the field '{field}' is present in the form.",
        "Enter a valid value for all required fields.",
        "Submit the form.",
        "Assert that a confirmation message or success banner appears."
    ]
    return {
        "task_type": "fom_signup_mailing_list",
        "mailing_list_field": field,
        "steps": steps,
        "assertion": "Mailing list signup confirmation is displayed."
    }

def fom_sort_category_articles(payload: dict) -> dict:
    category = random.choice(FOM_CATEGORIES)
    sort = random.choice(FOM_SORT_OPTIONS)
    steps = [
        "Go to url 'https://faroutmagazine.co.uk/'.",
        *_ui_hygiene(),
        f"Navigate to the '{category}' section.",
        f"Locate the sort dropdown or options and select '{sort}'.",
        "Wait for the articles to re-order.",
        f"Assert that the articles are sorted by '{sort}' (e.g., check order or label)."
    ]
    return {
        "task_type": "fom_sort_category_articles",
        "category": category,
        "sort_option": sort,
        "steps": steps,
        "assertion": "Articles are sorted as per the selected sort option."
    }

def fom_filter_category_combo(payload: dict) -> dict:
    combo = random.choice(FOM_FILTER_COMBOS)
    steps = [
        "Go to url 'https://faroutmagazine.co.uk/'.",
        *_ui_hygiene(),
        f"Navigate to the '{combo['category']}' section.",
        f"Apply the sort/filter option '{combo['sort']}'.",
        "Wait for the filtered/sorted articles to load.",
        f"Assert that the articles reflect both the '{combo['category']}' filter and '{combo['sort']}' sort."
    ]
    return {
        "task_type": "fom_filter_category_combo",
        "category": combo['category'],
        "sort_option": combo['sort'],
        "steps": steps,
        "assertion": "Filtered and sorted articles are displayed as per selection."
    }

_TASK_GENERATORS: Dict[FOM_TASK_TYPES, Callable[[dict], dict]] = {
    "fom_navigate_category": fom_navigate_category,
    "fom_search_article": fom_search_article,
    "fom_view_person_profile": fom_view_person_profile,
    "fom_read_feature_article": fom_read_feature_article,
    "fom_read_film_review": fom_read_film_review,
    "fom_load_more_section": fom_load_more_section,
    "fom_navigate_shop_category": fom_navigate_shop_category,
    "fom_signup_mailing_list": fom_signup_mailing_list,
    "fom_sort_category_articles": fom_sort_category_articles,
    "fom_filter_category_combo": fom_filter_category_combo,
}

def generate_fom_task(task_type: FOM_TASK_TYPES, payload: dict) -> dict:
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
    items = list(FOM_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_fom_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)