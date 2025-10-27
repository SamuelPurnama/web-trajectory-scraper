import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

GENIUS_TASK_TYPES = Literal[
    "genius_search_song",
    "genius_browse_trending",
    "genius_filter_by_genre",
    "genius_view_artist_page",
    "genius_view_album_page",
    "genius_read_song_annotations",
    "genius_browse_chart",
    "genius_signup_form_validation",
    "genius_faq_navigation",
    "genius_filter_by_year",
    "genius_search_by_lyrics",
    "genius_browse_editorial",
    "genius_song_page_share",
    "genius_song_page_report",
]

GENIUS_SAMPLING_CONFIG: Dict[GENIUS_TASK_TYPES, int] = {
    "genius_search_song": 10,
    "genius_browse_trending": 10,
    "genius_filter_by_genre": 10,
    "genius_view_artist_page": 10,
    "genius_view_album_page": 10,
    "genius_read_song_annotations": 10,
    "genius_browse_chart": 10,
    "genius_signup_form_validation": 10,
    "genius_faq_navigation": 10,
    "genius_filter_by_year": 10,
    "genius_search_by_lyrics": 10,
    "genius_browse_editorial": 10,
    "genius_song_page_share": 10,
    "genius_song_page_report": 10,
}

SONG_SEARCH_TERMS = [
    "Bohemian Rhapsody", "Blinding Lights", "Shape of You", "Bad Guy", "Old Town Road", "Sicko Mode", "God's Plan",
    "Despacito", "HUMBLE.", "Sunflower", "Rockstar", "Closer", "Lucid Dreams", "All of Me", "Uptown Funk",
    "Rolling in the Deep", "Thinking Out Loud", "Happier", "Believer", "Senorita", "Perfect", "Levitating",
    "Stay", "Shallow", "Drivers License", "Savage Love", "Dance Monkey", "Someone You Loved", "Montero", "Peaches", "Heat Waves"
]
ARTISTS = [
    "Drake", "Taylor Swift", "Kanye West", "Billie Eilish", "Adele", "The Weeknd", "Ed Sheeran", "Doja Cat",
    "Post Malone", "Ariana Grande", "BTS", "Lil Nas X", "Dua Lipa", "Olivia Rodrigo", "Travis Scott",
    "SZA", "Kendrick Lamar", "Harry Styles", "Justin Bieber", "Bad Bunny", "J. Cole", "Megan Thee Stallion",
    "Future", "Cardi B", "Lizzo", "Imagine Dragons", "Bruno Mars", "Halsey", "Juice WRLD", "Lil Baby", "21 Savage"
]
ALBUMS = [
    "1989", "DAMN.", "Astroworld", "Future Nostalgia", "After Hours", "Scorpion", "SOUR", "Beerbongs & Bentleys",
    "Fine Line", "Justice", "Lover", "Positions", "Hollywood's Bleeding", "Divide", "When We All Fall Asleep, Where Do We Go?",
    "Montero", "Planet Her", "Certified Lover Boy", "Folklore", "Views", "Thank U, Next", "Happier Than Ever",
    "Blame It on Baby", "Goodbye & Good Riddance", "Life of a Don", "The Off-Season", "Evermore", "My Turn", "Legend", "Future Hndrxx Presents: The WIZRD"
]
GENRES = [
    "Pop", "Hip-Hop", "R&B", "Rock", "Indie", "Country", "Latin", "Electronic", "Jazz", "Folk", "Metal", "Reggae",
    "Blues", "Soul", "Punk", "Alternative", "Classical", "Gospel", "K-Pop", "Afrobeats", "Dance", "Trap", "Drill", "EDM", "Disco"
]
YEARS = [str(y) for y in range(2000, 2024)]
CHARTS = [
    "Top Songs", "Top Albums", "Trending Songs", "Trending Artists", "Verified Artists", "Hot 100", "Billboard 200",
    "Rap Chart", "Pop Chart", "R&B Chart", "Rock Chart", "Indie Chart", "Latin Chart", "Country Chart", "K-Pop Chart",
    "Afrobeats Chart", "Global Chart", "New Releases", "Most Viewed", "Most Annotated", "Editors' Picks"
]
FAQ_TOPICS = [
    "How do I create an account?", "How do I reset my password?", "How do I add lyrics?", "How do I become a Genius contributor?",
    "How do I report incorrect lyrics?", "How do I annotate lyrics?", "How do I delete my account?", "How do I verify my artist page?",
    "How do I contact support?", "How do I change my username?", "How do I add an album?", "How do I edit song metadata?",
    "How do I link social media?", "How do I upvote annotations?", "How do I join the Genius community?", "How do I use the mobile app?",
    "How do I get my lyrics featured?", "How do I submit feedback?", "How do I manage notifications?", "How do I change my email address?",
    "How do I access the API?", "How do I embed a song?", "How do I follow an artist?", "How do I block users?"
]
LYRIC_SNIPPETS = [
    "I'm in love with the shape of you", "Is this the real life? Is this just fantasy?", "I got a feeling that tonight's gonna be a good night",
    "Cause baby you're a firework", "Hello from the other side", "I can't feel my face when I'm with you", "I'm off the deep end, watch as I dive in",
    "I took a pill in Ibiza", "I got sunshine on a cloudy day", "I'm a survivor, I'm not gonna give up", "I want it that way",
    "You are the dancing queen", "We don't talk anymore", "I'm too hot (hot damn)", "I see a little silhouetto of a man",
    "I got the eye of the tiger", "I will survive", "I want to hold your hand", "Let it be, let it be", "Don't stop believin'",
    "I want to break free", "I'm still standing", "It's a beautiful day", "I'm walking on sunshine", "I'm a believer"
]
EDITORIALS = [
    "Genius Verified", "Behind the Lyrics", "Song Stories", "The Making Of", "Decoded", "Open Mic", "For The Record",
    "Genius News", "Genius Interviews", "Genius Community", "Genius Live", "Genius Originals", "Genius Class",
    "Genius IQ", "Genius Lyrics Breakdown", "Genius Top Songs", "Genius Top Albums", "Genius Picks", "Genius Staff Picks",
    "Genius Year In Review", "Genius Video", "Genius Podcast"
]
SHARE_METHODS = [
    "Copy Link", "Share on Twitter", "Share on Facebook", "Share via Email", "Embed", "Share on WhatsApp", "Share on Reddit",
    "Share on Tumblr", "Share on Pinterest", "Share on LinkedIn", "Share on Messenger", "Share on Telegram", "Share on SMS",
    "Share on Snapchat", "Share on Instagram", "Share on Discord", "Share on WeChat", "Share on VK", "Share on Line", "Share on Signal"
]
REPORT_REASONS = [
    "Incorrect lyrics", "Offensive content", "Spam", "Duplicate song", "Wrong artist", "Wrong album", "Broken link",
    "Copyright infringement", "Inappropriate annotation", "Outdated information", "Formatting issue", "Other"
]
EMAILS = [f"testuser{i}@example.com" for i in range(1, 25)]
USERNAMES = [f"musicfan{i}" for i in range(1, 25)]
PASSWORDS = [f"TestPass{i}!" for i in range(1, 25)]
YEARS_OF_BIRTH = [str(y) for y in range(1980, 2005)]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups/banners (e.g., cookie consent, newsletter, login prompts).",
        "Do not sign up, log in, or purchase anything unless instructed.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Genius", steps).model_dump()

