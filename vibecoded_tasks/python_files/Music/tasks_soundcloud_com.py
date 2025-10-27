import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

SOUNDCLOUD_TASK_TYPES = Literal[
    "soundcloud_search_track",
    "soundcloud_search_artist",
    "soundcloud_search_playlist",
    "soundcloud_playback_controls",
    "soundcloud_queue_management",
    "soundcloud_language_switch",
    "soundcloud_account_signup",
    "soundcloud_signin_modal",
    "soundcloud_navigation_links",
    "soundcloud_trending_explore",
    "soundcloud_app_download_links",
    "soundcloud_artist_profile_link",
    "soundcloud_promotional_banner",
    "soundcloud_settings_menu",
]

SOUNDCLOUD_SAMPLING_CONFIG: Dict[SOUNDCLOUD_TASK_TYPES, int] = {
    "soundcloud_search_track": 10,
    "soundcloud_search_artist": 10,
    "soundcloud_search_playlist": 10,
    "soundcloud_playback_controls": 10,
    "soundcloud_queue_management": 10,
    "soundcloud_language_switch": 10,
    "soundcloud_account_signup": 10,
    "soundcloud_signin_modal": 10,
    "soundcloud_navigation_links": 10,
    "soundcloud_trending_explore": 10,
    "soundcloud_app_download_links": 10,
    "soundcloud_artist_profile_link": 10,
    "soundcloud_promotional_banner": 10,
    "soundcloud_settings_menu": 10,
}

SEARCH_TERMS = [
    "lofi", "jazz", "hip hop", "classical", "pop", "rock", "edm", "ambient", "podcast", "indie",
    "electronic", "trap", "house", "dubstep", "country", "metal", "reggae", "folk", "blues", "k-pop",
    "r&b", "chill", "study music", "gaming", "instrumental", "soundtrack", "acoustic", "dance", "techno", "garage", "drum & bass"
][:25]

ARTIST_NAMES = [
    "Drake", "Billie Eilish", "BTS", "Ariana Grande", "The Weeknd", "Taylor Swift", "Ed Sheeran", "Kanye West", "Doja Cat", "Bad Bunny",
    "Olivia Rodrigo", "Dua Lipa", "Lil Nas X", "Post Malone", "Travis Scott", "Justin Bieber", "J. Cole", "Kendrick Lamar", "SZA", "Harry Styles",
    "Megan Thee Stallion", "Imagine Dragons", "Lizzo", "Shawn Mendes", "Camila Cabello", "Halsey", "Marshmello", "Joji", "Tyler, The Creator", "Lana Del Rey"
][:25]

PLAYLIST_TERMS = [
    "chill vibes", "workout", "party", "sleep", "focus", "summer", "throwback", "road trip", "study", "gaming",
    "relax", "motivation", "love songs", "morning", "evening", "instrumental", "top hits", "new music", "indie", "pop hits",
    "hip hop classics", "electronic essentials", "lofi beats", "jazz cafe", "deep house"
][:25]

NAV_LINKS = [
    ("SoundCloud", "Home"), ("Home", "Home"), ("Feed", "Feed"), ("Library", "Library"),
    ("Upload", "Upload"), ("For Artists", "For Artists"), ("Directory", "People directory"),
    ("About us", "About SoundCloud"), ("Artist Resources", "Artist Resources"),
    ("Newsroom", "SoundCloud Newsroom"), ("Jobs", "Jobs at SoundCloud"),
    ("Developers", "SoundCloud for developers"), ("Help", "SoundCloud help"),
    ("Legal", "Terms of use"), ("Privacy", "Privacy policy"),
    ("Cookie Policy", "Cookie Policy"), ("Cookie Manager", "Cookie Manager"),
    ("Imprint", "Company information"), ("Charts", "Charts"),
    ("Transparency Reports", "Transparency Reports")
][:20]

TRENDING_LINKS = [
    "Explore trending playlists", "Start Free", "Explore Go+", "Explore Artist Pro", "Upload your own"
]

ARTIST_PROFILE_LINKS = [
    "DC the Don", "1900Rugrat", "bunii", "Tei Shi", "Chris Webby", "Witt Lowry"
]

LANGUAGES = [
    "English (US)", "Deutsch", "Español", "Français", "Italiano", "Nederlands", "Polski", "Português", "Русский", "Svenska",
    "Türkçe", "日本語", "한국어", "简体中文", "繁體中文", "العربية", "Čeština", "Dansk", "Ελληνικά", "Suomi",
    "Magyar", "Norsk", "Română", "Slovenčina", "Slovenščina"
][:20]

BANNER_TEXTS = [
    "Complete library", "Every song you know plus millions you don't, ad-free with Go+.",
    "Discover your next obsession, or become someone else’s.",
    "It all starts with an upload.", "Where every music scene lives.",
    "Hear what’s trending for free in the SoundCloud community",
    "Never stop listening", "Calling all creators", "Thanks for listening. Now join in.",
    "Save tracks, follow artists and build playlists. All for free.",
    "SoundCloud is available on Web, iOS, Android, Sonos, Chromecast, and Xbox One."
]

