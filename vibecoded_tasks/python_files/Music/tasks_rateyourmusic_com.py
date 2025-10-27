import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

RYM_TASK_TYPES = Literal[
    "rym_search_album",
    "rym_filter_genre",
    "rym_sort_by_rating",
    "rym_album_details",
    "rym_browse_charts",
    "rym_advanced_search",
    "rym_browse_artist",
    "rym_browse_list",
    "rym_signup_form_validation",
    "rym_help_center_topic",
]

RYM_SAMPLING_CONFIG: Dict[RYM_TASK_TYPES, int] = {
    "rym_search_album": 10,
    "rym_filter_genre": 10,
    "rym_sort_by_rating": 10,
    "rym_album_details": 10,
    "rym_browse_charts": 10,
    "rym_advanced_search": 10,
    "rym_browse_artist": 10,
    "rym_browse_list": 10,
    "rym_signup_form_validation": 10,
    "rym_help_center_topic": 10,
}

RYM_GENRES = [
    "Rock", "Pop", "Hip Hop", "Jazz", "Electronic", "Metal", "Folk", "Classical", "Punk", "Blues",
    "Country", "Reggae", "Soul", "Funk", "Ambient", "Disco", "R&B", "Indie Rock", "Experimental", "Progressive Rock",
    "Synthpop", "Techno", "House", "Noise", "Shoegaze", "Industrial", "Post-Punk", "Alternative Rock", "Grunge", "Hardcore Punk"
]

RYM_YEARS = [str(y) for y in range(1960, 2024)]

RYM_ARTISTS = [
    "The Beatles", "Radiohead", "Pink Floyd", "Kanye West", "David Bowie", "Bob Dylan", "Miles Davis", "Kendrick Lamar",
    "Led Zeppelin", "The Rolling Stones", "Beyoncé", "Taylor Swift", "Queen", "Frank Zappa", "Prince", "The Smiths",
    "Nick Cave", "Joni Mitchell", "PJ Harvey", "Sufjan Stevens", "Nirvana", "The Cure", "Daft Punk", "Aphex Twin",
    "Joy Division", "Fleetwood Mac", "Kate Bush", "Arctic Monkeys", "OutKast", "The Clash", "Tom Waits"
]

RYM_ALBUMS = [
    "OK Computer", "To Pimp a Butterfly", "The Dark Side of the Moon", "Abbey Road", "Blonde on Blonde",
    "Kind of Blue", "The Wall", "In the Aeroplane Over the Sea", "Sgt. Pepper's Lonely Hearts Club Band",
    "Kid A", "Rumours", "The Queen Is Dead", "Madvillainy", "Good Kid, M.A.A.D City", "Nevermind",
    "A Love Supreme", "Hounds of Love", "Discovery", "Blue", "The Velvet Underground & Nico",
    "Exile on Main St.", "Illmatic", "London Calling", "Blackstar", "Funeral",
    "Yankee Hotel Foxtrot", "DAMN.", "The Bends", "Born to Run", "Let It Be"
]

RYM_LISTS = [
    "RYM Ultimate Chart", "Top 100 Albums of the 1970s", "Best Shoegaze Albums", "Top Hip Hop Albums", "Best Metal Albums",
    "Top Electronic Albums", "Best Albums of 2020", "Top Jazz Albums", "Best Punk Albums", "Top Indie Rock Albums",
    "Best Albums of 1990s", "Top Experimental Albums", "Best Live Albums", "Top Soundtracks", "Best Debut Albums",
    "Top Concept Albums", "Best Female Artists", "Top EPs", "Best Post-Punk Albums", "Top Ambient Albums",
    "Best Album Covers", "Top R&B Albums", "Best Double Albums", "Top Folk Albums", "Best Instrumental Albums",
    "Top Progressive Rock Albums", "Best Albums of 1980s", "Top Grunge Albums", "Best Compilation Albums", "Top Noise Albums"
]

RYM_SEARCH_TERMS = [
    "Abbey Road", "OK Computer", "Miles Davis", "Beyoncé", "Kendrick Lamar", "Jazz", "Synthpop", "Ambient",
    "The Wall", "Let It Be", "A Love Supreme", "Rumours", "London Calling", "Aphex Twin", "Kate Bush",
    "Funeral", "The Bends", "Born to Run", "Madvillainy", "Fleetwood Mac", "Nirvana", "Joy Division",
    "Discovery", "Good Kid, M.A.A.D City", "Blue", "The Smiths", "Tom Waits", "OutKast", "Arctic Monkeys", "Grunge"
]

RYM_SORT_OPTIONS = [
    "Average Rating", "Number of Ratings", "Release Date", "Title", "Popularity", "Reviews", "Ownership Count",
    "Added Date", "Most Collected", "Most Wishlisted", "Most Reviewed", "Most Played", "Most Discussed",
    "Most Favorited", "Most Listed", "Most Tagged", "Most Commented", "Most Shared", "Most Liked", "Most Disliked", "Most Followed"
]

