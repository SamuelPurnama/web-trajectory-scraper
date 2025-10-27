import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

BANDCAMP_TASK_TYPES = Literal[
    "bc_accept_cookies",
    "bc_search_artist_album_track",
    "bc_search_with_tag",
    "bc_filter_by_genre",
    "bc_filter_by_format",
    "bc_sort_results",
    "bc_browse_by_location",
    "bc_play_preview",
    "bc_signup_flow",
    "bc_view_bandcamp_daily_article",
    "bc_browse_merch_category",
    "bc_explore_editorial",
    "bc_browse_new_and_notable",
    "bc_browse_album_of_the_day",
]

BANDCAMP_SAMPLING_CONFIG: Dict[BANDCAMP_TASK_TYPES, int] = {
    "bc_accept_cookies": 10,
    "bc_search_artist_album_track": 10,
    "bc_search_with_tag": 10,
    "bc_filter_by_genre": 10,
    "bc_filter_by_format": 10,
    "bc_sort_results": 10,
    "bc_browse_by_location": 10,
    "bc_play_preview": 10,
    "bc_signup_flow": 10,
    "bc_view_bandcamp_daily_article": 10,
    "bc_browse_merch_category": 10,
    "bc_explore_editorial": 10,
    "bc_browse_new_and_notable": 10,
    "bc_browse_album_of_the_day": 10,
}

SEARCH_TERMS = [
    "Radiohead", "ambient", "lo-fi", "jazz", "punk", "shoegaze", "synthwave", "hip-hop", "folk",
    "metal", "indie pop", "dream pop", "breakcore", "future funk", "post-rock", "house", "techno",
    "experimental", "instrumental", "pop", "bedroom pop", "afrobeats", "funk", "electronic", "rock",
    "noise", "beat tape", "underground hip hop", "Berlin", "Tokyo", "Los Angeles", "Paris"
]

TAGS = [
    "chill", "female vocals", "instrumental", "live", "remix", "experimental", "vaporwave", "synth",
    "beats", "indie", "electronic", "ambient", "jazz", "punk", "metal", "pop", "rock", "lo-fi",
    "shoegaze", "hip-hop", "folk", "house", "techno", "breakcore", "future funk"
]

GENRES = [
    "electronic", "experimental", "alternative", "rock", "ambient", "hip-hop/rap", "metal", "punk",
    "techno", "noise", "indie", "jazz", "instrumental", "folk", "pop", "funk", "post-rock", "house",
    "lo-fi", "indie pop", "shoegaze", "synthwave", "underground hip hop", "dream pop", "breakcore",
    "bedroom pop", "ambient + field recordings", "beat tape", "afrobeats", "future funk", "broken beat"
]

FORMATS = [
    "all categories", "digital", "vinyl", "compact discs", "cassettes", "t-shirts", "gift cards",
    "merch", "CDs", "T-Shirts", "Vinyl", "Cassettes"
]

SORT_ORDERS = [
    "best-selling", "fresh", "new arrivals", "top rated", "most collected", "most played",
    "trending", "recommended", "recently added", "staff picks", "editor's choice", "popular",
    "featured", "classic", "underground", "experimental", "by location", "by genre", "by format", "random"
]

LOCATIONS = [
    "Los Angeles", "Berlin", "Paris", "Tokyo", "San Francisco", "Detroit", "São Paulo", "Hamburg",
    "Lisbon", "Singapore", "Buenos Aires", "Barcelona", "Vietnam", "Mexico City", "Lima", "Egypt",
    "London", "New York", "Chicago", "Toronto", "Sydney", "Seoul", "Moscow", "Cape Town", "Dublin"
]

MERCH_CATEGORIES = [
    "Vinyl", "CDs", "Cassettes", "T-Shirts", "Posters", "Stickers", "Hats", "Hoodies", "Pins",
    "Patches", "Zines", "Art Prints", "Tote Bags", "Socks", "Mugs", "Books", "Calendars", "Buttons",
    "Sweatshirts", "Masks", "Scarves", "Shoes", "Jewelry", "Accessories"
]

