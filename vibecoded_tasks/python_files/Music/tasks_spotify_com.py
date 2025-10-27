import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

SPOTIFY_TASK_TYPES = Literal[
    "spotify_trending_song_play",
    "spotify_artist_browse",
    "spotify_album_single_browse",
    "spotify_radio_browse",
    "spotify_chart_browse",
    "spotify_search_combobox",
    "spotify_signup_flow",
    "spotify_login_flow",
    "spotify_faq_expand",
    "spotify_footer_nav",
    "spotify_privacy_choices",
    "spotify_error_recovery",
    "spotify_language_switch",
    "spotify_download_app",
    "spotify_support_nav",
]

SPOTIFY_SAMPLING_CONFIG: Dict[SPOTIFY_TASK_TYPES, int] = {
    "spotify_trending_song_play": 10,
    "spotify_artist_browse": 10,
    "spotify_album_single_browse": 10,
    "spotify_radio_browse": 10,
    "spotify_chart_browse": 10,
    "spotify_search_combobox": 10,
    "spotify_signup_flow": 10,
    "spotify_login_flow": 10,
    "spotify_faq_expand": 10,
    "spotify_footer_nav": 10,
    "spotify_privacy_choices": 10,
    "spotify_error_recovery": 10,
    "spotify_language_switch": 10,
    "spotify_download_app": 10,
    "spotify_support_nav": 10,
}

TRENDING_SONGS = [
    "Ghostbusters",
    "This Is Halloween",
    "Thriller",
    "Somebody's Watching Me - Single Version",
    "Spooky, Scary Skeletons - Undead Tombstone Remix",
    "Who Knows",
    "SPAGHETTI",
    "Beautiful Things",
    "LOVER GIRL",
    "Super Freak",
    "Disturbia",
    "Bloody Mary",
    "Pussy Palace",
    "Psycho Killer",
    "I'm Not There For You",
    "Halloween Theme - Main Title",
    "All On Me (feat. G Herbo)",
    "Harry Potter - Trap Remix",
    "Ghost Town",
    "I Put a Spell On You",
    "Monster Mash",
    "Bad Guy",
    "Blinding Lights",
    "Shape of You",
]

TRENDING_ARTISTS = [
    "Kendrick Lamar",
    "Drake",
    "The Weeknd",
    "Morgan Wallen",
    "Post Malone",
    "Rihanna",
    "Lady Gaga",
    "Billie Eilish",
    "Taylor Swift",
    "Kanye West",
    "Ed Sheeran",
    "Ariana Grande",
    "Doja Cat",
    "Olivia Rodrigo",
    "SZA",
    "Bad Bunny",
    "Megan Thee Stallion",
    "Lil Baby",
    "Rockwell",
    "Ray Parker Jr.",
    "Michael Jackson",
    "Andrew Gold",
    "Jessie Murph",
]

ALBUMS_AND_SINGLES = [
    "I’m The Problem",
    "DeBÍ TiRAR MáS FOToS",
    "10 Hours of Continuous Rain Sounds for Sleeping",
    "HIT ME HARD AND SOFT",
    "GNX",
    "$ome $exy $ongs 4 U",
    "MUSIC",
    "Hamilton (Original Broadway Cast Recording)",
    "Even In Arcadia",
    "Short n' Sweet",
    "Midnights",
    "After Hours",
    "Future Nostalgia",
    "SOUR",
    "Planet Her",
    "Justice",
    "Certified Lover Boy",
    "Positions",
    "Fine Line",
    "Hollywood's Bleeding",
    "Lover",
    "Scorpion",
    "Beerbongs & Bentleys",
]

RADIO_STATIONS = [
    "Morgan Wallen Radio",
    "Zach Bryan Radio",
    "Drake Radio",
    "Fleetwood Mac Radio",
    "SZA Radio",
    "Sabrina Carpenter Radio",
    "Noah Kahan Radio",
    "Post Malone Radio",
    "Chris Stapleton Radio",
    "Taylor Swift Radio",
    "Billie Eilish Radio",
    "Lady Gaga Radio",
    "The Weeknd Radio",
    "Kendrick Lamar Radio",
    "Ariana Grande Radio",
    "Ed Sheeran Radio",
    "Rihanna Radio",
    "Doja Cat Radio",
    "Olivia Rodrigo Radio",
    "Bad Bunny Radio",
    "Lil Baby Radio",
    "Rockwell Radio",
]

