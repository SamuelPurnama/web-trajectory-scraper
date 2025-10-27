import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

UG_TASK_TYPES = Literal[
    "ug_search_tabs",
    "ug_filter_by_type",
    "ug_filter_by_decade",
    "ug_filter_by_genre",
    "ug_featured_song_details",
    "ug_news_article_navigation",
    "ug_explore_tab_catalog",
    "ug_install_app_button",
    "ug_proplus_banner",
]

UG_SAMPLING_CONFIG: Dict[UG_TASK_TYPES, int] = {
    "ug_search_tabs": 10,
    "ug_filter_by_type": 10,
    "ug_filter_by_decade": 10,
    "ug_filter_by_genre": 10,
    "ug_featured_song_details": 10,
    "ug_news_article_navigation": 10,
    "ug_explore_tab_catalog": 10,
    "ug_install_app_button": 10,
    "ug_proplus_banner": 10,
}

SEARCH_TERMS = [
    "Stairway to Heaven", "Hotel California", "Nothing Else Matters", "Sweet Child O' Mine",
    "Wonderwall", "Hey Jude", "Smells Like Teen Spirit", "Imagine", "Let It Be", "Bohemian Rhapsody",
    "Knockin' on Heaven's Door", "Yesterday", "Comfortably Numb", "Blackbird", "Hallelujah",
    "Tears in Heaven", "Under the Bridge", "Highway to Hell", "Californication", "Zombie",
    "Creep", "Back in Black", "Layla", "Losing My Religion", "Time", "Sultans of Swing",
    "Paranoid", "Purple Haze", "Shallow", "Take Me Home, Country Roads"
]

TAB_TYPES = [
    "Chords", "Official", "Tab", "Ukulele", "Guitar Pro", "Bass"
]

DECADES = [
    "2020s", "2010s", "2000s", "1990s", "1980s", "1970s", "1960s", "1950s", "1940s", "1930s",
    "1920s", "1910s", "1900s", "1890s", "1880s", "1870s", "1860s", "1850s", "1840s", "1830s"
]

GENRES = [
    "Rock", "Metal", "Pop", "Folk", "Country", "Soundtrack", "Jazz", "Blues", "Classical",
    "Reggae", "Punk", "Hip-Hop", "Electronic", "Alternative", "Indie", "Funk", "Soul", "R&B",
    "Latin", "World", "Gospel", "Children", "Holiday", "Disco"
]

FEATURED_SONGS = [
    "Hey Joe Jimi Hendrix", "Wish You Were Here Pink Floyd", "Sweet Home Alabama Lynyrd Skynyrd",
    "Fear of the Dark Iron Maiden", "Still Loving You Scorpions", "I Got You I Feel Good James Brown",
    "Choosin Texas Ella Langley", "Man I Need Olivia Dean", "Sounds Like The Radio Zach Top",
    "The Man Who Sold The World Nirvana", "I Can Still Make Cheyenne George Strait",
    "Doin Time Sublime", "Isnt That Enough Shawn Mendes", "Lily And The Moon Thornhill",
    "Tennessee Orange Megan Moroney", "Firm Foundation He Wont Cody Carnes",
    "Pushing It Down And Praying Lizzy McAlpine", "10S Pantera", "Broken Window Serenade Whiskey Myers",
    "Bright Lights Matchbox Twenty", "Time Pink Floyd", "San Francisco The Mamas & The Papas",
    "Heaven Bryan Adams", "Dieter Meyers Inst Kaizers Orchestra", "Stick Season Her Version Deeps",
    "Sweater Weather The Neighbourhood", "Teenage Dirtbag Wheatus", "Save Me noheak125",
    "First Burn Lin-Manuel Miranda", "Wish You Were Here David Gilmour", "Pink Skies Zach Bryan"
]

