import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

DISCOGS_SEARCH_TERMS = [
    "The Beatles", "Pink Floyd", "Miles Davis", "Daft Punk", "Madonna", "Nirvana", "Radiohead", "Taylor Swift",
    "Beyoncé", "Kendrick Lamar", "David Bowie", "Queen", "Bob Dylan", "Metallica", "Aphex Twin", "Prince",
    "Kanye West", "The Rolling Stones", "Arctic Monkeys", "Adele", "Fleetwood Mac", "Led Zeppelin", "Drake",
    "The Cure", "Frank Sinatra", "The Smiths", "U2", "Bruce Springsteen", "The Doors", "Joy Division", "Sade"
]

DISCOGS_GENRES = [
    "Rock", "Electronic", "Jazz", "Pop", "Hip Hop", "Funk / Soul", "Classical", "Reggae", "Blues", "Folk, World, & Country",
    "Stage & Screen", "Latin", "Non-Music", "Children's", "Brass & Military", "Folk", "Country", "Ambient", "House", "Techno",
    "Disco", "Punk", "Experimental", "Dub", "Indie Rock"
]

DISCOGS_FORMATS = [
    "Vinyl", "CD", "Cassette", "File", "DVD", "Blu-ray", "Flexi-disc", "Lathe Cut", "Shellac", "Acetate", "MiniDisc",
    "8-Track Cartridge", "Reel-To-Reel", "VHS", "Laserdisc", "Hybrid", "Box Set", "All Media", "CDr", "DVDr", "SACD", "HDCD"
]

DISCOGS_YEARS = [str(y) for y in range(1960, 2023)]

DISCOGS_COUNTRIES = [
    "US", "UK", "Germany", "Japan", "France", "Canada", "Italy", "Australia", "Netherlands", "Brazil", "Russia", "Sweden",
    "Spain", "Poland", "Mexico", "Norway", "Finland", "Denmark", "Belgium", "Switzerland", "Austria", "Greece"
]

DISCOGS_LABELS = [
    "Columbia", "EMI", "Warner Bros. Records", "Atlantic", "Sony Music", "Universal", "Polydor", "Island Records",
    "Virgin", "RCA", "Motown", "Def Jam", "Sub Pop", "XL Recordings", "Mute", "Domino", "4AD", "Blue Note", "Verve",
    "Decca", "Mercury", "Epic", "Geffen", "Chess", "Ninja Tune"
]

DISCOGS_SORTS = [
    "Best Match", "Artist, A-Z", "Artist, Z-A", "Title, A-Z", "Title, Z-A", "Year, Newest First", "Year, Oldest First",
    "Format, A-Z", "Format, Z-A", "Label, A-Z", "Label, Z-A", "Country, A-Z", "Country, Z-A", "Catalog Number, A-Z",
    "Catalog Number, Z-A", "Added, Newest First", "Added, Oldest First", "Price, Lowest First", "Price, Highest First"
]

DISCOGS_COLLECTION_FILTERS = [
    "Wantlist", "Collection", "Folders", "Rated", "Unrated", "For Sale", "Not For Sale", "Private Notes", "Public Notes",
    "Duplicates", "Missing Info", "With Images", "Without Images", "With Videos", "Without Videos", "With Reviews",
    "Without Reviews", "With Ratings", "Without Ratings", "With Tracklist", "Without Tracklist"
]

DISCOGS_HELP_TOPICS = [
    ("How to search for releases", "search"), ("How to add a release", "add-release"), ("How to edit an artist", "edit-artist"),
    ("How to use the Marketplace", "marketplace"), ("How to report an issue", "report-issue"), ("How to manage your collection", "collection"),
    ("How to manage your wantlist", "wantlist"), ("How to contact sellers", "contact-seller"), ("How to leave feedback", "feedback"),
    ("How to request a merge", "merge"), ("How to reset your password", "reset-password"), ("How to create an account", "create-account"),
    ("How to delete your account", "delete-account"), ("How to block a user", "block-user"), ("How to report copyright", "copyright"),
    ("How to use advanced search", "advanced-search"), ("How to filter search results", "filter-search"), ("How to use Discogs App", "app"),
    ("How to use Discogs API", "api"), ("How to update your profile", "update-profile"), ("How to change language", "language")
]