CHARTS = [
    "Top Songs - Global",
    "Top Songs - USA",
    "Top 50 - UK",
    "Top 50 - Germany",
    "Top 50 - Brazil",
    "Top 50 - Japan",
    "Top 50 - Australia",
    "Top 50 - Canada",
    "Top 50 - France",
    "Top 50 - India",
    "Top 50 - Italy",
    "Top 50 - Spain",
    "Top 50 - Mexico",
    "Top 50 - Sweden",
    "Top 50 - Norway",
    "Top 50 - Netherlands",
    "Top 50 - Turkey",
    "Top 50 - Poland",
    "Top 50 - South Africa",
    "Top 50 - Russia",
    "Top 50 - Argentina",
    "Top 50 - Indonesia",
]

SEARCH_TERMS = [
    "Halloween",
    "Love",
    "Rain",
    "Pop",
    "Hip Hop",
    "Rock",
    "Jazz",
    "Classical",
    "Workout",
    "Chill",
    "Party",
    "Focus",
    "Sleep",
    "Country",
    "Indie",
    "EDM",
    "Latin",
    "Reggae",
    "Metal",
    "Blues",
    "Podcast",
    "Audiobook",
    "Instrumental",
    "Throwback",
]

FAQ_QUESTIONS = [
    "How do I create a playlist?",
    "How do I activate Data Saver mode?",
    "Where can I find Podcasts?",
    "How do I reset my password?",
    "How do I change my email address?",
    "How do I delete my account?",
    "How do I manage my subscription?",
    "How do I redeem a gift card?",
    "How do I share music?",
    "How do I block explicit content?",
    "How do I update payment details?",
    "How do I download music?",
    "How do I use Spotify Connect?",
    "How do I use offline mode?",
    "How do I recover deleted playlists?",
    "How do I change my profile picture?",
    "How do I follow artists?",
    "How do I report a problem?",
    "How do I contact support?",
    "How do I use the web player?",
    "How do I use the mobile app?",
    "How do I get student discount?",
]

FOOTER_LINKS = [
    "About",
    "Jobs",
    "For the Record",
    "For Artists",
    "Developers",
    "Advertising",
    "Investors",
    "Vendors",
    "Support",
    "Web Player",
    "Free Mobile App",
    "Import your music",
    "Premium Individual",
    "Premium Duo",
    "Premium Family",
    "Premium Student",
    "Spotify Free",
    "Audiobooks Access",
    "Legal",
    "Safety & Privacy Center",
    "Privacy Policy",
    "Cookies",
    "About Ads",
    "Accessibility",
    "Notice at Collection",
    "Instagram",
    "Twitter",
    "Facebook",
]

LANGUAGES = [
    "English", "Español", "Français", "Deutsch", "Italiano", "Português", "Nederlands", "Svenska", "Norsk", "Suomi",
    "Dansk", "Polski", "Türkçe", "Русский", "日本語", "한국어", "中文", "العربية", "ไทย", "Bahasa Indonesia",
    "Čeština", "Magyar", "Ελληνικά", "Română",
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, cookie banners, or modals if present.",
        "Do not attempt to play or download content requiring payment or login.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Spotify", steps).model_dump()

def spotify_trending_song_play(_: dict) -> dict:
    song = random.choice(TRENDING_SONGS)
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Trending songs' section.",
        f"Locate the row for '{song}'.",
        f"Click the 'Play {song}' button.",
        "Assert that the now playing bar updates to show the selected song title.",
        "Assert that the play button changes to a pause icon.",
        "Do not attempt to skip, shuffle, or repeat.",
    ]
    return {
        "task_type": "spotify_trending_song_play",
        "song": song,
        "steps": steps,
        "assertion": f"Now playing bar displays '{song}' and play button is in pause state."
    }

def spotify_artist_browse(_: dict) -> dict:
    artist = random.choice(TRENDING_ARTISTS)
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Popular artists' section.",
        f"Locate the row for '{artist}'.",
        f"Click the link with artist name '{artist}'.",
        "Assert that the artist page loads and displays the correct artist name in the header.",
        "Assert that a list of songs or albums by the artist is visible.",
    ]
    return {
        "task_type": "spotify_artist_browse",
        "artist": artist,
        "steps": steps,
        "assertion": f"Artist page header contains '{artist}' and their discography is listed."
    }

def spotify_album_single_browse(_: dict) -> dict:
    album = random.choice(ALBUMS_AND_SINGLES)
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Popular albums and singles' section.",
        f"Locate the row for '{album}'.",
        f"Click the link with album/single name '{album}'.",
        "Assert that the album/single page loads with the correct title.",
        "Assert that a tracklist or play button is visible.",
    ]
    return {
        "task_type": "spotify_album_single_browse",
        "album": album,
        "steps": steps,
        "assertion": f"Album/single page displays '{album}' as title and shows tracklist or play button."
    }