NEWS_ARTICLES = [
    "Ex-Bandmate Claims Brent Hinds Has 'Entire Album' of Unheard Material, Reveals What He Was Really Like: 'He Wasn't Just Doing This for a Cheque'",
    "They Almost Fell Apart: Facing Tragedy and Turmoil, Their Unique Take on Prog Endured to Defy Genre Labels Amid 'Toxic' Fans",
    "'I'm Sure They're Getting Better, but…': Warren Haynes Admits He's Not Into Digital Amps (for Now), Explains Preference for Les Pauls Over SGs",
    "The Tone Is in the Blood? This Horror-Themed '90s Album Features an Evil 'Blood-Soaked' Guitar",
    "'It Got So Blown Out of Proportion': Slash Speaks Up on Axl Rose Meltdown, Gives Opinion on New Guns N' Roses Drummer Isaac Carpenter",
    "Billy Corgan on What David Gilmour Told Him About Pink Floyd's Struggles to Record as Syd Barrett's Mental Health Deteriorated: 'He Kind of Slid Into Total Madness'",
    "Folk Legend Shares 'Spinal Tap' Episode With Jeff Beck: 'It's a Train, and It's Going Helter-Skelter Down the F___ing Track'",
    "Hayley Williams Opens Up on Paramore's 'Unreal' Tour With Taylor Swift, Reveals Why She Has to Tear the Band Down: 'I've Been Sick of Us Like Twenty Times By Now'",
    "What Could Have Been: How a Punk Legend (Almost) Joined This Obscure Band That Pioneered Experimental Music",
    "'It's Not Made Up': The Real Meaning Behind Queens of the Stone Age's Name and Biggest Hit, EoDM Frontman Reveals",
    "Nicko McBrain Reveals if He'll Play on Iron Maiden's Next Album: 'I'm Still a Member of the Band, But What Does That Mean Exactly?'",
    "'Nobody Did That for Me Before': Rudy Sarzo Opens Up About Joining Ozzy's Band and Why the Prince of Darkness Was Really a Different Breed",
    "They're One of the Most Exciting Indie Rock Bands to Persist Today: 10 Years Ago, They Merged the Genre With the Big Screen Vibes",
    "'Most People Would Not Do That S__t': Bumblefoot Points Out What Actually Made Van Halen Stand Out",
    "'James Just Looks at Me and Shakes His Head': Les Claypool on His Botched Metallica Audition, and What Cliff Burton Thought of His Playing",
    "Eddie Van Halen's Guitar, Also Used By Mick Mars, Becomes Sixth Most Expensive Guitar Ever Sold, Here's How Much It Went For",
    "Everyone Knows David Bowie's Ziggy Stardust Persona: But Barely Anyone Has Heard of Obscure Rock Musician Who Actually Inspired It",
    "'If You Can't Do It in Two Takes, You Can't Do It. Roll It!': John 5 on How Cold-Calling David Lee Roth Got Him One of His Most Important Gigs",
    "'He's Writing Like Crazy': Bill Kelliher Seems to Confirm Mastodon's New Lead Guitarist",
    "'Not Me Trying to Show I Can Sing Better Than Ozzy': What Dio Really Thought of Singing Sabbath's Ozzy-Era Songs and Ozzy's Solo Success",
    "'She Was Not a Rush Fan': Geddy Lee on the 'Daunting Task' in Front of Rush's New Drummer",
    "Guns N' Roses Share Statement on Axl Rose's Recent Live Meltdown: 'The Issue Was Fixed'",
    "'Voice for the Voiceless': They Play Music That Could Literally Get Them Executed in Their Country, and They Do It Anyway",
    "'You Want Us to Reconfigure the Whole Thing Every Night?' Tobias Forge Speaks Up on Recent Criticism Aimed at Ghost Shows",
    "He's One of the Finest Modern Guitarists, and His Music Can Help You Start Tapping: Young Virtuoso Sammy Boller Reveals What You Need to Know"
]