DISCOGS_MARKETPLACE_PRICE_RANGES = [
    "$0-5", "$5-10", "$10-20", "$20-30", "$30-50", "$50-75", "$75-100", "$100-150", "$150-200", "$200-300", "$300-500",
    "$500-750", "$750-1000", "$1000-1500", "$1500-2000", "$2000-3000", "$3000-5000", "$5000-7500", "$7500-10000", "$10000+"
]

DISCOGS_MARKETPLACE_CONDITIONS = [
    "Mint (M)", "Near Mint (NM or M-)", "Very Good Plus (VG+)", "Very Good (VG)", "Good Plus (G+)", "Good (G)", "Fair (F)", "Poor (P)",
    "Sealed", "Unplayed", "Promo", "White Label", "Test Pressing", "Picture Disc", "Coloured Vinyl", "Numbered", "Limited Edition",
    "Reissue", "Remastered", "Box Set", "Signed"
]

DISCOGS_ARTIST_SAMPLE = [
    "The Beatles", "Radiohead", "Miles Davis", "Daft Punk", "Madonna", "Queen", "David Bowie", "Nirvana", "Taylor Swift",
    "Bob Dylan", "Prince", "Kanye West", "The Rolling Stones", "Adele", "Fleetwood Mac", "Metallica", "Aphex Twin", "The Cure",
    "Frank Sinatra", "Bruce Springsteen", "The Doors", "Joy Division", "Sade", "Drake", "U2"
]

DISCOGS_RELEASE_SAMPLE = [
    "Abbey Road", "OK Computer", "Kind Of Blue", "Random Access Memories", "Like A Virgin", "A Night At The Opera",
    "The Rise And Fall Of Ziggy Stardust", "Nevermind", "1989", "Highway 61 Revisited", "Purple Rain", "Graduation",
    "Let It Bleed", "21", "Rumours", "Master Of Puppets", "Selected Ambient Works 85-92", "Disintegration", "In The Wee Small Hours",
    "Born To Run", "L.A. Woman", "Unknown Pleasures", "Diamond Life", "Take Care", "The Joshua Tree"
]

DISCOGS_USERNAMES = [
    "vinylfanatic", "musiclover22", "rarecollector", "beatlesmaniac", "jazzcat", "popdiva", "punkrocker", "soulbrother",
    "classicman", "electrohead", "hiphopaddict", "metalhead", "indiegirl", "groovemaster", "discogsdigger", "tapehunter",
    "cdjunkie", "blueshound", "latinjazzman", "funkyvinyl", "audiophile", "progrockfan", "ambientdreamer", "househead",
    "technotraveller"
]

DISCOGS_EMAILS = [
    f"user{i}@example.com" for i in range(1, 26)
]

DISCOGS_PASSWORDS = [
    "Discogs123!", "Music4Life!", "Vinyl2024!", "JazzIsCool1!", "RockOn2024!", "PopStar!22", "FunkSoul2024!", "Classic123!",
    "ElectroBeats!", "HipHop2024!", "MetalPower!", "IndieRocks!", "GrooveMaster1", "TapeHunter22", "CDJunkie2024", "BluesHound1",
    "LatinJazz2024", "FunkyVinyl!", "AudioPhile22", "ProgRock2024!", "AmbientDreamer!", "HouseHead2024", "TechnoTrav1", "RareFinds2024", "Collector2024!"
]