SETTINGS_OPTIONS = [
    "Settings and more", "Language: English (US)"
]

QUEUE_ACTIONS = [
    "Clear", "Hide queue"
]

PLAYBACK_ACTIONS = [
    "Skip to previous", "Play current", "Skip to next", "Shuffle", "Repeat track"
]

APP_DOWNLOAD_LINKS = [
    "Download on the App Store", "Get it on Google Play"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., promotional, cookie, or language selection).",
        "Do not sign up, sign in, or make any purchases unless explicitly instructed.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("SoundCloud", steps).model_dump()

def soundcloud_search_track(_: dict) -> dict:
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        "Focus the searchbox labeled 'Search'.",
        f"Type '{term}' and press Enter or click the 'Search' button.",
        "Wait for search results to load.",
        "Locate the first track result in the list.",
        "Assert the result contains the search term or is relevant.",
        "Do not click play or navigate away.",
    ]
    return {
        "task_type": "soundcloud_search_track",
        "search_term": term,
        "steps": steps,
        "assertion": f"First result in search results contains '{term}' or is relevant to it.",
    }

def soundcloud_search_artist(_: dict) -> dict:
    artist = random.choice(ARTIST_NAMES)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        "Focus the searchbox labeled 'Search'.",
        f"Type '{artist}' and press Enter or click the 'Search' button.",
        "Wait for search results to load.",
        "Switch to the 'People' or 'Artists' tab if available.",
        "Locate the artist profile in the results.",
        "Assert the artist name appears in the result.",
    ]
    return {
        "task_type": "soundcloud_search_artist",
        "artist_name": artist,
        "steps": steps,
        "assertion": f"Artist '{artist}' is present in the search results.",
    }

def soundcloud_search_playlist(_: dict) -> dict:
    playlist = random.choice(PLAYLIST_TERMS)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        "Focus the searchbox labeled 'Search'.",
        f"Type '{playlist}' and press Enter or click the 'Search' button.",
        "Wait for search results to load.",
        "Switch to the 'Playlists' tab if available.",
        "Locate the first playlist result.",
        "Assert the playlist title or description contains the search term.",
    ]
    return {
        "task_type": "soundcloud_search_playlist",
        "playlist_term": playlist,
        "steps": steps,
        "assertion": f"First playlist result contains '{playlist}' in the title or description.",
    }

def soundcloud_playback_controls(_: dict) -> dict:
    action = random.choice(PLAYBACK_ACTIONS)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        "If not already, play any available track from the homepage.",
        f"Use the player control '{action}' to manipulate playback.",
        "Observe the player UI for the expected change (e.g., skip, play, pause, shuffle, repeat).",
        "Assert that the player state changes accordingly.",
    ]
    return {
        "task_type": "soundcloud_playback_controls",
        "player_action": action,
        "steps": steps,
        "assertion": f"Player responds to '{action}' and updates the UI as expected.",
    }

def soundcloud_queue_management(_: dict) -> dict:
    action = random.choice(QUEUE_ACTIONS)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        "If not already, play any available track from the homepage.",
        f"Click the '{action}' button in the player queue controls.",
        "Observe the queue area for the expected change.",
        "Assert that the queue is cleared or hidden as appropriate.",
    ]
    return {
        "task_type": "soundcloud_queue_management",
        "queue_action": action,
        "steps": steps,
        "assertion": f"Queue area reflects the '{action}' action (e.g., empty or hidden).",
    }

def soundcloud_language_switch(_: dict) -> dict:
    lang = random.choice(LANGUAGES)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        "Locate and click the 'Language' or 'Language: English (US)' button in the footer or settings.",
        f"Select '{lang}' from the language options.",
        "Wait for the page to reload or update.",
        "Assert that the site interface updates to the selected language.",
    ]
    return {
        "task_type": "soundcloud_language_switch",
        "language": lang,
        "steps": steps,
        "assertion": f"Site interface is displayed in '{lang}' language.",
    }

def soundcloud_account_signup(_: dict) -> dict:
    name = f"TestUser{random.randint(1000,9999)}"
    email = f"test{random.randint(10000,99999)}@example.com"
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        "Click the 'Create a SoundCloud account' button.",
        "Wait for the signup modal or page to appear.",
        f"Enter name '{name}' and email '{email}' in the registration form.",
        "Enter a valid password (e.g., 'TestPass123!').",
        "Do not submit the form.",
        "Assert that the 'Sign up' or 'Create account' button becomes enabled.",
    ]
    return {
        "task_type": "soundcloud_account_signup",
        "signup_name": name,
        "signup_email": email,
        "steps": steps,
        "assertion": "Signup button is enabled after filling all required fields.",
    }

