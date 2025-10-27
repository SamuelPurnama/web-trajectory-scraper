import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

AOTY_TASK_TYPES = Literal[
    "aoty_search_album",
    "aoty_search_artist",
    "aoty_browse_genre",
    "aoty_filter_by_year",
    "aoty_filter_by_decade",
    "aoty_filter_by_min_reviews",
    "aoty_browse_must_hear",
    "aoty_browse_recently_rated",
    "aoty_album_details_external_links",
    "aoty_album_details_recommendations",
    "aoty_browse_publication_list",
    "aoty_toggle_user_score",
    "aoty_browse_new_releases",
    "aoty_browse_lists",
    "aoty_browse_discover",
    "aoty_browse_community",
    "aoty_browse_news",
    "aoty_become_donor",
]

AOTY_SAMPLING_CONFIG: Dict[AOTY_TASK_TYPES, int] = {
    "aoty_search_album": 10,
    "aoty_search_artist": 10,
    "aoty_browse_genre": 10,
    "aoty_filter_by_year": 10,
    "aoty_filter_by_decade": 10,
    "aoty_filter_by_min_reviews": 10,
    "aoty_browse_must_hear": 10,
    "aoty_browse_recently_rated": 10,
    "aoty_album_details_external_links": 10,
    "aoty_album_details_recommendations": 10,
    "aoty_browse_publication_list": 10,
    "aoty_toggle_user_score": 10,
    "aoty_browse_new_releases": 10,
    "aoty_browse_lists": 10,
    "aoty_browse_discover": 10,
    "aoty_browse_community": 10,
    "aoty_browse_news": 10,
    "aoty_become_donor": 10,
}

# 20+ search terms for albums and artists
ALBUM_SEARCH_TERMS = [
    "Blonde", "To Pimp a Butterfly", "Random Access Memories", "DAMN.", "Melodrama", "Currents", "Good Kid, M.A.A.D City", "After Hours", "Norman Fucking Rockwell", "Fetch the Bolt Cutters",
    "SOUR", "Igor", "A Moon Shaped Pool", "RTJ4", "Flower Boy", "Future Nostalgia", "Fine Line", "Beerbongs & Bentleys", "Astroworld", "When We All Fall Asleep, Where Do We Go?",
    "The Slow Rush", "Evermore", "Folklore", "Map of the Soul: 7", "Hollywood's Bleeding"
]
ARTIST_SEARCH_TERMS = [
    "Kendrick Lamar", "Taylor Swift", "Lorde", "Tyler, The Creator", "Billie Eilish", "The Weeknd", "Adele", "Drake", "Beyoncé", "Arctic Monkeys",
    "Radiohead", "SZA", "Phoebe Bridgers", "Dua Lipa", "Frank Ocean", "Harry Styles", "Post Malone", "Travis Scott", "FKA twigs", "Mitski",
    "Vampire Weekend", "Lana Del Rey", "St. Vincent", "Childish Gambino", "Paramore"
]

# 20+ genres
GENRES = [
    "Alternative Rock", "Indie Rock", "Hip Hop", "Pop", "Electronic", "R&B", "Folk", "Jazz", "Metal", "Punk",
    "Country", "Soul", "Experimental", "Singer-Songwriter", "Dance", "Ambient", "Hard Rock", "Psychedelic", "Blues", "Reggae",
    "Industrial", "Classical", "Trap", "Synthpop", "Garage Rock"
]

# 20+ years and decades
YEARS = [str(y) for y in range(2000, 2025)]
DECADES = ["1970s", "1980s", "1990s", "2000s", "2010s", "2020s", "1960s", "1950s", "1940s", "1930s",
           "1920s", "1910s", "1900s", "1890s", "1880s", "1870s", "1860s", "1850s", "1840s", "1830s"]

# 20+ min reviews options
MIN_REVIEWS = [str(n) for n in range(1, 21)]

