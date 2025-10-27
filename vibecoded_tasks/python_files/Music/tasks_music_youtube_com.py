import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

MUSIC_TASK_TYPES = Literal[
    "music_search_song",
    "music_search_album",
    "music_search_artist",
    "music_browse_genre_tab",
    "music_play_quick_pick",
    "music_browse_trending_playlist",
    "music_browse_community_playlist",
    "music_browse_album_for_you",
    "music_browse_all_time_essentials",
    "music_browse_autumn_vibes",
    "music_filter_quick_pick_by_artist",
    "music_filter_quick_pick_by_plays",
    "music_filter_album_by_artist",
    "music_filter_album_by_type",
    "music_filter_playlist_by_views",
]

MUSIC_SAMPLING_CONFIG: Dict[MUSIC_TASK_TYPES, int] = {
    "music_search_song": 10,
    "music_search_album": 10,
    "music_search_artist": 10,
    "music_browse_genre_tab": 10,
    "music_play_quick_pick": 10,
    "music_browse_trending_playlist": 10,
    "music_browse_community_playlist": 10,
    "music_browse_album_for_you": 10,
    "music_browse_all_time_essentials": 10,
    "music_browse_autumn_vibes": 10,
    "music_filter_quick_pick_by_artist": 10,
    "music_filter_quick_pick_by_plays": 10,
    "music_filter_album_by_artist": 10,
    "music_filter_album_by_type": 10,
    "music_filter_playlist_by_views": 10,
}

# 20+ search terms for songs, albums, artists, genres, etc.
SONG_SEARCH_TERMS = [
    "Shape of You", "Blinding Lights", "Bad Guy", "Levitating", "Peaches", "Drivers License", "Stay",
    "Dance Monkey", "Watermelon Sugar", "Old Town Road", "Senorita", "Uptown Funk", "Sunflower",
    "Perfect", "Shallow", "Rockstar", "Havana", "Believer", "Lucid Dreams", "God's Plan",
    "Monor Nijanot", "Kiwenenya Amazina", "Omwoyo Gwokulya.", "Dil Huwa Hai Tukde Tukde",
    "Bastarhin Bala", "Yegwe", "More Jago Moke Jani", "Manya", "Nariyal Je Farela Ghawad Se",
    "Maso Gange", "Ghuthva Ke Pairi", "Jaalise Hiya", "Endhar Hobo Nuware", "Bukute Gupute",
    "MOI NOTHOKAR ANUBHAB", "Rod Aaji", "Mur Kothai Amoni Korene", "Kar Porokh", "Barikhare Banot", "Xmoye Jen"
]

ALBUM_SEARCH_TERMS = [
    "Rumours", "Starboy", "Hybrid Theory", "Un Verano Sin Ti", "Short n' Sweet", "The Last", "The Life of a Showgirl",
    "Camino del Amor", "I’m The Problem", "Golden Collection Of Zubeen Vol - III", "Golden Collection Of Zubeen Vol - I",
    "Golden Collection Of Zubeen Vol - IV", "Classic Rock's Greatest Hits", "Pop's Biggest Hits", "Dance Hits",
    "Christian Music's Biggest Hits", "Bachata Mix", "All-Time Hip Hop Hits", "Feel-Good Classic Rock",
    "Morning Drive", "Wide Open Country", "Kick-Back Country", "'00s R&B Chill", "Classical for Autumn",
    "Country Tailgate", "Friday Night Lights", "Feel-Good Hip Hop and R&B"
]

ARTIST_SEARCH_TERMS = [
    "Taylor Swift", "Justin Bieber", "Zubeen Garg", "Paul Kafeero", "Sir Mathias Walukagga", "Hiresh Sinha",
    "Indrani Verma", "Haruna", "Sajan Nayak", "David Lutalo", "Bishnu Routh", "Walukagga", "Roshan Vaishnav",
    "Anupama Mishra", "Fleetwood Mac", "The Weeknd", "Sabrina Carpenter", "Bad Bunny", "Linkin Park",
    "Morgan Wallen", "Los Temerarios", "Aventura", "Selena", "Shakira", "KAROL G", "Vicente Fernández",
    "Cornelio Reyna", "José Alfredo Jiménez", "Antonio Aguilar", "Grupo Frontera", "Los Ángeles Azules",
    "Raymix", "JAY-Z", "Eminem", "Drake", "Kanye West", "Avicii", "Calvin Harris", "DJ Snake", "David Guetta",
    "Tyla", "Tyler, The Creator"
]