def soundcloud_signin_modal(_: dict) -> dict:
    email = f"test{random.randint(10000,99999)}@example.com"
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        "Click the 'Sign in' button.",
        "Wait for the sign-in modal or page to appear.",
        f"Enter email '{email}' and any password (e.g., 'FakePass123!').",
        "Do not submit the form.",
        "Assert that the 'Sign in' button is enabled.",
        "Assert that an error message appears if submitting with fake credentials (do not submit).",
    ]
    return {
        "task_type": "soundcloud_signin_modal",
        "signin_email": email,
        "steps": steps,
        "assertion": "Sign in button is enabled after input; error message appears if submitted with fake credentials.",
    }

def soundcloud_navigation_links(_: dict) -> dict:
    nav = random.choice(NAV_LINKS)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        f"Locate and click the '{nav[0]}' navigation link.",
        "Wait for the page to load.",
        f"Assert that the page or section for '{nav[1]}' is displayed (e.g., URL or heading matches).",
    ]
    return {
        "task_type": "soundcloud_navigation_links",
        "navigation_link": nav[0],
        "steps": steps,
        "assertion": f"Page or section for '{nav[1]}' is displayed after navigation.",
    }

def soundcloud_trending_explore(_: dict) -> dict:
    link = random.choice(TRENDING_LINKS)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        f"Locate and click the '{link}' link or button.",
        "Wait for the new page or modal to load.",
        f"Assert that the content is relevant to '{link}' (e.g., trending playlists, Go+ info, upload page).",
    ]
    return {
        "task_type": "soundcloud_trending_explore",
        "explore_link": link,
        "steps": steps,
        "assertion": f"Content relevant to '{link}' is displayed.",
    }

def soundcloud_app_download_links(_: dict) -> dict:
    app = random.choice(APP_DOWNLOAD_LINKS)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        f"Scroll to the footer and locate the '{app}' link.",
        f"Click the '{app}' link.",
        "Assert that the browser navigates to the correct app store page (URL contains 'apple' or 'google').",
    ]
    return {
        "task_type": "soundcloud_app_download_links",
        "app_link": app,
        "steps": steps,
        "assertion": f"Browser navigates to the correct app store page after clicking '{app}'.",
    }

def soundcloud_artist_profile_link(_: dict) -> dict:
    artist = random.choice(ARTIST_PROFILE_LINKS)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        f"Locate the link for artist '{artist}' on the homepage.",
        f"Click the '{artist}' link.",
        "Wait for the artist profile page to load.",
        f"Assert that the artist's name '{artist}' appears on the profile page.",
    ]
    return {
        "task_type": "soundcloud_artist_profile_link",
        "artist_profile": artist,
        "steps": steps,
        "assertion": f"Artist profile page for '{artist}' is displayed.",
    }

def soundcloud_promotional_banner(_: dict) -> dict:
    banner = random.choice(BANNER_TEXTS)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        f"Scroll through the homepage and locate the promotional banner or text: '{banner}'.",
        "Assert that the banner or text is visible on the page.",
    ]
    return {
        "task_type": "soundcloud_promotional_banner",
        "banner_text": banner,
        "steps": steps,
        "assertion": f"Promotional banner or text '{banner}' is visible on the homepage.",
    }

def soundcloud_settings_menu(_: dict) -> dict:
    opt = random.choice(SETTINGS_OPTIONS)
    steps = [
        "Go to url 'https://soundcloud.com/'.",
        *_ui_hygiene(),
        f"Locate and click the '{opt}' button in the header or footer.",
        "Wait for the settings or language menu to appear.",
        "Assert that the menu or options are displayed.",
    ]
    return {
        "task_type": "soundcloud_settings_menu",
        "settings_option": opt,
        "steps": steps,
        "assertion": f"Settings or language menu for '{opt}' is displayed.",
    }

_TASK_GENERATORS: Dict[SOUNDCLOUD_TASK_TYPES, Callable[[dict], dict]] = {
    "soundcloud_search_track": soundcloud_search_track,
    "soundcloud_search_artist": soundcloud_search_artist,
    "soundcloud_search_playlist": soundcloud_search_playlist,
    "soundcloud_playback_controls": soundcloud_playback_controls,
    "soundcloud_queue_management": soundcloud_queue_management,
    "soundcloud_language_switch": soundcloud_language_switch,
    "soundcloud_account_signup": soundcloud_account_signup,
    "soundcloud_signin_modal": soundcloud_signin_modal,
    "soundcloud_navigation_links": soundcloud_navigation_links,
    "soundcloud_trending_explore": soundcloud_trending_explore,
    "soundcloud_app_download_links": soundcloud_app_download_links,
    "soundcloud_artist_profile_link": soundcloud_artist_profile_link,
    "soundcloud_promotional_banner": soundcloud_promotional_banner,
    "soundcloud_settings_menu": soundcloud_settings_menu,
}

def generate_soundcloud_task(task_type: SOUNDCLOUD_TASK_TYPES, payload: dict) -> dict:
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
    items = list(SOUNDCLOUD_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_soundcloud_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)