# 20+ publication lists
PUBLICATION_LISTS = [
    "Pitchfork's Highest Rated Albums of 2023", "The Needle Drop's Highest Rated Albums of 2022", "Rolling Stone's Best Albums of 2021",
    "NME's Best Albums of 2020", "Consequence's Top Albums of 2019", "Billboard's Best Albums of 2018", "Spin's Best Albums of 2017",
    "The Guardian's Best Albums of 2016", "AllMusic's Best Albums of 2015", "Stereogum's Best Albums of 2014",
    "Paste's Best Albums of 2013", "Mojo's Best Albums of 2012", "Uncut's Best Albums of 2011", "Q Magazine's Best Albums of 2010",
    "BBC's Best Albums of 2009", "PopMatters' Best Albums of 2008", "Slant's Best Albums of 2007", "Tiny Mix Tapes' Best Albums of 2006",
    "Drowned in Sound's Best Albums of 2005", "Fact's Best Albums of 2004", "Spin's Best Albums of 2003", "Rolling Stone's Best Albums of 2002"
]

# 20+ community/discover/news/list sections
COMMUNITY_SECTIONS = [
    "Forums", "Album Discussions", "Artist Discussions", "Site Feedback", "Rankings", "User Reviews", "Lists", "Polls",
    "Recommendations", "Music News", "Release Calendar", "Contests", "Events", "User Rankings", "Genre Discussions", "Site Announcements",
    "Album of the Year", "Staff Picks", "User Lists", "Top Users", "Recent Activity"
]
DISCOVER_SECTIONS = [
    "Trending Albums", "New Artists", "Hidden Gems", "Staff Picks", "Most Anticipated", "Top Debuts", "Under the Radar", "Genre Spotlights",
    "Emerging Artists", "Top Singles", "Editor's Picks", "Breakout Albums", "Classic Albums", "Cult Favorites", "Viral Albums", "Global Picks",
    "Fan Favorites", "Reissues", "Remastered Albums", "Soundtrack Highlights", "Indie Discoveries"
]
NEWS_SECTIONS = [
    "Album Announcements", "Artist Interviews", "Music Industry News", "Award Shows", "Tour Announcements", "Festival Lineups",
    "Chart Updates", "Release Delays", "Obituaries", "Album Leaks", "Music Videos", "Song Premieres", "Critical Reception",
    "Streaming Updates", "Vinyl Releases", "Remix News", "Collaboration Announcements", "Music Documentaries", "Reunion News",
    "Breakup Announcements", "Charity Releases"
]
LISTS_SECTIONS = [
    "Top 50 Albums", "Top 100 Albums", "Best Debut Albums", "Best Comeback Albums", "Best Live Albums", "Best EPs", "Best Soundtracks",
    "Best Concept Albums", "Best Cover Albums", "Best Compilation Albums", "Best Albums by Women", "Best Albums by Decade",
    "Best Albums by Genre", "Best Albums by Year", "Best Albums by Country", "Best Albums by Label", "Most Overrated Albums",
    "Most Underrated Albums", "Most Influential Albums", "Best Album Art", "Best Produced Albums"
]

# 20+ must-hear/recently rated album titles (for navigation)
MUST_HEAR_ALBUMS = [
    "Ego Death At A Bachelorette Party", "Son Of Spergy", "The Boy Who Played the Harp", "The Slow Rush", "Fetch the Bolt Cutters",
    "Future Nostalgia", "RTJ4", "Fine Line", "Astroworld", "Beerbongs & Bentleys", "Currents", "DAMN.", "Igor", "Melodrama",
    "Norman Fucking Rockwell", "Good Kid, M.A.A.D City", "Flower Boy", "Evermore", "Folklore", "Hollywood's Bleeding",
    "Map of the Soul: 7", "Random Access Memories", "SOUR", "A Moon Shaped Pool", "Blonde"
]
RECENTLY_RATED_ALBUMS = [
    "The Car", "Midnights", "SOS", "Mr. Morale & the Big Steppers", "Renaissance", "Un Verano Sin Ti", "Harry's House", "Motomami",
    "Gemini Rights", "Dragon New Warm Mountain I Believe In You", "Blue Rev", "Caprisongs", "Laurel Hell", "Crash", "Big Time",
    "Being Funny in a Foreign Language", "Dawn FM", "Ants From Up There", "Wet Leg", "Skinty Fia", "Once Twice Melody", "Lucifer on the Sofa"
]