def genius_search_song(_: dict) -> dict:
    term = random.choice(SONG_SEARCH_TERMS)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Focus the search input at the top of the page.",
        f"Type '{term}' and press Enter.",
        "Wait for search results to load.",
        f"Assert that at least one result contains '{term.split()[0]}' (case-insensitive) in the title or artist.",
        "Click the first result.",
        "Assert the song page loads and displays the correct title and artist.",
    ]
    return {"task_type": "genius_search_song", "search_term": term, "steps": steps}

def genius_browse_trending(_: dict) -> dict:
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Locate the 'Trending' section on the homepage.",
        "Assert that at least 5 trending songs are visible.",
        "Click the first trending song.",
        "Assert the song page loads and displays lyrics.",
    ]
    return {"task_type": "genius_browse_trending", "steps": steps}

def genius_filter_by_genre(_: dict) -> dict:
    genre = random.choice(GENRES)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Locate the genres dropdown or navigation.",
        f"Select the genre '{genre}'.",
        "Wait for the genre page to load.",
        f"Assert that the page title or header contains '{genre}'.",
        "Assert that at least 10 songs listed are labeled with the selected genre.",
    ]
    return {"task_type": "genius_filter_by_genre", "genre": genre, "steps": steps}

def genius_view_artist_page(_: dict) -> dict:
    artist = random.choice(ARTISTS)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Focus the search input at the top of the page.",
        f"Type '{artist}' and press Enter.",
        "Wait for search results to load.",
        "Click the first result that is an artist (not a song or album).",
        f"Assert the artist's page loads and the artist name '{artist}' is in the header.",
        "Assert that at least 5 songs are listed on the artist's page.",
    ]
    return {"task_type": "genius_view_artist_page", "artist": artist, "steps": steps}