def spotify_radio_browse(_: dict) -> dict:
    radio = random.choice(RADIO_STATIONS)
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Popular radio' section.",
        f"Locate the row for '{radio}'.",
        f"Click the link with radio name '{radio}'.",
        "Assert that the radio station page loads and displays the correct name.",
        "Assert that a list of featured artists or tracks is visible.",
    ]
    return {
        "task_type": "spotify_radio_browse",
        "radio": radio,
        "steps": steps,
        "assertion": f"Radio station page header contains '{radio}' and lists featured artists or tracks."
    }

def spotify_chart_browse(_: dict) -> dict:
    chart = random.choice(CHARTS)
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Featured Charts' section.",
        f"Locate the row for '{chart}'.",
        f"Click the link with chart name '{chart}'.",
        "Assert that the chart page loads and displays the correct chart name.",
        "Assert that a ranked list of songs is visible.",
    ]
    return {
        "task_type": "spotify_chart_browse",
        "chart": chart,
        "steps": steps,
        "assertion": f"Chart page header contains '{chart}' and a ranked song list is present."
    }

def spotify_search_combobox(_: dict) -> dict:
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Locate the combobox labeled 'What do you want to play?'.",
        f"Type '{term}' into the combobox.",
        "Wait for autocomplete suggestions to appear.",
        f"Select the first suggestion related to '{term}'.",
        "Assert that the results page or section updates to show items matching the search term.",
        "Assert that at least one result is visible.",
    ]
    return {
        "task_type": "spotify_search_combobox",
        "search_term": term,
        "steps": steps,
        "assertion": f"Results update to show items matching '{term}' and at least one result is visible."
    }

def spotify_signup_flow(_: dict) -> dict:
    fake_email = f"testuser{random.randint(10000,99999)}@example.com"
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Click the 'Sign up' button in the top navigation.",
        "Fill in the registration form with a valid email address, password, display name, and date of birth.",
        f"Use the email '{fake_email}'.",
        "Select a country from the dropdown.",
        "Check the terms and conditions box.",
        "Click the 'Sign up' or 'Continue' button.",
        "Assert that a confirmation or welcome message appears.",
        "Assert that the user is redirected to a logged-in state or dashboard.",
    ]
    return {
        "task_type": "spotify_signup_flow",
        "email": fake_email,
        "steps": steps,
        "assertion": "Confirmation/welcome message is shown and user is logged in."
    }

def spotify_login_flow(_: dict) -> dict:
    fake_email = f"testuser{random.randint(10000,99999)}@example.com"
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Click the 'Log in' button in the top navigation.",
        f"Enter email '{fake_email}' and an invalid password.",
        "Click the 'Log in' button.",
        "Assert that an error message is displayed indicating invalid credentials.",
        "Do not attempt to recover the password.",
    ]
    return {
        "task_type": "spotify_login_flow",
        "email": fake_email,
        "steps": steps,
        "assertion": "Login error message is displayed for invalid credentials."
    }

def spotify_faq_expand(_: dict) -> dict:
    question = random.choice(FAQ_QUESTIONS)
    steps = [
        "Go to url 'https://www.spotify.com/us/free/'.",
        *_ui_hygiene(),
        "Scroll to the FAQ section.",
        f"Locate the disclosure triangle for '{question}'.",
        f"Click to expand the answer for '{question}'.",
        "Assert that the answer text becomes visible.",
        "Click again to collapse the answer.",
        "Assert that the answer text is hidden.",
    ]
    return {
        "task_type": "spotify_faq_expand",
        "faq_question": question,
        "steps": steps,
        "assertion": f"Answer for '{question}' is shown when expanded and hidden when collapsed."
    }

def spotify_footer_nav(_: dict) -> dict:
    link = random.choice(FOOTER_LINKS)
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Scroll to the footer section.",
        f"Locate the link labeled '{link}'.",
        f"Click the '{link}' link.",
        "Assert that the destination page loads and the header or title matches the link.",
        "Assert that the URL changes appropriately.",
    ]
    return {
        "task_type": "spotify_footer_nav",
        "footer_link": link,
        "steps": steps,
        "assertion": f"Destination page for '{link}' loads with matching header/title and correct URL."
    }

