import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

SPOTIFY_TASK_TYPES = Literal[
    "spotify_search_song",
    "spotify_search_artist",
    "spotify_search_album",
    "spotify_search_playlist",
    "spotify_browse_genre",
    "spotify_browse_mood",
    "spotify_play_preview",
    "spotify_check_unsupported_browser_banner",
    "spotify_download_app_link",
    "spotify_learn_more_link",
    "spotify_filter_search_results",
]

SPOTIFY_SAMPLING_CONFIG: Dict[SPOTIFY_TASK_TYPES, int] = {
    "spotify_search_song": 10,
    "spotify_search_artist": 10,
    "spotify_search_album": 10,
    "spotify_search_playlist": 10,
    "spotify_browse_genre": 10,
    "spotify_browse_mood": 10,
    "spotify_play_preview": 10,
    "spotify_check_unsupported_browser_banner": 10,
    "spotify_download_app_link": 10,
    "spotify_learn_more_link": 10,
    "spotify_filter_search_results": 10,
}

SONG_SEARCH_TERMS = [
    "Shape of You", "Blinding Lights", "Bohemian Rhapsody", "Bad Guy", "Old Town Road",
    "Levitating", "Dance Monkey", "Havana", "Sunflower", "Perfect",
    "Senorita", "Believer", "Rockstar", "Someone You Loved", "One Dance",
    "Closer", "Girls Like You", "God's Plan", "Lucid Dreams", "Despacito",
    "Stay", "Peaches", "Heat Waves", "Save Your Tears", "Shallow",
    "Faded", "Memories", "Don't Start Now", "Stressed Out", "Sicko Mode",
]

ARTIST_SEARCH_TERMS = [
    "Ed Sheeran", "Dua Lipa", "The Weeknd", "Billie Eilish", "Queen",
    "Drake", "Ariana Grande", "Post Malone", "Imagine Dragons", "BTS",
    "Taylor Swift", "Justin Bieber", "Shawn Mendes", "Maroon 5", "Khalid",
    "Camila Cabello", "Travis Scott", "Selena Gomez", "Juice WRLD", "Olivia Rodrigo",
    "Bruno Mars", "Harry Styles", "Doja Cat", "Sia", "Coldplay",
    "Lil Nas X", "Lizzo", "Sam Smith", "Halsey", "Katy Perry",
]

ALBUM_SEARCH_TERMS = [
    "Divide", "Future Nostalgia", "After Hours", "When We All Fall Asleep, Where Do We Go?", "A Night at the Opera",
    "Scorpion", "thank u, next", "Hollywood's Bleeding", "Evolve", "Map of the Soul: 7",
    "Lover", "Justice", "Shawn Mendes", "Red Pill Blues", "Free Spirit",
    "Romance", "Astroworld", "Rare", "Goodbye & Good Riddance", "SOUR",
    "24K Magic", "Fine Line", "Planet Her", "This Is Acting", "Music of the Spheres",
    "Montero", "Cuz I Love You", "In the Lonely Hour", "Manic", "Smile",
]

PLAYLIST_SEARCH_TERMS = [
    "Today's Top Hits", "RapCaviar", "Hot Country", "Rock Classics", "Peaceful Piano",
    "Chill Hits", "All Out 80s", "Mood Booster", "Songs to Sing in the Car", "Pop Rising",
    "Beast Mode", "Viva Latino", "Are & Be", "mint", "Happy Hits!",
    "Throwback Hits", "Dance Party", "Confidence Boost", "Deep Focus", "Sad Songs",
    "Mega Hit Mix", "Good Vibes", "Feelin' Good", "Summer Hits", "Indie Pop",
    "Power Workout", "Sleep", "Acoustic Hits", "Workout", "Evening Chill",
]

GENRES = [
    "Pop", "Hip-Hop", "Rock", "Country", "EDM", "Jazz", "Classical", "R&B", "Latin", "Indie",
    "Metal", "Reggae", "Folk", "Blues", "Soul", "Punk", "Funk", "Gospel", "K-Pop", "World",
    "Alternative", "Disco", "House", "Techno", "Trap",
]