CATALOG_ACTIONS = [
    "Click 'EXPLORE' under 'EXPLORE TAB CATALOG' and verify navigation to the tab catalog page.",
    "Click 'Show All' under 'TYPE' and verify all tab types are listed.",
    "Click 'Show All' under 'DECADE' and verify all decades are listed.",
    "Click 'Show All' under 'GENRE' and verify all genres are listed.",
    "Click the 'Tabs' main navigation and verify tabs page loads.",
    "Click the 'Songbooks' main navigation and verify songbooks page loads.",
    "Click the 'Articles' main navigation and verify articles page loads.",
    "Click the 'Forums' main navigation and verify forums page loads.",
    "Click the 'Publish tab' main navigation and verify publish interface loads.",
    "Click the 'Pro+' main navigation and verify Pro+ page loads.",
    "Click the 'Courses' main navigation and verify courses page loads.",
    "Click the 'Top Hits' button and verify top hits are displayed.",
    "Click the '90s Alternative' button and verify alternative songs from the 90s are displayed.",
    "Click 'Classic Rock' text and verify classic rock songs are shown.",
    "Click the 'START NOW' link in the Pro+ banner and verify Pro+ signup or info page loads.",
    "Click 'EXPLORE' under 'SHOTS' and verify navigation to the shots section.",
    "Click the 'Hot' button under #WHATSUP and verify hot news or tabs are displayed.",
    "Click 'News' link in a news article and verify news section loads.",
    "Click a comment count link (e.g., '1 comment') and verify comments are displayed.",
    "Click a tag link (e.g., 'Metal', 'Music business') in a news article and verify tag filtering."
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, banners, or cookie notices if present.",
        "Do not sign in, purchase, or submit any personal information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Ultimate Guitar", steps).model_dump()

def ug_search_tabs(_: dict) -> dict:
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Locate the searchbox labeled 'Enter artist name or song title'.",
        f"Type '{term}' into the searchbox.",
        "Click the 'Search' button.",
        f"Verify that search results for '{term}' are displayed.",
        "Assert that at least one result is shown.",
        "Assert that the searchbox value is '{term}'.",
        "Assert that the URL contains 'search'.",
        "If no results, assert that a 'No results' or similar message is shown."
    ]
    return {
        "task_type": "ug_search_tabs",
        "search_term": term,
        "steps": steps,
        "assertion": f"Results for '{term}' are visible or a 'No results' message is shown."
    }

def ug_filter_by_type(_: dict) -> dict:
    tab_type = random.choice(TAB_TYPES)
    steps = [
        "Go to url 'https://www.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Scroll to the 'TYPE' section.",
        f"Click the '{tab_type}' link.",
        f"Verify that tabs of type '{tab_type}' are displayed.",
        "Assert that the filter for tab type is active.",
        "Assert that the tab count shown matches the type selected.",
        "If no results, assert that a 'No results' or similar message is shown."
    ]
    return {
        "task_type": "ug_filter_by_type",
        "tab_type": tab_type,
        "steps": steps,
        "assertion": f"Tabs of type '{tab_type}' are listed or a 'No results' message is shown."
    }

def ug_filter_by_decade(_: dict) -> dict:
    decade = random.choice(DECADES)
    steps = [
        "Go to url 'https://www.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Scroll to the 'DECADE' section.",
        f"Click the '{decade}' link.",
        f"Verify that tabs from the '{decade}' are displayed.",
        "Assert that the filter for decade is active.",
        "Assert that the tab count shown matches the decade selected.",
        "If no results, assert that a 'No results' or similar message is shown."
    ]
    return {
        "task_type": "ug_filter_by_decade",
        "decade": decade,
        "steps": steps,
        "assertion": f"Tabs from the '{decade}' are listed or a 'No results' message is shown."
    }

def ug_filter_by_genre(_: dict) -> dict:
    genre = random.choice(GENRES)
    steps = [
        "Go to url 'https://www.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Scroll to the 'GENRE' section.",
        f"Click the '{genre}' link.",
        f"Verify that tabs from the '{genre}' genre are displayed.",
        "Assert that the filter for genre is active.",
        "Assert that the tab count shown matches the genre selected.",
        "If no results, assert that a 'No results' or similar message is shown."
    ]
    return {
        "task_type": "ug_filter_by_genre",
        "genre": genre,
        "steps": steps,
        "assertion": f"Tabs from the '{genre}' genre are listed or a 'No results' message is shown."
    }