def genius_view_album_page(_: dict) -> dict:
    album = random.choice(ALBUMS)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Focus the search input at the top of the page.",
        f"Type '{album}' and press Enter.",
        "Wait for search results to load.",
        "Click the first result that is an album (not a song or artist).",
        f"Assert the album page loads and the album name '{album}' is in the header.",
        "Assert that at least 3 tracks are listed on the album page.",
    ]
    return {"task_type": "genius_view_album_page", "album": album, "steps": steps}

def genius_read_song_annotations(_: dict) -> dict:
    term = random.choice(SONG_SEARCH_TERMS)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Focus the search input at the top of the page.",
        f"Type '{term}' and press Enter.",
        "Wait for search results to load.",
        "Click the first song result.",
        "Assert the song page loads and lyrics are visible.",
        "Click a highlighted lyric line to open its annotation.",
        "Assert that an annotation panel appears with at least 1 paragraph of explanation.",
    ]
    return {"task_type": "genius_read_song_annotations", "song_term": term, "steps": steps}

def genius_browse_chart(_: dict) -> dict:
    chart = random.choice(CHARTS)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Locate the 'Charts' or 'Top Songs' navigation link and click it.",
        f"Select the '{chart}' chart from the available options.",
        "Wait for the chart page to load.",
        f"Assert that the chart page header contains '{chart}'.",
        "Assert that at least 10 items are listed in the chart.",
    ]
    return {"task_type": "genius_browse_chart", "chart": chart, "steps": steps}

def genius_signup_form_validation(_: dict) -> dict:
    email = random.choice(EMAILS)
    username = random.choice(USERNAMES)
    password = random.choice(PASSWORDS)
    year = random.choice(YEARS_OF_BIRTH)
    steps = [
        "Go to url 'https://genius.com/signup'.",
        *_ui_hygiene(),
        "Fill in the email field with an invalid email (e.g., 'notanemail').",
        "Attempt to submit the form.",
        "Assert that an error message appears for the email field.",
        f"Fill in the email field with '{email}'.",
        f"Fill in the username field with '{username}'.",
        f"Fill in the password field with '{password}'.",
        f"Select year of birth '{year}'.",
        "Attempt to submit the form.",
        "Assert that no error messages are shown for the filled fields.",
        "Do not actually create an account.",
    ]
    return {
        "task_type": "genius_signup_form_validation",
        "email": email,
        "username": username,
        "password": password,
        "year_of_birth": year,
        "steps": steps
    }

def genius_faq_navigation(_: dict) -> dict:
    topic = random.choice(FAQ_TOPICS)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Scroll to the footer and locate the 'Help' or 'FAQ' link.",
        "Click the link to open the FAQ/help center.",
        f"Search or browse for the topic: '{topic}'.",
        f"Assert that an answer or article is displayed for '{topic.split()[0]}'.",
    ]
    return {"task_type": "genius_faq_navigation", "faq_topic": topic, "steps": steps}