MOODS = [
    "Happy", "Sad", "Chill", "Energetic", "Romantic", "Focus", "Party", "Workout", "Sleep", "Motivation",
    "Relax", "Melancholy", "Upbeat", "Calm", "Groovy", "Epic", "Dreamy", "Dark", "Feel Good", "Angry",
    "Peaceful", "Nostalgic", "Confident", "Hopeful", "In Love",
]

FILTERS = [
    "Sort by popularity", "Sort by release date", "Sort by relevance", "Show only explicit", "Show only non-explicit",
    "Show only singles", "Show only albums", "Show only podcasts", "Show only verified artists", "Show only playlists",
    "Show only tracks", "Show only videos", "Show only user playlists", "Show only editorial playlists",
    "Show only local results", "Show only global results", "Show only new releases", "Show only top results",
    "Show only trending", "Show only recommended", "Show only radio", "Show only recently played", "Show only liked songs",
    "Show only collaborative playlists", "Show only public playlists",
]

def _ui_hygiene() -> list[str]:
    return [
        "If any popups or banners appear, dismiss them (e.g., cookie notice, unsupported browser).",
        "Do not attempt to sign in or provide personal information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Spotify", steps).model_dump()

def spotify_search_song(_: dict) -> dict:
    term = random.choice(SONG_SEARCH_TERMS)
    steps = [
        "Go to url 'https://open.spotify.com'.",
        *_ui_hygiene(),
        "Locate the search field (magnifying glass icon or 'Search' label).",
        f"Type '{term}' into the search field and submit.",
        "Wait for results to load.",
        f"Assert that a song result matching '{term}' appears in the results list.",
        "Do not click play or sign in.",
    ]
    return {"task_type": "spotify_search_song", "search_term": term, "steps": steps}

def spotify_search_artist(_: dict) -> dict:
    term = random.choice(ARTIST_SEARCH_TERMS)
    steps = [
        "Go to url 'https://open.spotify.com'.",
        *_ui_hygiene(),
        "Locate the search field (magnifying glass icon or 'Search' label).",
        f"Type '{term}' into the search field and submit.",
        "Wait for results to load.",
        f"Assert that an artist result matching '{term}' appears in the results list.",
        "Do not click play or sign in.",
    ]
    return {"task_type": "spotify_search_artist", "search_term": term, "steps": steps}

def spotify_search_album(_: dict) -> dict:
    term = random.choice(ALBUM_SEARCH_TERMS)
    steps = [
        "Go to url 'https://open.spotify.com'.",
        *_ui_hygiene(),
        "Locate the search field (magnifying glass icon or 'Search' label).",
        f"Type '{term}' into the search field and submit.",
        "Wait for results to load.",
        f"Assert that an album result matching '{term}' appears in the results list.",
        "Do not click play or sign in.",
    ]
    return {"task_type": "spotify_search_album", "search_term": term, "steps": steps}

def spotify_search_playlist(_: dict) -> dict:
    term = random.choice(PLAYLIST_SEARCH_TERMS)
    steps = [
        "Go to url 'https://open.spotify.com'.",
        *_ui_hygiene(),
        "Locate the search field (magnifying glass icon or 'Search' label).",
        f"Type '{term}' into the search field and submit.",
        "Wait for results to load.",
        f"Assert that a playlist result matching '{term}' appears in the results list.",
        "Do not click play or sign in.",
    ]
    return {"task_type": "spotify_search_playlist", "search_term": term, "steps": steps}

def spotify_browse_genre(_: dict) -> dict:
    genre = random.choice(GENRES)
    steps = [
        "Go to url 'https://open.spotify.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Search' navigation item.",
        "Wait for the genre/mood browser to load.",
        f"Find and click the '{genre}' genre card.",
        f"Assert that the page header or main section shows '{genre}'.",
        "Do not click play or sign in.",
    ]
    return {"task_type": "spotify_browse_genre", "genre": genre, "steps": steps}