GENRE_TABS = [
    "Podcasts", "Energize", "Workout", "Feel good", "Relax", "Party", "Commute", "Romance", "Sad", "Focus", "Sleep"
]

ALL_TIME_ESSENTIALS = [
    "Pop's Biggest Hits", "Classic Rock's Greatest Hits", "Bachata Mix", "Christian Music's Biggest Hits",
    "Dance Hits", "Hip-Hop Classics", "Los Himnos", "Himnos Rancheros", "Cumbia Megamix", "All-Time Hip Hop Hits"
]

AUTUMN_VIBES = [
    "Autumn Feel", "Feel-Good Classic Rock", "Morning Drive", "Wide Open Country", "Kick-Back Country",
    "'00s R&B Chill", "Classical for Autumn", "Country Tailgate", "Friday Night Lights", "Feel-Good Hip Hop and R&B"
]

QUICK_PICK_ARTISTS = [
    "Zubeen Garg", "Paul Kafeero", "Sir Mathias Walukagga", "Hiresh Sinha", "Indrani Verma", "Haruna",
    "Sajan Nayak", "David Lutalo", "Bishnu Routh", "Walukagga", "Roshan Vaishnav", "Anupama Mishra",
    "Fleetwood Mac", "Taylor Swift", "The Weeknd", "Sabrina Carpenter", "Bad Bunny", "Linkin Park",
    "Morgan Wallen", "Los Temerarios"
]

QUICK_PICK_PLAYS = [
    "3M plays", "211K plays", "166K plays", "3.6M plays", "234K plays", "1.1M plays", "5.1M plays", "6.2M plays",
    "121K plays", "47K plays", "56K plays", "2.3M plays", "12M plays", "2.2M plays", "15M plays", "10M plays",
    "24M plays", "4.7M plays", "36M plays", "8.2M plays"
]

ALBUM_ARTISTS = [
    "Morgan Wallen", "Los Temerarios", "Taylor Swift", "Fleetwood Mac", "Aventura", "Sabrina Carpenter",
    "The Weeknd", "Bad Bunny", "Linkin Park", "Zubeen Garg", "Paul Kafeero", "Sir Mathias Walukagga",
    "Hiresh Sinha", "Indrani Verma", "Haruna", "Sajan Nayak", "David Lutalo", "Bishnu Routh", "Walukagga", "Roshan Vaishnav"
]

ALBUM_TYPES = [
    "Album", "EP", "Single", "Compilation", "Live", "Remix", "Soundtrack", "Mixtape", "Deluxe", "Reissue",
    "Greatest Hits", "Box Set", "Anniversary Edition", "Instrumental", "Acoustic", "Cover", "Tribute", "Demo", "Sampler", "Promo"
]

PLAYLIST_VIEWS = [
    "29M views", "4.6M views", "3.6M views", "10M views", "12M views", "1.2M views", "28M views", "5.4M views",
    "3.1M views", "1.7M views", "2.5M views", "7.8M views", "6.4M views", "9.9M views", "8.3M views", "11M views",
    "13M views", "15M views", "20M views", "18M views"
]

COMMUNITY_PLAYLISTS = [
    "Miguel Angel Juarez Hernandez", "Alejandra Muñoz morales", "Gabriel Goodman", "Maria Elena Martinez Vazquez",
    "Marcelo Dominguez Cabrera", "Jariel Diaz", "Jorge Lopez G", "adiestramiento canino", "Seantela Andrews",
    "Alex Reyes", "Juan Perez", "Maria Garcia", "Carlos Sanchez", "Ana Rodriguez", "Luis Martinez",
    "Sofia Lopez", "Pedro Gonzalez", "Lucia Fernandez", "Diego Ramirez", "Camila Torres"
]

COMMUNITY_PLAYLIST_DESCRIPTIONS = [
    "gruperas 90", "Reguetón antiguo", "90s rock hits", "conjunto primavera album", "canciones viejita",
    "puras pa pistiar", "Mix Pepe aguilar, Ana Gabriel, Banda", "brindis,bronco, temerarios, conjunto primavera,el trono de México, liberación,los Acosta",
    "Vibe", "Románticos gruperos", "Pop en español", "Rock clásico", "Baladas románticas", "Música para estudiar",
    "Hits del verano", "Chill latino", "Fiesta electrónica", "Jazz essentials", "Indie vibes", "Workout mix"
]