DISCOGS_SAMPLING_CONFIG = {
    "discogs_search_release": 10,
    "discogs_filter_genre": 10,
    "discogs_filter_format": 10,
    "discogs_marketplace_price": 10,
    "discogs_marketplace_condition": 10,
    "discogs_artist_browse": 10,
    "discogs_label_browse": 10,
    "discogs_signup_validation": 10,
    "discogs_help_center_topic": 10,
    "discogs_sort_results": 10
}

DISCOGS_TASK_TYPES = Literal[
    "discogs_search_release",
    "discogs_filter_genre",
    "discogs_filter_format",
    "discogs_marketplace_price",
    "discogs_marketplace_condition",
    "discogs_artist_browse",
    "discogs_label_browse",
    "discogs_signup_validation",
    "discogs_help_center_topic",
    "discogs_sort_results"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, cookie banners, or newsletter modals.",
        "Do not log in, sign up, or attempt to purchase anything.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Discogs", steps).model_dump()

def discogs_search_release(_: dict) -> dict:
    term = random.choice(DISCOGS_SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.discogs.com/'.",
        *_ui_hygiene(),
        "Focus the main search input at the top of the page.",
        f"Type '{term}' and press Enter.",
        "Wait for the search results page to load.",
        "Verify that at least one result is displayed.",
        "Assert that the search term appears in the page title or results header.",
        "Check that the URL contains '/search/'."
    ]
    return {"task_type": "discogs_search_release", "search_term": term, "steps": steps}

def discogs_filter_genre(_: dict) -> dict:
    genre = random.choice(DISCOGS_GENRES)
    steps = [
        "Go to url 'https://www.discogs.com/search/'.",
        *_ui_hygiene(),
        "Locate the 'Genre' filter in the sidebar.",
        f"Select the '{genre}' genre.",
        "Wait for results to update.",
        "Verify that the results list is not empty.",
        "Assert that the selected genre appears as an active filter.",
        "Check that the URL query includes 'genre' parameter."
    ]
    return {"task_type": "discogs_filter_genre", "genre": genre, "steps": steps}

def discogs_filter_format(_: dict) -> dict:
    fmt = random.choice(DISCOGS_FORMATS)
    steps = [
        "Go to url 'https://www.discogs.com/search/'.",
        *_ui_hygiene(),
        "Locate the 'Format' filter in the sidebar.",
        f"Select the '{fmt}' format.",
        "Wait for results to update.",
        "Verify that the results list is not empty.",
        "Assert that the selected format appears as an active filter.",
        "Check that the URL query includes 'format' parameter."
    ]
    return {"task_type": "discogs_filter_format", "format": fmt, "steps": steps}

def discogs_marketplace_price(_: dict) -> dict:
    price = random.choice(DISCOGS_MARKETPLACE_PRICE_RANGES)
    steps = [
        "Go to url 'https://www.discogs.com/sell/list'.",
        *_ui_hygiene(),
        "Locate the price range filter in the sidebar.",
        f"Select the '{price}' price range.",
        "Wait for results to update.",
        "Verify that at least one item is shown.",
        "Assert that the selected price range is displayed as an active filter.",
        "Check that the URL query includes the price range."
    ]
    return {"task_type": "discogs_marketplace_price", "price_range": price, "steps": steps}

def discogs_marketplace_condition(_: dict) -> dict:
    cond = random.choice(DISCOGS_MARKETPLACE_CONDITIONS)
    steps = [
        "Go to url 'https://www.discogs.com/sell/list'.",
        *_ui_hygiene(),
        "Locate the 'Condition' filter in the sidebar.",
        f"Select the '{cond}' condition.",
        "Wait for results to update.",
        "Verify that at least one item is shown.",
        "Assert that the selected condition is displayed as an active filter.",
        "Check that the URL query includes the condition."
    ]
    return {"task_type": "discogs_marketplace_condition", "condition": cond, "steps": steps}