def spotify_browse_mood(_: dict) -> dict:
    mood = random.choice(MOODS)
    steps = [
        "Go to url 'https://open.spotify.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Search' navigation item.",
        "Wait for the genre/mood browser to load.",
        f"Find and click the '{mood}' mood card.",
        f"Assert that the page header or main section shows '{mood}'.",
        "Do not click play or sign in.",
    ]
    return {"task_type": "spotify_browse_mood", "mood": mood, "steps": steps}

def spotify_play_preview(_: dict) -> dict:
    term = random.choice(SONG_SEARCH_TERMS)
    steps = [
        "Go to url 'https://open.spotify.com'.",
        *_ui_hygiene(),
        "Locate the search field (magnifying glass icon or 'Search' label).",
        f"Type '{term}' into the search field and submit.",
        "Wait for results to load.",
        f"Locate the first song result for '{term}'.",
        "If a play preview button is available (e.g., play icon on the song card), click it.",
        "Assert that playback starts (e.g., progress bar moves, play icon changes to pause).",
        "Do not sign in or attempt to play full tracks.",
    ]
    return {"task_type": "spotify_play_preview", "search_term": term, "steps": steps}

def spotify_check_unsupported_browser_banner(_: dict) -> dict:
    steps = [
        "Go to url 'https://open.spotify.com'.",
        *_ui_hygiene(),
        "Check for a heading or banner with text 'Unsupported browser'.",
        "Assert that the text 'Spotify is unavailable on this browser.' is visible.",
        "Assert that links 'Get the App' and 'Learn more' are present.",
    ]
    return {"task_type": "spotify_check_unsupported_browser_banner", "steps": steps}

def spotify_download_app_link(_: dict) -> dict:
    steps = [
        "Go to url 'https://open.spotify.com'.",
        *_ui_hygiene(),
        "Locate the link labeled 'Get the App'.",
        "Click the 'Get the App' link.",
        "Assert that the new page or modal contains download options for Spotify (e.g., Windows, Mac, mobile).",
        "Do not download or install anything.",
    ]
    return {"task_type": "spotify_download_app_link", "steps": steps}

def spotify_learn_more_link(_: dict) -> dict:
    steps = [
        "Go to url 'https://open.spotify.com'.",
        *_ui_hygiene(),
        "Locate the link labeled 'Learn more'.",
        "Click the 'Learn more' link.",
        "Assert that the new page or modal contains information about browser support or troubleshooting.",
        "Do not attempt to sign in or provide personal information.",
    ]
    return {"task_type": "spotify_learn_more_link", "steps": steps}

def spotify_filter_search_results(_: dict) -> dict:
    filter_opt = random.choice(FILTERS)
    term = random.choice(SONG_SEARCH_TERMS + ARTIST_SEARCH_TERMS + ALBUM_SEARCH_TERMS + PLAYLIST_SEARCH_TERMS)
    steps = [
        "Go to url 'https://open.spotify.com'.",
        *_ui_hygiene(),
        "Locate the search field (magnifying glass icon or 'Search' label).",
        f"Type '{term}' into the search field and submit.",
        "Wait for results to load.",
        f"Apply the filter: {filter_opt}.",
        f"Assert that the results update according to '{filter_opt}'.",
        "Do not click play or sign in.",
    ]
    return {"task_type": "spotify_filter_search_results", "search_term": term, "filter": filter_opt, "steps": steps}

_TASK_GENERATORS: Dict[SPOTIFY_TASK_TYPES, Callable[[dict], dict]] = {
    "spotify_search_song": spotify_search_song,
    "spotify_search_artist": spotify_search_artist,
    "spotify_search_album": spotify_search_album,
    "spotify_search_playlist": spotify_search_playlist,
    "spotify_browse_genre": spotify_browse_genre,
    "spotify_browse_mood": spotify_browse_mood,
    "spotify_play_preview": spotify_play_preview,
    "spotify_check_unsupported_browser_banner": spotify_check_unsupported_browser_banner,
    "spotify_download_app_link": spotify_download_app_link,
    "spotify_learn_more_link": spotify_learn_more_link,
    "spotify_filter_search_results": spotify_filter_search_results,
}

def generate_spotify_task(task_type: SPOTIFY_TASK_TYPES, payload: dict) -> dict:
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
    items = list(SPOTIFY_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_spotify_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)