EDITORIAL_ARTICLES = [
    "The Best Hip-Hop on Bandcamp, October 2025",
    "Shoegaze, Post-Punk and Central America’s Echoing Melancholy",
    "Essential Releases, October 24, 2025",
    "All Boats Rise Together: How Dundalk’s Artists Built a Thriving Music Scene",
    "The Best Electronic on Bandcamp, September 2025",
    "Bandcamp Essentials: Dream Pop",
    "Bandcamp Essentials: Ambient",
    "Bandcamp Essentials: Jazz",
    "Bandcamp Essentials: Indie",
    "Bandcamp Essentials: Metal",
    "Bandcamp Essentials: Punk",
    "Bandcamp Essentials: Lo-fi",
    "Bandcamp Essentials: Synthwave",
    "Bandcamp Essentials: House",
    "Bandcamp Essentials: Techno",
    "Bandcamp Essentials: Experimental",
    "Bandcamp Essentials: Shoegaze",
    "Bandcamp Essentials: Post-Rock",
    "Bandcamp Essentials: Hip-Hop",
    "Bandcamp Essentials: Folk",
    "Bandcamp Essentials: Pop",
    "Bandcamp Essentials: Funk",
    "Bandcamp Essentials: Instrumental"
]

NEW_AND_NOTABLE = [
    "Korus Majken", "Time Is Coming To An End Glacis & Polaroid Notes", "The Barge of Sorrow JP Olsen",
    "Purity Ring Purity Ring", "4 Stages of Sleep Josi Miller", "Oneiric Rural Tapes",
    "Earth Is Begging Sunbörn Meets Clap! Clap!", "Mount Crystal Joviale", "Vibra Vibra Sha Ru",
    "Wake Up, Play Nice Ramonda Hammer", "Lost Within Loss", "Disorder", "feather river canyon blues",
    "Cone", "Dolphin 303 - Ataque de Nervios", "Musique - Keep On Jumpin' (we.amps re-edit)",
    "Frankie Knuckles - Your Love (we.amps remix)", "130 releases Full Discography"
]

ALBUM_OF_THE_DAY = [
    "Perera Elsewhere, “Just Wanna Live Some”", "JP Olsen, “The Barge of Sorrow”", "Purity Ring, “Purity Ring”",
    "Josi Miller, “4 Stages of Sleep”", "Sunbörn Meets Clap! Clap!, “Earth Is Begging”",
    "Joviale, “Mount Crystal”", "Sha Ru, “Vibra Vibra”", "Ramonda Hammer, “Wake Up, Play Nice”",
    "Glacis & Polaroid Notes, “Time Is Coming To An End”", "Majken, “Korus”", "Natalie Foss, “In Lieu”",
    "JP Olsen, “Disorder”", "Lost Within Loss", "feather river canyon blues", "Cone", "Dolphin 303 - Ataque de Nervios",
    "Musique - Keep On Jumpin' (we.amps re-edit)", "Frankie Knuckles - Your Love (we.amps remix)", "130 releases Full Discography"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss cookie banners or popups if present (e.g., 'We care about your privacy').",
        "Do not make any purchases or submit payment information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Bandcamp", steps).model_dump()

def bc_accept_cookies(_: dict) -> dict:
    steps = [
        "Go to url 'https://bandcamp.com/'.",
        "If a cookie consent dialog appears, click the button labeled 'Accept all'.",
        "Verify the dialog disappears and the main page is visible.",
    ]
    return {"task_type": "bc_accept_cookies", "steps": steps}

def bc_search_artist_album_track(_: dict) -> dict:
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://bandcamp.com/'.",
        *_ui_hygiene(),
        "Locate the search box labeled 'Search for artist, album or track'.",
        f"Type '{term}' into the search box.",
        "Click the 'Search' button or press Enter.",
        "Wait for the results page to load.",
        f"Verify that at least one result contains the term '{term}' in the artist, album, or track name.",
    ]
    return {"task_type": "bc_search_artist_album_track", "search_term": term, "steps": steps}