def discogs_artist_browse(_: dict) -> dict:
    artist = random.choice(DISCOGS_ARTIST_SAMPLE)
    steps = [
        "Go to url 'https://www.discogs.com/'.",
        *_ui_hygiene(),
        "Focus the main search input at the top of the page.",
        f"Type '{artist}' and select the artist suggestion from the autocomplete dropdown.",
        "Wait for the artist page to load.",
        "Verify the artist name appears in the page header.",
        "Assert that the URL contains '/artist/'.",
        "Check that at least one release is listed on the artist page."
    ]
    return {"task_type": "discogs_artist_browse", "artist": artist, "steps": steps}

def discogs_label_browse(_: dict) -> dict:
    label = random.choice(DISCOGS_LABELS)
    steps = [
        "Go to url 'https://www.discogs.com/'.",
        *_ui_hygiene(),
        "Focus the main search input at the top of the page.",
        f"Type '{label}' and select the label suggestion from the autocomplete dropdown.",
        "Wait for the label page to load.",
        "Verify the label name appears in the page header.",
        "Assert that the URL contains '/label/'.",
        "Check that at least one release is listed on the label page."
    ]
    return {"task_type": "discogs_label_browse", "label": label, "steps": steps}

def discogs_signup_validation(_: dict) -> dict:
    username = random.choice(DISCOGS_USERNAMES)
    email = random.choice(DISCOGS_EMAILS)
    password = random.choice(DISCOGS_PASSWORDS)
    steps = [
        "Go to url 'https://www.discogs.com/register'.",
        *_ui_hygiene(),
        "Locate the registration form.",
        f"Enter username '{username}'.",
        f"Enter email '{email}'.",
        f"Enter password '{password}'.",
        "Check the terms and conditions checkbox.",
        "Click the 'Register' button.",
        "Verify that an error message appears indicating email confirmation is required, or that a confirmation banner appears.",
        "Assert that no personal data is displayed after submission.",
        "Do not proceed with any email confirmation."
    ]
    return {"task_type": "discogs_signup_validation", "username": username, "email": email, "password": password, "steps": steps}

def discogs_help_center_topic(_: dict) -> dict:
    topic, slug = random.choice(DISCOGS_HELP_TOPICS)
    steps = [
        "Go to url 'https://support.discogs.com/'.",
        *_ui_hygiene(),
        f"Locate and open the help topic '{topic}'.",
        "Read the first two points or paragraphs.",
        "Assert that the help article or FAQ content loads.",
        "Check that the topic title appears in the page header."
    ]
    return {"task_type": "discogs_help_center_topic", "topic": topic, "steps": steps}

def discogs_sort_results(_: dict) -> dict:
    sort = random.choice(DISCOGS_SORTS)
    term = random.choice(DISCOGS_SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.discogs.com/'.",
        *_ui_hygiene(),
        "Focus the main search input at the top of the page.",
        f"Type '{term}' and press Enter.",
        "Wait for the search results page to load.",
        "Locate the 'Sort' dropdown or menu.",
        f"Select the '{sort}' sorting option.",
        "Wait for results to update.",
        "Assert that the selected sort is displayed as active.",
        "Check that the results order changes accordingly."
    ]
    return {"task_type": "discogs_sort_results", "sort": sort, "search_term": term, "steps": steps}

_TASK_GENERATORS: Dict[DISCOGS_TASK_TYPES, Callable[[dict], dict]] = {
    "discogs_search_release": discogs_search_release,
    "discogs_filter_genre": discogs_filter_genre,
    "discogs_filter_format": discogs_filter_format,
    "discogs_marketplace_price": discogs_marketplace_price,
    "discogs_marketplace_condition": discogs_marketplace_condition,
    "discogs_artist_browse": discogs_artist_browse,
    "discogs_label_browse": discogs_label_browse,
    "discogs_signup_validation": discogs_signup_validation,
    "discogs_help_center_topic": discogs_help_center_topic,
    "discogs_sort_results": discogs_sort_results
}

def generate_discogs_task(task_type: DISCOGS_TASK_TYPES, payload: dict) -> dict:
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
    items = list(DISCOGS_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_discogs_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)