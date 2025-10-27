import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

UG_TASK_TYPES = Literal[
    "ug_search_song",
    "ug_filter_genre",
    "ug_filter_difficulty",
    "ug_filter_tuning",
    "ug_filter_decade",
    "ug_filter_instrument",
    "ug_filter_key",
    "ug_filter_part",
    "ug_browse_artist_letter",
    "ug_view_tab_details",
    "ug_sort_by_hits",
    "ug_sort_by_rating",
    "ug_filter_acoustic",
]

UG_SAMPLING_CONFIG: Dict[UG_TASK_TYPES, int] = {
    "ug_search_song": 10,
    "ug_filter_genre": 10,
    "ug_filter_difficulty": 10,
    "ug_filter_tuning": 10,
    "ug_filter_decade": 10,
    "ug_filter_instrument": 10,
    "ug_filter_key": 10,
    "ug_filter_part": 10,
    "ug_browse_artist_letter": 10,
    "ug_view_tab_details": 10,
    "ug_sort_by_hits": 10,
    "ug_sort_by_rating": 10,
    "ug_filter_acoustic": 10,
}

UG_SEARCH_TERMS = [
    "Wonderwall", "Hotel California", "Creep", "Let It Be", "Yesterday", "Hallelujah", "Knockin On Heavens Door",
    "Perfect", "Iris", "Zombie", "Wish You Were Here", "Riptide", "All Of Me", "Landslide", "Photograph",
    "Fly Me To The Moon", "Let Her Go", "Viva La Vida", "Sparks", "Best Part", "Wildflower", "Take Me Home Country Roads",
    "Someone Like You", "So Easy To Fall In Love", "Nothing Else Matters", "Where Is My Mind", "Hey Jude", "Stand By Me",
    "The Night We Met", "Die With A Smile", "Goodness Of God", "House Of The Rising Sun", "Sailor Song", "Linger Acoustic",
    "Man I Need", "Shallow", "Somewhere Only We Know", "The Fate Of Ophelia", "Golden", "Intro", "Solo", "Album", "Whole song"
][:30]

UG_GENRES = [
    "Rock", "Metal", "Pop", "Folk", "Country", "Jazz", "Blues", "Classical", "Reggae", "Punk", "Alternative", "Indie",
    "Electronic", "Hip-Hop", "R&B", "Soul", "Funk", "Latin", "World", "Gospel", "Soundtrack", "Children", "Holiday",
    "Experimental", "Progressive", "Hard Rock", "Singer-songwriter", "Pop Rock", "Alternative Rock", "Indie Rock", "Hardcore"
][:30]

UG_DIFFICULTIES = [
    "Absolute Beginner", "Beginner", "Intermediate", "Advanced", "Expert", "Easy", "Medium", "Hard", "Very Hard",
    "Novice", "Pro", "Intermediate+", "Intermediate-", "Advanced+", "Advanced-", "Beginner+", "Beginner-", "Expert+",
    "Expert-", "All Levels"
][:20]

UG_TUNINGS = [
    "Standard", "Half-Step Down", "Drop D", "Drop C", "Open G", "Open D", "Open E", "Open A", "Double Drop D",
    "DADGAD", "C Standard", "Eb Standard", "Drop B", "Drop A", "Open C", "Open F", "Open B", "Open Bb", "Open Ab",
    "G C E A", "F A D G", "E A D G", "C G D A", "B E A D", "A D G C"
][:24]

UG_DECADES = [
    "2020s", "2010s", "2000s", "1990s", "1980s", "1970s", "1960s", "1950s", "1940s", "1930s", "1920s", "1910s",
    "1900s", "1890s", "1880s", "1870s", "1860s", "1850s", "1840s", "1830s"
][:20]

UG_INSTRUMENTS = [
    "Acoustic Guitar (steel)", "Acoustic Guitar (nylon)", "Electric Guitar", "Distortion Guitar", "Overdriven Guitar",
    "Electric Bass (finger)", "Electric Bass (pick)", "Drums", "Piano", "Keyboard", "Synthesizer", "Ukulele", "Banjo",
    "Mandolin", "Violin", "Cello", "Saxophone", "Trumpet", "Flute", "Percussion", "Harmonica", "Clarinet", "Trombone",
    "Double Bass", "Accordion"
][:24]