# 20+ genres for album details page (for genre link navigation)
ALBUM_DETAIL_GENRES = GENRES

# 20+ external links types
EXTERNAL_LINKS = ["Amazon", "Apple Music", "Spotify", "Bandcamp", "YouTube Music", "Tidal", "Deezer", "SoundCloud", "Napster", "Qobuz",
    "Google Play Music", "Pandora", "iTunes", "Discogs", "Last.fm", "eMusic", "Beatport", "7digital", "Audiomack", "Boomplay"
]

# 20+ recommendations (album titles)
RECOMMENDATIONS = [
    "Son Of Spergy", "The Boy Who Played the Harp", "Future Nostalgia", "RTJ4", "Fine Line", "Astroworld", "Beerbongs & Bentleys",
    "Currents", "DAMN.", "Igor", "Melodrama", "Norman Fucking Rockwell", "Good Kid, M.A.A.D City", "Flower Boy", "Evermore",
    "Folklore", "Hollywood's Bleeding", "Map of the Soul: 7", "Random Access Memories", "SOUR", "A Moon Shaped Pool", "Blonde"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, newsletter prompts).",
        "Do not sign up, log in, or make purchases.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Album of the Year", steps).model_dump()

def aoty_search_album(_: dict) -> dict:
    term = random.choice(ALBUM_SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Focus the search box labeled 'Search albums, artists, genres etc.'.",
        f"Type '{term}' and submit the search (e.g., click magnifying glass or press Enter).",
        "Wait for the search results to load.",
        f"Verify that at least one album result contains '{term}' (case-insensitive).",
        "If no results, verify that a 'No results' or similar message is shown.",
    ]
    return {"task_type": "aoty_search_album", "search_term": term, "steps": steps}

def aoty_search_artist(_: dict) -> dict:
    term = random.choice(ARTIST_SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Focus the search box labeled 'Search albums, artists, genres etc.'.",
        f"Type '{term}' and submit the search.",
        "Wait for the search results to load.",
        f"Verify that at least one artist or album result contains '{term}' (case-insensitive).",
        "If no results, verify that a 'No results' or similar message is shown.",
    ]
    return {"task_type": "aoty_search_artist", "search_term": term, "steps": steps}

def aoty_browse_genre(_: dict) -> dict:
    genre = random.choice(GENRES)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Open the 'Genres' menu in the top navigation.",
        f"Select the genre '{genre}'.",
        "Wait for the genre page to load.",
        f"Verify that the page title or heading includes '{genre}'.",
        "Verify that at least one album listed is tagged with '{genre}'.",
    ]
    return {"task_type": "aoty_browse_genre", "genre": genre, "steps": steps}

def aoty_filter_by_year(_: dict) -> dict:
    year = random.choice(YEARS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Navigate to the 'Best Albums' section.",
        "Locate the year filter (e.g., links labeled with years).",
        f"Click the link for year '{year}'.",
        "Wait for the filtered album list to load.",
        f"Verify that the page or album list is filtered to '{year}'.",
        "Check that at least one album is shown for that year.",
    ]
    return {"task_type": "aoty_filter_by_year", "year": year, "steps": steps}

def aoty_filter_by_decade(_: dict) -> dict:
    decade = random.choice(DECADES)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Navigate to the 'Best Albums' section.",
        "Locate the decade filter (e.g., links labeled with decades).",
        f"Click the link for decade '{decade}'.",
        "Wait for the filtered album list to load.",
        f"Verify that the page or album list is filtered to '{decade}'.",
        "Check that at least one album is shown for that decade.",
    ]
    return {"task_type": "aoty_filter_by_decade", "decade": decade, "steps": steps}