def bc_search_with_tag(_: dict) -> dict:
    tag = random.choice(TAGS)
    steps = [
        "Go to url 'https://bandcamp.com/discover'.",
        *_ui_hygiene(),
        "Locate the tag search box labeled 'Tag search (optional)'.",
        f"Type '{tag}' into the tag search box.",
        "Submit the tag search.",
        "Wait for the results to update.",
        f"Verify that the tag '{tag}' appears in the applied filters or in the results.",
    ]
    return {"task_type": "bc_search_with_tag", "tag": tag, "steps": steps}

def bc_filter_by_genre(_: dict) -> dict:
    genre = random.choice(GENRES)
    steps = [
        "Go to url 'https://bandcamp.com/discover'.",
        *_ui_hygiene(),
        "Locate and click the 'all genres' button or genre dropdown.",
        f"Select the genre '{genre}' from the list.",
        "Wait for the results to update.",
        f"Verify that the genre '{genre}' is shown as an active filter or in the results.",
    ]
    return {"task_type": "bc_filter_by_genre", "genre": genre, "steps": steps}

def bc_filter_by_format(_: dict) -> dict:
    fmt = random.choice(FORMATS)
    steps = [
        "Go to url 'https://bandcamp.com/discover'.",
        *_ui_hygiene(),
        "Locate the format/category filter (e.g., radio buttons for 'all categories', 'vinyl', etc.).",
        f"Select '{fmt}' as the format/category.",
        "Wait for the results to update.",
        f"Verify that the format/category '{fmt}' is shown as active or reflected in the results.",
    ]
    return {"task_type": "bc_filter_by_format", "format": fmt, "steps": steps}

def bc_sort_results(_: dict) -> dict:
    sort = random.choice(SORT_ORDERS)
    steps = [
        "Go to url 'https://bandcamp.com/discover'.",
        *_ui_hygiene(),
        "Locate the sort order dropdown or buttons (e.g., 'best-selling', 'fresh').",
        f"Select '{sort}' as the sort order.",
        "Wait for the results to update.",
        f"Verify that the results are sorted according to '{sort}' (e.g., check label or order).",
    ]
    return {"task_type": "bc_sort_results", "sort_order": sort, "steps": steps}

def bc_browse_by_location(_: dict) -> dict:
    loc = random.choice(LOCATIONS)
    steps = [
        "Go to url 'https://bandcamp.com/discover'.",
        *_ui_hygiene(),
        "Locate the location filter (e.g., button labeled 'artists from anywhere').",
        f"Select '{loc}' as the location.",
        "Wait for the results to update.",
        f"Verify that the location '{loc}' is shown as an active filter or reflected in the results.",
    ]
    return {"task_type": "bc_browse_by_location", "location": loc, "steps": steps}

def bc_play_preview(_: dict) -> dict:
    steps = [
        "Go to url 'https://bandcamp.com/'.",
        *_ui_hygiene(),
        "Scroll to the 'New and Notable' or 'What's New' section.",
        "Locate a visible album or track with a 'Play' button.",
        "Click the 'Play' button.",
        "Verify that audio playback starts (e.g., play indicator or progress bar appears).",
        "Pause playback and verify audio stops.",
    ]
    return {"task_type": "bc_play_preview", "steps": steps}

def bc_signup_flow(_: dict) -> dict:
    email = f"testuser{random.randint(1000,9999)}@example.com"
    steps = [
        "Go to url 'https://bandcamp.com/'.",
        *_ui_hygiene(),
        "Click the 'Sign up' menu item.",
        "On the sign-up page, locate the email address field.",
        f"Enter '{email}' as the email address.",
        "Attempt to submit the form without filling other required fields.",
        "Verify that an error message appears indicating missing or invalid information.",
    ]
    return {"task_type": "bc_signup_flow", "test_email": email, "steps": steps}