UG_KEYS = [
    "C", "G", "D", "E", "A", "F", "B", "Bb", "Eb", "Ab", "Db", "Gb", "C#", "G#", "D#", "A#", "E#", "B#", "F#", "Cb"
][:20]

UG_PARTS = [
    "Whole song", "Intro", "Solo", "Verse", "Chorus", "Bridge", "Outro", "Pre-Chorus", "Interlude", "Instrumental",
    "Breakdown", "Riff", "Verse 1", "Verse 2", "Chorus 2", "Solo 2", "Bridge 2", "Ending", "Album", "Medley"
][:20]

UG_ARTIST_LETTERS = list("#ABCDEFGHIJKLMNOPQRSTUVWXYZ")[:27]

UG_SORTS = ["hits", "rating"]

UG_ACOUSTIC = ["Acoustic", "Non-acoustic"]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, banners, or advertisements if present.",
        "Do not attempt to sign up, log in, or purchase anything.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Ultimate-Guitar", steps).model_dump()

def ug_search_song(_: dict) -> dict:
    term = random.choice(UG_SEARCH_TERMS)
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Focus the search box labeled 'Enter artist name or song title'.",
        f"Type '{term}' and press Enter or click 'Search'.",
        f"Wait for search results to load for '{term}'.",
        f"Verify at least one result is shown for '{term}'.",
        "If no results, assert a 'no results' message is displayed.",
    ]
    return {"task_type": "ug_search_song", "search_term": term, "steps": steps}

def ug_filter_genre(_: dict) -> dict:
    genre = random.choice(UG_GENRES)
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        f"Locate the 'GENRE' filter section.",
        f"Click the '{genre}' link under 'GENRE'.",
        f"Wait for the page to update to show only '{genre}' genre tabs.",
        f"Verify that the first 3 results are labeled with the '{genre}' genre or a related tag.",
        "If no results, assert a 'no results' or 'no tabs found' message is displayed.",
    ]
    return {"task_type": "ug_filter_genre", "genre": genre, "steps": steps}

def ug_filter_difficulty(_: dict) -> dict:
    diff = random.choice(UG_DIFFICULTIES)
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Locate the 'DIFFICULTY' filter section.",
        f"Click the '{diff}' link under 'DIFFICULTY'.",
        f"Wait for the page to update to show only '{diff}' difficulty tabs.",
        f"Verify that the first 3 results are labeled as '{diff}' or equivalent.",
        "If no results, assert a 'no results' or 'no tabs found' message is displayed.",
    ]
    return {"task_type": "ug_filter_difficulty", "difficulty": diff, "steps": steps}

def ug_filter_tuning(_: dict) -> dict:
    tuning = random.choice(UG_TUNINGS)
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Locate the 'TUNING' filter section.",
        f"Click the '{tuning}' link under 'TUNING'.",
        f"Wait for the page to update to show only tabs in '{tuning}' tuning.",
        f"Verify that the first 3 results display tuning as '{tuning}' or equivalent.",
        "If no results, assert a 'no results' or 'no tabs found' message is displayed.",
    ]
    return {"task_type": "ug_filter_tuning", "tuning": tuning, "steps": steps}

def ug_filter_decade(_: dict) -> dict:
    decade = random.choice(UG_DECADES)
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Locate the 'DECADE' filter section.",
        f"Click the '{decade}' link under 'DECADE'.",
        f"Wait for the page to update to show only tabs from the '{decade}'.",
        f"Verify that the first 3 results are from the '{decade}' (check year or tag).",
        "If no results, assert a 'no results' or 'no tabs found' message is displayed.",
    ]
    return {"task_type": "ug_filter_decade", "decade": decade, "steps": steps}

def ug_filter_instrument(_: dict) -> dict:
    instrument = random.choice(UG_INSTRUMENTS)
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Locate the 'INSTRUMENT' filter section.",
        f"Click the '{instrument}' link under 'INSTRUMENT'.",
        f"Wait for the page to update to show only tabs for '{instrument}'.",
        f"Verify that the first 3 results include '{instrument}' as instrument or tag.",
        "If no results, assert a 'no results' or 'no tabs found' message is displayed.",
    ]
    return {"task_type": "ug_filter_instrument", "instrument": instrument, "steps": steps}