def aoty_filter_by_min_reviews(_: dict) -> dict:
    min_reviews = random.choice(MIN_REVIEWS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Navigate to the 'Best Albums' section.",
        "Locate the filter dropdown labeled 'MIN. REVIEWS'.",
        f"Open the dropdown and select '{min_reviews}'.",
        "Wait for the album list to update.",
        f"Verify that all albums shown have at least {min_reviews} critic reviews (if review counts are visible).",
        "If not possible to verify, confirm the filter value is applied in the UI.",
    ]
    return {"task_type": "aoty_filter_by_min_reviews", "min_reviews": min_reviews, "steps": steps}

def aoty_browse_must_hear(_: dict) -> dict:
    album = random.choice(MUST_HEAR_ALBUMS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Locate and click the 'MUST HEAR' link in the navigation or sidebar.",
        "Wait for the must-hear albums page to load.",
        f"Verify that album '{album}' is present in the list (case-insensitive).",
        "If not present, verify at least 10 albums are shown on the page.",
    ]
    return {"task_type": "aoty_browse_must_hear", "album": album, "steps": steps}

def aoty_browse_recently_rated(_: dict) -> dict:
    album = random.choice(RECENTLY_RATED_ALBUMS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Locate and click the 'RECENTLY RATED' link in the navigation or sidebar.",
        "Wait for the recently rated albums page to load.",
        f"Verify that album '{album}' is present in the list (case-insensitive).",
        "If not present, verify at least 10 albums are shown on the page.",
    ]
    return {"task_type": "aoty_browse_recently_rated", "album": album, "steps": steps}

def aoty_album_details_external_links(_: dict) -> dict:
    album = random.choice(MUST_HEAR_ALBUMS + RECENTLY_RATED_ALBUMS)
    service = random.choice(EXTERNAL_LINKS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Search for the album by title using the search box.",
        f"Type '{album}' and submit the search.",
        "In the results, click on the album title to open its detail page.",
        f"On the album detail page, locate and click the external link for '{service}'.",
        f"Verify that clicking the link opens the album on '{service}' in a new tab or window.",
        "If the link is not present, verify that at least one external music service link is shown.",
    ]
    return {"task_type": "aoty_album_details_external_links", "album": album, "service": service, "steps": steps}

def aoty_album_details_recommendations(_: dict) -> dict:
    album = random.choice(MUST_HEAR_ALBUMS + RECENTLY_RATED_ALBUMS)
    rec = random.choice(RECOMMENDATIONS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Search for the album by title using the search box.",
        f"Type '{album}' and submit the search.",
        "In the results, click on the album title to open its detail page.",
        "Scroll to the 'YOU MAY ALSO LIKE' or recommendations section.",
        f"Verify that '{rec}' is present as a recommendation (case-insensitive).",
        "If not present, verify that at least 3 recommendations are shown.",
        "Click on any recommendation and verify that it opens the corresponding album detail page.",
    ]
    return {"task_type": "aoty_album_details_recommendations", "album": album, "recommendation": rec, "steps": steps}

def aoty_browse_publication_list(_: dict) -> dict:
    pub = random.choice(PUBLICATION_LISTS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Navigate to the 'Lists' section in the top navigation.",
        "Locate the subsection for publication lists (e.g., 'Pitchfork', 'The Needle Drop', etc.).",
        f"Click on '{pub}'.",
        "Wait for the publication list page to load.",
        f"Verify that the page heading includes '{pub.split('\'')[0]}' (case-insensitive).",
        "Verify that at least 5 albums are listed.",
    ]
    return {"task_type": "aoty_browse_publication_list", "publication": pub, "steps": steps}

def aoty_toggle_user_score(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Navigate to the 'Best Albums' or main album ranking page.",
        "Locate the toggle or link labeled 'USER SCORE'.",
        "Click 'USER SCORE' to switch to user-based album rankings.",
        "Verify that the album list updates to reflect user scores (e.g., column or heading changes).",
        "Click 'CRITIC SCORE' to switch back and verify the list updates accordingly.",
    ]
    return {"task_type": "aoty_toggle_user_score", "steps": steps}