def genius_filter_by_year(_: dict) -> dict:
    year = random.choice(YEARS)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Locate the 'Year' filter or search option.",
        f"Select the year '{year}'.",
        "Wait for the page to update.",
        f"Assert that at least 5 songs or albums from '{year}' are listed.",
    ]
    return {"task_type": "genius_filter_by_year", "year": year, "steps": steps}

def genius_search_by_lyrics(_: dict) -> dict:
    snippet = random.choice(LYRIC_SNIPPETS)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Focus the search input at the top of the page.",
        f"Type the lyric snippet '{snippet}' and press Enter.",
        "Wait for search results to load.",
        f"Assert that at least one result contains the snippet '{snippet.split()[0]}' in the lyrics preview.",
        "Click the first result.",
        "Assert the song page displays the lyric snippet.",
    ]
    return {"task_type": "genius_search_by_lyrics", "lyric_snippet": snippet, "steps": steps}

def genius_browse_editorial(_: dict) -> dict:
    editorial = random.choice(EDITORIALS)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Locate the 'Editorial' or 'Features' section on the homepage or navigation.",
        f"Select the '{editorial}' feature.",
        "Wait for the editorial page to load.",
        f"Assert that the editorial page header contains '{editorial}'.",
        "Assert that at least 1 article or video is visible.",
    ]
    return {"task_type": "genius_browse_editorial", "editorial": editorial, "steps": steps}

def genius_song_page_share(_: dict) -> dict:
    term = random.choice(SONG_SEARCH_TERMS)
    method = random.choice(SHARE_METHODS)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Focus the search input at the top of the page.",
        f"Type '{term}' and press Enter.",
        "Wait for search results to load.",
        "Click the first song result.",
        "Assert the song page loads.",
        "Locate the 'Share' button and click it.",
        f"Select the '{method}' option.",
        f"Assert that the share action for '{method}' is available (e.g., link copied, share dialog opens, embed code shown).",
    ]
    return {"task_type": "genius_song_page_share", "song_term": term, "share_method": method, "steps": steps}

def genius_song_page_report(_: dict) -> dict:
    term = random.choice(SONG_SEARCH_TERMS)
    reason = random.choice(REPORT_REASONS)
    steps = [
        "Go to url 'https://genius.com'.",
        *_ui_hygiene(),
        "Focus the search input at the top of the page.",
        f"Type '{term}' and press Enter.",
        "Wait for search results to load.",
        "Click the first song result.",
        "Assert the song page loads.",
        "Locate the 'Report' or 'Flag' button and click it.",
        f"Select the reason '{reason}'.",
        "Attempt to submit the report.",
        "Assert that a confirmation or thank you message appears.",
        "Do not submit any personal information.",
    ]
    return {"task_type": "genius_song_page_report", "song_term": term, "report_reason": reason, "steps": steps}

_TASK_GENERATORS: Dict[GENIUS_TASK_TYPES, Callable[[dict], dict]] = {
    "genius_search_song": genius_search_song,
    "genius_browse_trending": genius_browse_trending,
    "genius_filter_by_genre": genius_filter_by_genre,
    "genius_view_artist_page": genius_view_artist_page,
    "genius_view_album_page": genius_view_album_page,
    "genius_read_song_annotations": genius_read_song_annotations,
    "genius_browse_chart": genius_browse_chart,
    "genius_signup_form_validation": genius_signup_form_validation,
    "genius_faq_navigation": genius_faq_navigation,
    "genius_filter_by_year": genius_filter_by_year,
    "genius_search_by_lyrics": genius_search_by_lyrics,
    "genius_browse_editorial": genius_browse_editorial,
    "genius_song_page_share": genius_song_page_share,
    "genius_song_page_report": genius_song_page_report,
}

def generate_genius_task(task_type: GENIUS_TASK_TYPES, payload: dict) -> dict:
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
    items = list(GENIUS_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_genius_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)