def ug_featured_song_details(_: dict) -> dict:
    song = random.choice(FEATURED_SONGS)
    steps = [
        "Go to url 'https://www.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Scroll to the 'FEATURED' or 'Top Hits' section.",
        f"Click the featured song link '{song}'.",
        f"Verify that the song page for '{song}' loads.",
        "Assert that the song title matches '{song}'.",
        "Assert that chords or tabs are present on the page.",
        "Assert that the URL contains the song's name or artist.",
        "If the song page fails to load, assert that an error or 'Not found' message is shown."
    ]
    return {
        "task_type": "ug_featured_song_details",
        "featured_song": song,
        "steps": steps,
        "assertion": f"Song page for '{song}' loads with chords/tabs or an error message is shown."
    }

def ug_news_article_navigation(_: dict) -> dict:
    article = random.choice(NEWS_ARTICLES)
    steps = [
        "Go to url 'https://www.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Scroll to the '#WHATSUP' or news section.",
        f"Click the news article link '{article}'.",
        f"Verify that the article page for '{article}' loads.",
        "Assert that the article title matches '{article}'.",
        "Assert that the article body or content is visible.",
        "Assert that the URL contains 'news' or the article's slug.",
        "If the article fails to load, assert that an error or 'Not found' message is shown."
    ]
    return {
        "task_type": "ug_news_article_navigation",
        "news_article": article,
        "steps": steps,
        "assertion": f"Article page for '{article}' loads with content or an error message is shown."
    }

def ug_explore_tab_catalog(_: dict) -> dict:
    action = random.choice(CATALOG_ACTIONS)
    steps = [
        "Go to url 'https://www.ultimate-guitar.com'.",
        *_ui_hygiene(),
        action,
        "Assert that the destination page or section loads as expected.",
        "If navigation fails, assert that an error or 'Not found' message is shown."
    ]
    return {
        "task_type": "ug_explore_tab_catalog",
        "catalog_action": action,
        "steps": steps,
        "assertion": "Navigation to the catalog section or feature is successful or an error message is shown."
    }

def ug_install_app_button(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Locate the 'Install' button near the top of the page.",
        "Click the 'Install' button.",
        "Verify that an installation prompt, modal, or download page appears.",
        "Assert that the page or modal mentions 'Ultimate Guitar' app installation.",
        "If no prompt appears, assert that the button is disabled or a message is shown."
    ]
    return {
        "task_type": "ug_install_app_button",
        "steps": steps,
        "assertion": "Installation prompt/modal or download page for the app is shown."
    }

def ug_proplus_banner(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.ultimate-guitar.com'.",
        *_ui_hygiene(),
        "Scroll to the 'PRO+ | LEARN SONGS EASIER AND FASTER' banner.",
        "Click the 'START NOW' link or button in the Pro+ banner.",
        "Verify that the Pro+ signup or information page loads.",
        "Assert that the page mentions 'Pro+' or 'Pro experience'.",
        "Assert that the URL contains 'pro' or similar.",
        "If the page fails to load, assert that an error or 'Not found' message is shown."
    ]
    return {
        "task_type": "ug_proplus_banner",
        "steps": steps,
        "assertion": "Pro+ info or signup page loads or an error message is shown."
    }

_TASK_GENERATORS: Dict[UG_TASK_TYPES, Callable[[dict], dict]] = {
    "ug_search_tabs": ug_search_tabs,
    "ug_filter_by_type": ug_filter_by_type,
    "ug_filter_by_decade": ug_filter_by_decade,
    "ug_filter_by_genre": ug_filter_by_genre,
    "ug_featured_song_details": ug_featured_song_details,
    "ug_news_article_navigation": ug_news_article_navigation,
    "ug_explore_tab_catalog": ug_explore_tab_catalog,
    "ug_install_app_button": ug_install_app_button,
    "ug_proplus_banner": ug_proplus_banner,
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