def bc_view_bandcamp_daily_article(_: dict) -> dict:
    article = random.choice(EDITORIAL_ARTICLES)
    steps = [
        "Go to url 'https://bandcamp.com/'.",
        *_ui_hygiene(),
        "Scroll to the 'Bandcamp Daily' section.",
        f"Locate and click the article titled '{article}'.",
        "Wait for the article page to load.",
        f"Verify that the article title '{article}' appears at the top of the page.",
    ]
    return {"task_type": "bc_view_bandcamp_daily_article", "article_title": article, "steps": steps}

def bc_browse_merch_category(_: dict) -> dict:
    merch = random.choice(MERCH_CATEGORIES)
    steps = [
        "Go to url 'https://bandcamp.com/'.",
        *_ui_hygiene(),
        "Scroll to the 'Discover merch' section.",
        f"Click the link labeled '{merch}' (or the closest match if not present).",
        "Wait for the merch category page to load.",
        f"Verify that the page displays items in the '{merch}' category.",
    ]
    return {"task_type": "bc_browse_merch_category", "merch_category": merch, "steps": steps}

def bc_explore_editorial(_: dict) -> dict:
    steps = [
        "Go to url 'https://bandcamp.com/'.",
        *_ui_hygiene(),
        "Scroll to the 'Bandcamp Daily' section.",
        "Click the link labeled 'Explore more editorial'.",
        "Wait for the editorial page to load.",
        "Verify that a list of editorial articles is displayed.",
    ]
    return {"task_type": "bc_explore_editorial", "steps": steps}

def bc_browse_new_and_notable(_: dict) -> dict:
    notable = random.choice(NEW_AND_NOTABLE)
    steps = [
        "Go to url 'https://bandcamp.com/'.",
        *_ui_hygiene(),
        "Scroll to the 'New and Notable' section.",
        f"Locate and click the link for '{notable}'.",
        "Wait for the album or track page to load.",
        f"Verify that the album or track title '{notable}' appears on the page.",
    ]
    return {"task_type": "bc_browse_new_and_notable", "item": notable, "steps": steps}

def bc_browse_album_of_the_day(_: dict) -> dict:
    album = random.choice(ALBUM_OF_THE_DAY)
    steps = [
        "Go to url 'https://bandcamp.com/'.",
        *_ui_hygiene(),
        "Scroll to the 'Album of the Day' section.",
        f"Locate and click the link for '{album}'.",
        "Wait for the album page to load.",
        f"Verify that the album title '{album}' appears on the page.",
    ]
    return {"task_type": "bc_browse_album_of_the_day", "album": album, "steps": steps}

_TASK_GENERATORS: Dict[BANDCAMP_TASK_TYPES, Callable[[dict], dict]] = {
    "bc_accept_cookies": bc_accept_cookies,
    "bc_search_artist_album_track": bc_search_artist_album_track,
    "bc_search_with_tag": bc_search_with_tag,
    "bc_filter_by_genre": bc_filter_by_genre,
    "bc_filter_by_format": bc_filter_by_format,
    "bc_sort_results": bc_sort_results,
    "bc_browse_by_location": bc_browse_by_location,
    "bc_play_preview": bc_play_preview,
    "bc_signup_flow": bc_signup_flow,
    "bc_view_bandcamp_daily_article": bc_view_bandcamp_daily_article,
    "bc_browse_merch_category": bc_browse_merch_category,
    "bc_explore_editorial": bc_explore_editorial,
    "bc_browse_new_and_notable": bc_browse_new_and_notable,
    "bc_browse_album_of_the_day": bc_browse_album_of_the_day,
}

def generate_bandcamp_task(task_type: BANDCAMP_TASK_TYPES, payload: dict) -> dict:
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
    items = list(BANDCAMP_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_bandcamp_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)