def ug_filter_key(_: dict) -> dict:
    key = random.choice(UG_KEYS)
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Locate the 'KEY' filter section.",
        f"Click the '{key}' link under 'KEY'.",
        f"Wait for the page to update to show only tabs in the key of '{key}'.",
        f"Verify that the first 3 results display key as '{key}' or equivalent.",
        "If no results, assert a 'no results' or 'no tabs found' message is displayed.",
    ]
    return {"task_type": "ug_filter_key", "key": key, "steps": steps}

def ug_filter_part(_: dict) -> dict:
    part = random.choice(UG_PARTS)
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Locate the 'PART' filter section.",
        f"Click the '{part}' link under 'PART'.",
        f"Wait for the page to update to show only tabs for '{part}'.",
        f"Verify that the first 3 results include '{part}' as part or tag.",
        "If no results, assert a 'no results' or 'no tabs found' message is displayed.",
    ]
    return {"task_type": "ug_filter_part", "part": part, "steps": steps}

def ug_browse_artist_letter(_: dict) -> dict:
    letter = random.choice(UG_ARTIST_LETTERS)
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Scroll to the 'All artists' section.",
        f"Click the '{letter}' link to browse artists starting with '{letter}'.",
        f"Wait for the artist list to update to '{letter}'.",
        f"Verify that at least one artist name starts with '{letter}' (or, for '#', a number).",
        "If no artists, assert a 'no results' or 'no artists found' message is displayed.",
    ]
    return {"task_type": "ug_browse_artist_letter", "artist_letter": letter, "steps": steps}

def ug_view_tab_details(_: dict) -> dict:
    term = random.choice(UG_SEARCH_TERMS)
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Focus the search box labeled 'Enter artist name or song title'.",
        f"Type '{term}' and press Enter or click 'Search'.",
        f"Wait for search results to load for '{term}'.",
        "Click the first result to open its tab details page.",
        "Verify that the tab details page loads and displays chords or tablature.",
        "Check that the song title matches '{term}' (case-insensitive, partial match allowed).",
    ]
    return {"task_type": "ug_view_tab_details", "search_term": term, "steps": steps}

def ug_sort_by_hits(_: dict) -> dict:
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Locate the 'HITS' column header or sort option.",
        "Click to sort results by number of hits (descending).",
        "Verify that the first 3 results have hits counts in descending order.",
        "If sorting fails, assert that the 'HITS' column is unchanged.",
    ]
    return {"task_type": "ug_sort_by_hits", "steps": steps}

def ug_sort_by_rating(_: dict) -> dict:
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Locate the 'RATING' column header or sort option.",
        "Click to sort results by rating (descending).",
        "Verify that the first 3 results have ratings in descending order.",
        "If sorting fails, assert that the 'RATING' column is unchanged.",
    ]
    return {"task_type": "ug_sort_by_rating", "steps": steps}

def ug_filter_acoustic(_: dict) -> dict:
    acoustic = random.choice(UG_ACOUSTIC)
    steps = [
        "Go to url 'https://tabs.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Locate the 'ACOUSTIC' filter section.",
        f"Click the '{acoustic}' link under 'ACOUSTIC'.",
        f"Wait for the page to update to show only '{acoustic}' tabs.",
        f"Verify that the first 3 results are labeled as '{acoustic}' or equivalent.",
        "If no results, assert a 'no results' or 'no tabs found' message is displayed.",
    ]
    return {"task_type": "ug_filter_acoustic", "acoustic": acoustic, "steps": steps}

_TASK_GENERATORS: Dict[UG_TASK_TYPES, Callable[[dict], dict]] = {
    "ug_search_song": ug_search_song,
    "ug_filter_genre": ug_filter_genre,
    "ug_filter_difficulty": ug_filter_difficulty,
    "ug_filter_tuning": ug_filter_tuning,
    "ug_filter_decade": ug_filter_decade,
    "ug_filter_instrument": ug_filter_instrument,
    "ug_filter_key": ug_filter_key,
    "ug_filter_part": ug_filter_part,
    "ug_browse_artist_letter": ug_browse_artist_letter,
    "ug_view_tab_details": ug_view_tab_details,
    "ug_sort_by_hits": ug_sort_by_hits,
    "ug_sort_by_rating": ug_sort_by_rating,
    "ug_filter_acoustic": ug_filter_acoustic,
}

def generate_ug_task(task_type: UG_TASK_TYPES, payload: dict) -> dict:
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
    items = list(UG_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_ug_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)