ALBUMS_FOR_YOU = [
    "I’m The Problem", "Camino del Amor", "The Life of a Showgirl", "Rumours", "The Last", "Short n' Sweet",
    "Starboy", "Un Verano Sin Ti", "Hybrid Theory", "Golden Collection Of Zubeen Vol - III", "Golden Collection Of Zubeen Vol - I",
    "Golden Collection Of Zubeen Vol - IV", "Classic Rock's Greatest Hits", "Pop's Biggest Hits", "Dance Hits",
    "Christian Music's Biggest Hits", "Bachata Mix", "All-Time Hip Hop Hits", "Feel-Good Classic Rock", "Morning Drive"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, sign-in prompts).",
        "Do not sign in or create an account; only browse and view public content.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("YouTube Music", steps).model_dump()

def music_search_song(_: dict) -> dict:
    term = random.choice(SONG_SEARCH_TERMS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Click the 'Initiate search' button or focus the search box.",
        f"Type the song name '{term}' and press Enter.",
        "Wait for search results to load.",
        f"Verify that at least one result contains the song title '{term}' (case-insensitive).",
        "Do not play or sign in; only confirm result presence.",
    ]
    return {"task_type": "music_search_song", "search_term": term, "steps": steps}

def music_search_album(_: dict) -> dict:
    term = random.choice(ALBUM_SEARCH_TERMS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Click the 'Initiate search' button or focus the search box.",
        f"Type the album name '{term}' and press Enter.",
        "Wait for search results to load.",
        f"Verify that at least one result contains the album title '{term}' (case-insensitive).",
        "Do not play or sign in; only confirm result presence.",
    ]
    return {"task_type": "music_search_album", "search_term": term, "steps": steps}

def music_search_artist(_: dict) -> dict:
    term = random.choice(ARTIST_SEARCH_TERMS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Click the 'Initiate search' button or focus the search box.",
        f"Type the artist name '{term}' and press Enter.",
        "Wait for search results to load.",
        f"Verify that at least one result contains the artist name '{term}' (case-insensitive).",
        "Do not play or sign in; only confirm result presence.",
    ]
    return {"task_type": "music_search_artist", "search_term": term, "steps": steps}

def music_browse_genre_tab(_: dict) -> dict:
    tab = random.choice(GENRE_TABS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        f"Click the '{tab}' tab in the main navigation bar.",
        f"Wait for the '{tab}' section to load.",
        f"Verify that the page displays playlists or content related to '{tab}'.",
        "Do not play or sign in; only confirm content is visible.",
    ]
    return {"task_type": "music_browse_genre_tab", "genre_tab": tab, "steps": steps}

def music_play_quick_pick(_: dict) -> dict:
    # Pick a quick pick song and artist
    song = random.choice(SONG_SEARCH_TERMS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Quick picks' section.",
        f"Locate the song '{song}' in the quick picks list.",
        f"Click the 'Play' button for '{song}'.",
        "Verify that the player bar at the bottom displays the song title.",
        "Pause playback after verifying.",
    ]
    return {"task_type": "music_play_quick_pick", "quick_pick_song": song, "steps": steps}

def music_browse_trending_playlist(_: dict) -> dict:
    playlist = random.choice(ALL_TIME_ESSENTIALS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Scroll to the 'All-time essentials' or 'Trending community playlists' section.",
        f"Locate the playlist '{playlist}'.",
        f"Click the playlist link to open its details page.",
        f"Verify that the playlist page shows the title '{playlist}'.",
        "Do not play or sign in; only confirm playlist details are visible.",
    ]
    return {"task_type": "music_browse_trending_playlist", "playlist": playlist, "steps": steps}

def music_browse_community_playlist(_: dict) -> dict:
    creator = random.choice(COMMUNITY_PLAYLISTS)
    desc = random.choice(COMMUNITY_PLAYLIST_DESCRIPTIONS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Trending community playlists' section.",
        f"Locate the playlist by '{creator}' with description '{desc}'.",
        f"Click the playlist link to open its details page.",
        f"Verify that the playlist page shows the creator '{creator}' and description '{desc}'.",
        "Do not play or sign in; only confirm playlist details are visible.",
    ]
    return {"task_type": "music_browse_community_playlist", "creator": creator, "description": desc, "steps": steps}

def music_browse_album_for_you(_: dict) -> dict:
    album = random.choice(ALBUMS_FOR_YOU)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Albums for you' section.",
        f"Locate the album '{album}'.",
        f"Click the album link to open its details page.",
        f"Verify that the album page shows the title '{album}'.",
        "Do not play or sign in; only confirm album details are visible.",
    ]
    return {"task_type": "music_browse_album_for_you", "album": album, "steps": steps}