RYM_HELP_TOPICS = [
    ("Account Registration", "register"),
    ("Password Reset", "password"),
    ("Rating Albums", "rate"),
    ("Creating Lists", "lists"),
    ("Adding Releases", "add-release"),
    ("Editing Artist Info", "edit-artist"),
    ("Reporting Errors", "report"),
    ("Site Rules", "rules"),
    ("Privacy Policy", "privacy"),
    ("Contact Support", "contact"),
    ("Tagging Albums", "tags"),
    ("Using Charts", "charts"),
    ("Advanced Search", "search"),
    ("Mobile Site", "mobile"),
    ("Genres & Styles", "genres"),
    ("User Levels", "user-levels"),
    ("Blocking Users", "block"),
    ("Importing Collections", "import"),
    ("Exporting Data", "export"),
    ("Deleting Account", "delete-account"),
    ("Notifications", "notifications"),
    ("Site Announcements", "announcements"),
    ("FAQ", "faq"),
    ("Moderation", "moderation"),
    ("Community Guidelines", "community")
]

RYM_SIGNUP_USERNAMES = [
    "musicfan2024", "vinylhunter", "jazzcat", "proghead", "punkrocker", "popaddict", "synthwavefan", "indielover",
    "metalmaniac", "hiphophead", "classicalbuff", "ambientdreamer", "folkenthusiast", "electrobeat", "soulsearcher",
    "funkmaster", "countrykid", "blueshound", "discodancer", "altrocker", "shoegazer", "noisefan", "grungechild", "postpunker", "soundtrackfan"
]