def aoty_browse_new_releases(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Click the 'New Releases' link in the top navigation.",
        "Wait for the new releases page to load.",
        "Verify that at least 10 new albums are listed with release dates within the last 30 days.",
        "For one album, verify that its release date is not in the future.",
    ]
    return {"task_type": "aoty_browse_new_releases", "steps": steps}

def aoty_browse_lists(_: dict) -> dict:
    section = random.choice(LISTS_SECTIONS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Click the 'Lists' link in the top navigation.",
        "Wait for the lists page to load.",
        f"Locate and click the list titled '{section}'.",
        "Verify that the page heading matches the list name.",
        "Verify that at least 5 albums are shown in the list.",
    ]
    return {"task_type": "aoty_browse_lists", "list_section": section, "steps": steps}

def aoty_browse_discover(_: dict) -> dict:
    section = random.choice(DISCOVER_SECTIONS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Click the 'Discover' link in the top navigation.",
        "Wait for the discover page to load.",
        f"Locate the section '{section}'.",
        f"Verify that at least 3 albums or artists are shown in '{section}'.",
    ]
    return {"task_type": "aoty_browse_discover", "discover_section": section, "steps": steps}

def aoty_browse_community(_: dict) -> dict:
    section = random.choice(COMMUNITY_SECTIONS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Click the 'Community' link in the top navigation.",
        "Wait for the community page to load.",
        f"Locate the section '{section}'.",
        f"Verify that the section '{section}' is present and contains at least one post, thread, or item.",
    ]
    return {"task_type": "aoty_browse_community", "community_section": section, "steps": steps}

def aoty_browse_news(_: dict) -> dict:
    section = random.choice(NEWS_SECTIONS)
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Click the 'News' link in the top navigation.",
        "Wait for the news page to load.",
        f"Locate the section or article titled '{section}'.",
        f"Verify that at least one news article is present in '{section}' or that the section exists.",
    ]
    return {"task_type": "aoty_browse_news", "news_section": section, "steps": steps}

def aoty_become_donor(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.albumoftheyear.org/'.",
        *_ui_hygiene(),
        "Locate the link labeled 'Become a Donor' (may include a badge or description).",
        "Click the 'Become a Donor' link.",
        "Wait for the donor/support page to load.",
        "Verify that the page contains information about donor benefits (e.g., 'no ads', 'donor badge').",
        "Do not enter payment or personal information.",
    ]
    return {"task_type": "aoty_become_donor", "steps": steps}

_TASK_GENERATORS: Dict[AOTY_TASK_TYPES, Callable[[dict], dict]] = {
    "aoty_search_album": aoty_search_album,
    "aoty_search_artist": aoty_search_artist,
    "aoty_browse_genre": aoty_browse_genre,
    "aoty_filter_by_year": aoty_filter_by_year,
    "aoty_filter_by_decade": aoty_filter_by_decade,
    "aoty_filter_by_min_reviews": aoty_filter_by_min_reviews,
    "aoty_browse_must_hear": aoty_browse_must_hear,
    "aoty_browse_recently_rated": aoty_browse_recently_rated,
    "aoty_album_details_external_links": aoty_album_details_external_links,
    "aoty_album_details_recommendations": aoty_album_details_recommendations,
    "aoty_browse_publication_list": aoty_browse_publication_list,
    "aoty_toggle_user_score": aoty_toggle_user_score,
    "aoty_browse_new_releases": aoty_browse_new_releases,
    "aoty_browse_lists": aoty_browse_lists,
    "aoty_browse_discover": aoty_browse_discover,
    "aoty_browse_community": aoty_browse_community,
    "aoty_browse_news": aoty_browse_news,
    "aoty_become_donor": aoty_become_donor,
}

def generate_aoty_task(task_type: AOTY_TASK_TYPES, payload: dict) -> dict:
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
    items = list(AOTY_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_aoty_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)