def music_browse_all_time_essentials(_: dict) -> dict:
    playlist = random.choice(ALL_TIME_ESSENTIALS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Scroll to the 'All-time essentials' section.",
        f"Locate the playlist '{playlist}'.",
        f"Click the playlist link to open its details page.",
        f"Verify that the playlist page shows the title '{playlist}'.",
        "Do not play or sign in; only confirm playlist details are visible.",
    ]
    return {"task_type": "music_browse_all_time_essentials", "playlist": playlist, "steps": steps}

def music_browse_autumn_vibes(_: dict) -> dict:
    playlist = random.choice(AUTUMN_VIBES)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Fall is here🍂' or 'AUTUMN VIBES' section.",
        f"Locate the playlist '{playlist}'.",
        f"Click the playlist link to open its details page.",
        f"Verify that the playlist page shows the title '{playlist}'.",
        "Do not play or sign in; only confirm playlist details are visible.",
    ]
    return {"task_type": "music_browse_autumn_vibes", "playlist": playlist, "steps": steps}

def music_filter_quick_pick_by_artist(_: dict) -> dict:
    artist = random.choice(QUICK_PICK_ARTISTS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Quick picks' section.",
        f"Filter or visually scan for songs by artist '{artist}'.",
        f"Verify that at least one quick pick displays the artist '{artist}'.",
        "Do not play or sign in; only confirm presence.",
    ]
    return {"task_type": "music_filter_quick_pick_by_artist", "artist": artist, "steps": steps}

def music_filter_quick_pick_by_plays(_: dict) -> dict:
    plays = random.choice(QUICK_PICK_PLAYS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Quick picks' section.",
        f"Filter or visually scan for a song with '{plays}'.",
        f"Verify that at least one quick pick displays '{plays}'.",
        "Do not play or sign in; only confirm presence.",
    ]
    return {"task_type": "music_filter_quick_pick_by_plays", "plays": plays, "steps": steps}

def music_filter_album_by_artist(_: dict) -> dict:
    artist = random.choice(ALBUM_ARTISTS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Albums for you' section.",
        f"Filter or visually scan for albums by artist '{artist}'.",
        f"Verify that at least one album displays the artist '{artist}'.",
        "Do not play or sign in; only confirm presence.",
    ]
    return {"task_type": "music_filter_album_by_artist", "artist": artist, "steps": steps}

def music_filter_album_by_type(_: dict) -> dict:
    album_type = random.choice(ALBUM_TYPES)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Albums for you' section.",
        f"Filter or visually scan for albums labeled as '{album_type}'.",
        f"Verify that at least one album displays the type '{album_type}'.",
        "Do not play or sign in; only confirm presence.",
    ]
    return {"task_type": "music_filter_album_by_type", "album_type": album_type, "steps": steps}

def music_filter_playlist_by_views(_: dict) -> dict:
    views = random.choice(PLAYLIST_VIEWS)
    steps = [
        "Go to url 'https://music.youtube.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Trending community playlists' section.",
        f"Filter or visually scan for a playlist with '{views}'.",
        f"Verify that at least one playlist displays '{views}'.",
        "Do not play or sign in; only confirm presence.",
    ]
    return {"task_type": "music_filter_playlist_by_views", "views": views, "steps": steps}

_TASK_GENERATORS: Dict[MUSIC_TASK_TYPES, Callable[[dict], dict]] = {
    "music_search_song": music_search_song,
    "music_search_album": music_search_album,
    "music_search_artist": music_search_artist,
    "music_browse_genre_tab": music_browse_genre_tab,
    "music_play_quick_pick": music_play_quick_pick,
    "music_browse_trending_playlist": music_browse_trending_playlist,
    "music_browse_community_playlist": music_browse_community_playlist,
    "music_browse_album_for_you": music_browse_album_for_you,
    "music_browse_all_time_essentials": music_browse_all_time_essentials,
    "music_browse_autumn_vibes": music_browse_autumn_vibes,
    "music_filter_quick_pick_by_artist": music_filter_quick_pick_by_artist,
    "music_filter_quick_pick_by_plays": music_filter_quick_pick_by_plays,
    "music_filter_album_by_artist": music_filter_album_by_artist,
    "music_filter_album_by_type": music_filter_album_by_type,
    "music_filter_playlist_by_views": music_filter_playlist_by_views,
}

def generate_music_task(task_type: MUSIC_TASK_TYPES, payload: dict) -> dict:
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
    items = list(MUSIC_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_music_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)