RYM_SIGNUP_EMAILS = [
    "user1@example.com", "musiclover@example.com", "fan2024@example.com", "vinyl@example.com", "proghead@example.com",
    "punkrock@example.com", "popfan@example.com", "synthwave@example.com", "indie@example.com", "metal@example.com",
    "hiphop@example.com", "classical@example.com", "ambient@example.com", "folk@example.com", "electro@example.com",
    "soul@example.com", "funk@example.com", "country@example.com", "blues@example.com", "disco@example.com",
    "altrock@example.com", "shoegaze@example.com", "noise@example.com", "grunge@example.com", "postpunk@example.com"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, cookie banners, or overlays if present.",
        "Do not log in, sign up, or submit any personal data unless instructed.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("RateYourMusic", steps).model_dump()

def rym_search_album(_: dict) -> dict:
    term = random.choice(RYM_SEARCH_TERMS)
    steps = [
        "Go to url 'https://rateyourmusic.com/'.",
        *_ui_hygiene(),
        "Locate the main search bar at the top of the page.",
        f"Type '{term}' into the search bar.",
        "Wait for autocomplete suggestions to appear.",
        "Press Enter or click the search icon to submit the search.",
        "Verify that the search results page loads and contains results for the term.",
        f"Assert that at least one result contains '{term}' in the title, artist, or description.",
        "Check that the URL contains '/search'.",
    ]
    return {"task_type": "rym_search_album", "search_term": term, "steps": steps}

def rym_filter_genre(_: dict) -> dict:
    genre = random.choice(RYM_GENRES)
    steps = [
        "Go to url 'https://rateyourmusic.com/charts/top/album/all-time'.",
        *_ui_hygiene(),
        "Locate the genre filter dropdown or input.",
        f"Select or type the genre '{genre}'.",
        "Apply the filter.",
        "Wait for the page to refresh with filtered results.",
        f"Assert that the genre '{genre}' appears in the filter bar or as an active filter.",
        "Check that the results list contains at least one album with the genre label.",
        "Check that the URL contains the genre parameter or filter.",
    ]
    return {"task_type": "rym_filter_genre", "genre": genre, "steps": steps}

def rym_sort_by_rating(_: dict) -> dict:
    sort_option = random.choice(RYM_SORT_OPTIONS)
    steps = [
        "Go to url 'https://rateyourmusic.com/charts/top/album/all-time'.",
        *_ui_hygiene(),
        "Locate the sort dropdown or controls above the album list.",
        f"Select the sort option '{sort_option}'.",
        "Wait for the page to update.",
        f"Assert that the sort order is set to '{sort_option}' (e.g., check label or URL parameter).",
        "Verify that the first page of results is sorted as expected for the chosen option.",
    ]
    return {"task_type": "rym_sort_by_rating", "sort_option": sort_option, "steps": steps}

def rym_album_details(_: dict) -> dict:
    album = random.choice(RYM_ALBUMS)
    steps = [
        "Go to url 'https://rateyourmusic.com/'.",
        *_ui_hygiene(),
        "Use the search bar to search for the album by name.",
        f"Type '{album}' and press Enter.",
        "In the search results, click the album title that matches exactly.",
        "Wait for the album details page to load.",
        "Assert that the album title matches the expected name.",
        "Check that the page contains sections for tracklist, ratings, and reviews.",
        "Verify that the URL contains '/release/' or '/album/'.",
    ]
    return {"task_type": "rym_album_details", "album": album, "steps": steps}

def rym_browse_charts(_: dict) -> dict:
    year = random.choice(RYM_YEARS)
    genre = random.choice(RYM_GENRES)
    steps = [
        "Go to url 'https://rateyourmusic.com/charts/top/album/'.",
        *_ui_hygiene(),
        f"Set the year filter to '{year}'.",
        f"Set the genre filter to '{genre}'.",
        "Apply the filters.",
        "Wait for the chart to refresh.",
        f"Assert that the chart heading or filter bar shows year '{year}' and genre '{genre}'.",
        "Check that the results list is not empty.",
        "Verify that the URL contains the year and genre parameters.",
    ]
    return {"task_type": "rym_browse_charts", "year": year, "genre": genre, "steps": steps}

def rym_advanced_search(_: dict) -> dict:
    artist = random.choice(RYM_ARTISTS)
    genre = random.choice(RYM_GENRES)
    year = random.choice(RYM_YEARS)
    steps = [
        "Go to url 'https://rateyourmusic.com/advanced_search'.",
        *_ui_hygiene(),
        f"Enter '{artist}' in the artist field.",
        f"Select '{genre}' in the genre dropdown.",
        f"Set the release year to '{year}'.",
        "Submit the advanced search form.",
        "Wait for the results page to load.",
        f"Assert that at least one result has artist '{artist}', genre '{genre}', and year '{year}'.",
        "Check that the URL contains '/search' and relevant parameters.",
    ]
    return {"task_type": "rym_advanced_search", "artist": artist, "genre": genre, "year": year, "steps": steps}

def rym_browse_artist(_: dict) -> dict:
    artist = random.choice(RYM_ARTISTS)
    steps = [
        "Go to url 'https://rateyourmusic.com/'.",
        *_ui_hygiene(),
        "Use the search bar to search for the artist by name.",
        f"Type '{artist}' and press Enter.",
        "In the search results, click the artist name that matches exactly.",
        "Wait for the artist profile page to load.",
        "Assert that the artist name is displayed as the page heading.",
        "Check that the page lists albums, singles, and related artists.",
        "Verify that the URL contains '/artist/'.",
    ]
    return {"task_type": "rym_browse_artist", "artist": artist, "steps": steps}

def rym_browse_list(_: dict) -> dict:
    list_name = random.choice(RYM_LISTS)
    steps = [
        "Go to url 'https://rateyourmusic.com/lists/'.",
        *_ui_hygiene(),
        "Locate the search or browse field for lists.",
        f"Type '{list_name}' and submit.",
        "In the results, click the list title that matches exactly.",
        "Wait for the list page to load.",
        "Assert that the list title matches the expected name.",
        "Check that the list contains at least 10 items.",
        "Verify that the URL contains '/list/'.",
    ]
    return {"task_type": "rym_browse_list", "list_name": list_name, "steps": steps}

def rym_signup_form_validation(_: dict) -> dict:
    username = random.choice(RYM_SIGNUP_USERNAMES)
    email = random.choice(RYM_SIGNUP_EMAILS)
    steps = [
        "Go to url 'https://rateyourmusic.com/account/register'.",
        *_ui_hygiene(),
        f"Enter username '{username}'.",
        f"Enter email '{email}'.",
        "Enter a password shorter than 6 characters (e.g., 'abc').",
        "Attempt to submit the registration form.",
        "Assert that a validation error appears for password length.",
        "Enter a password that meets requirements (e.g., 'MusicFan2024!').",
        "Attempt to submit the registration form.",
        "Assert that no validation error appears for the password field.",
        "Do not complete the registration or submit real data.",
    ]
    return {"task_type": "rym_signup_form_validation", "username": username, "email": email, "steps": steps}

def rym_help_center_topic(_: dict) -> dict:
    topic, slug = random.choice(RYM_HELP_TOPICS)
    url = f"https://rateyourmusic.com/help/{slug}"
    steps = [
        f"Go to url '{url}'.",
        *_ui_hygiene(),
        f"Verify that the help topic '{topic}' is present in the page heading or content.",
        "Assert that at least two FAQ or help points are visible.",
        "Check that the URL matches the expected help topic.",
    ]
    return {"task_type": "rym_help_center_topic", "topic": topic, "steps": steps}

_TASK_GENERATORS: Dict[RYM_TASK_TYPES, Callable[[dict], dict]] = {
    "rym_search_album": rym_search_album,
    "rym_filter_genre": rym_filter_genre,
    "rym_sort_by_rating": rym_sort_by_rating,
    "rym_album_details": rym_album_details,
    "rym_browse_charts": rym_browse_charts,
    "rym_advanced_search": rym_advanced_search,
    "rym_browse_artist": rym_browse_artist,
    "rym_browse_list": rym_browse_list,
    "rym_signup_form_validation": rym_signup_form_validation,
    "rym_help_center_topic": rym_help_center_topic,
}

def generate_rym_task(task_type: RYM_TASK_TYPES, payload: dict) -> dict:
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
    items = list(RYM_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_rym_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)