def spotify_privacy_choices(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Scroll to the footer section.",
        "Locate the button labeled 'Your Privacy Choices'.",
        "Click the 'Your Privacy Choices' button.",
        "Assert that a privacy or cookie preferences dialog appears.",
        "Change at least one privacy preference (e.g., disable a cookie type).",
        "Save or confirm the changes.",
        "Assert that a confirmation message appears or the dialog closes.",
    ]
    return {
        "task_type": "spotify_privacy_choices",
        "steps": steps,
        "assertion": "Privacy dialog appears, preference is changed, and confirmation is shown."
    }

def spotify_error_recovery(_: dict) -> dict:
    error_pages = [
        "https://www.spotify.com/genre/podcasts-web",
        "https://www.spotify.com/popular-in/us",
        "https://www.spotify.com/404",
        "https://www.spotify.com/unknown-page",
    ]
    url = random.choice(error_pages)
    recovery_links = ["Web Player", "Support", "Sign up free"]
    recovery = random.choice(recovery_links)
    steps = [
        f"Go to url '{url}'.",
        *_ui_hygiene(),
        "Wait for the error or 'Page not found' message to appear.",
        f"Locate and click the '{recovery}' link in the error message area.",
        f"Assert that the user is redirected to the correct '{recovery}' page.",
        "Assert that the new page loads successfully and is not an error page.",
    ]
    return {
        "task_type": "spotify_error_recovery",
        "error_url": url,
        "recovery_link": recovery,
        "steps": steps,
        "assertion": f"Clicking '{recovery}' on error page '{url}' redirects to the correct working page."
    }

def spotify_language_switch(_: dict) -> dict:
    lang = random.choice(LANGUAGES)
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Scroll to the footer section.",
        "Locate the language selector button (e.g., labeled 'English').",
        f"Click the language selector and choose '{lang}'.",
        "Assert that the page reloads or updates to display text in the selected language.",
        "Assert that navigation and headings are translated.",
    ]
    return {
        "task_type": "spotify_language_switch",
        "language": lang,
        "steps": steps,
        "assertion": f"Page displays in '{lang}' after selection, with translated navigation and headings."
    }

def spotify_download_app(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Locate the 'Download' button in the top navigation.",
        "Click the 'Download' button.",
        "Assert that the download page loads with options for different platforms (Windows, Mac, mobile, etc).",
        "Assert that at least one download link or button is visible.",
    ]
    return {
        "task_type": "spotify_download_app",
        "steps": steps,
        "assertion": "Download page loads and shows at least one platform download option."
    }

def spotify_support_nav(_: dict) -> dict:
    support_links = [
        "Account Help",
        "Payment Help",
        "Technical Issues",
        "Plan Information",
        "App Features",
        "Safety & Privacy Center",
        "Accessibility",
        "Legal",
        "Community",
        "Contact Us",
        "Web Player Help",
        "Mobile App Help",
        "Premium Support",
        "Student Discount Help",
        "Family Plan Help",
        "Duo Plan Help",
        "Podcasts Help",
        "Audiobooks Help",
        "Import Music Help",
        "Gift Card Help",
        "Subscription Help",
        "Password Reset Help",
    ]
    link = random.choice(support_links)
    steps = [
        "Go to url 'https://www.spotify.com'.",
        *_ui_hygiene(),
        "Locate the 'Support' button in the top navigation.",
        "Click the 'Support' button.",
        f"On the support page, locate the section or link for '{link}'.",
        f"Click the '{link}' link or heading.",
        "Assert that the relevant help or FAQ section loads.",
        "Assert that the page or section header matches the selected support topic.",
    ]
    return {
        "task_type": "spotify_support_nav",
        "support_topic": link,
        "steps": steps,
        "assertion": f"Support page for '{link}' loads with matching header."
    }

_TASK_GENERATORS: Dict[SPOTIFY_TASK_TYPES, Callable[[dict], dict]] = {
    "spotify_trending_song_play": spotify_trending_song_play,
    "spotify_artist_browse": spotify_artist_browse,
    "spotify_album_single_browse": spotify_album_single_browse,
    "spotify_radio_browse": spotify_radio_browse,
    "spotify_chart_browse": spotify_chart_browse,
    "spotify_search_combobox": spotify_search_combobox,
    "spotify_signup_flow": spotify_signup_flow,
    "spotify_login_flow": spotify_login_flow,
    "spotify_faq_expand": spotify_faq_expand,
    "spotify_footer_nav": spotify_footer_nav,
    "spotify_privacy_choices": spotify_privacy_choices,
    "spotify_error_recovery": spotify_error_recovery,
    "spotify_language_switch": spotify_language_switch,
    "spotify_download_app": spotify_download_app,
    "spotify_support_nav": spotify_support_nav,
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