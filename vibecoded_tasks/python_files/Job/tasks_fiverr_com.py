import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

FIVERR_TASK_TYPES = Literal[
    "fiverr_search_gig",
    "fiverr_filter_category",
    "fiverr_filter_price",
    "fiverr_filter_delivery_time",
    "fiverr_filter_seller_level",
    "fiverr_filter_language",
    "fiverr_sort_results",
    "fiverr_gig_detail_view",
    "fiverr_help_center_topic",
    "fiverr_signup_form_validation",
    "fiverr_login_form_validation",
    "fiverr_browse_categories",
]

FIVERR_SAMPLING_CONFIG: Dict[FIVERR_TASK_TYPES, int] = {
    "fiverr_search_gig": 10,
    "fiverr_filter_category": 10,
    "fiverr_filter_price": 10,
    "fiverr_filter_delivery_time": 10,
    "fiverr_filter_seller_level": 10,
    "fiverr_filter_language": 10,
    "fiverr_sort_results": 10,
    "fiverr_gig_detail_view": 10,
    "fiverr_help_center_topic": 10,
    "fiverr_signup_form_validation": 10,
    "fiverr_login_form_validation": 10,
    "fiverr_browse_categories": 10,
}

SEARCH_TERMS = [
    "logo design", "wordpress", "voice over", "video editing", "business card", "SEO", "translation",
    "data entry", "resume writing", "social media", "animation", "illustration", "music production",
    "web development", "app development", "copywriting", "email marketing", "product description",
    "shopify", "podcast editing", "UI UX", "NFT art", "book cover", "3D modeling", "virtual assistant",
    "transcription", "proofreading", "content writing", "brand style guide", "flyer design", "presentation design"
]

CATEGORIES = [
    "Graphics & Design", "Digital Marketing", "Writing & Translation", "Video & Animation",
    "Music & Audio", "Programming & Tech", "Business", "Lifestyle", "Data", "Photography",
    "AI Services", "Web Programming", "Mobile Apps", "E-Commerce", "Game Development",
    "Branding", "Social Media", "SEO", "Email Marketing", "Legal Consulting", "Financial Consulting",
    "Architecture", "Interior Design", "Fashion", "Fitness", "Cooking", "Crafts", "Parenting", "Travel", "Online Tutoring"
]

PRICE_RANGES = [
    (5, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 75), (75, 100), (100, 150), (150, 200),
    (200, 250), (250, 300), (300, 350), (350, 400), (400, 500), (500, 600), (600, 750), (750, 1000),
    (1000, 1500), (1500, 2000), (2000, 3000), (3000, 5000)
]

DELIVERY_TIMES = [
    "Express 24H", "Up to 3 days", "Up to 7 days", "Up to 14 days", "Up to 30 days",
    "Same Day", "2 Days", "5 Days", "10 Days", "15 Days", "20 Days", "1 Week", "2 Weeks",
    "3 Weeks", "1 Month", "Flexible", "Custom", "48 Hours", "72 Hours", "6 Hours", "12 Hours"
]

SELLER_LEVELS = [
    "Top Rated Seller", "Level Two", "Level One", "New Seller", "Pro Verified", "Rising Talent",
    "Fiverr's Choice", "Studio", "Agency", "Certified", "Elite", "Premium", "Standard", "Basic",
    "Community Favorite", "Recommended", "Popular", "Trending", "Most Reviewed", "Best Rated", "Recently Joined"
]

LANGUAGES = [
    "English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Chinese", "Japanese",
    "Korean", "Arabic", "Hindi", "Turkish", "Polish", "Hebrew", "Swedish", "Danish", "Finnish", "Norwegian",
    "Greek", "Czech", "Hungarian", "Romanian", "Thai"
]

SORT_OPTIONS = [
    "Best Selling", "Newest Arrivals", "Recommended", "Price: Low to High", "Price: High to Low",
    "Most Reviewed", "Most Relevant", "Fast Delivery", "Top Rated", "Popular", "Trending",
    "Pro Services", "Local Sellers", "Online Sellers", "Rising Talent", "Recently Joined",
    "Highest Rated", "Lowest Rated", "Most Orders", "Fewest Orders"
]

HELP_TOPICS = [
    ("Account & Profile", "account-profile"),
    ("Payments & Billing", "payments-billing"),
    ("Orders", "orders"),
    ("Gigs", "gigs"),
    ("Fiverr Business", "fiverr-business"),
    ("Fiverr Pro", "fiverr-pro"),
    ("Trust & Safety", "trust-safety"),
    ("Resolution Center", "resolution-center"),
    ("Fiverr Learn", "fiverr-learn"),
    ("Fiverr Logo Maker", "logo-maker"),
    ("Fiverr Studios", "studios"),
    ("Fiverr Workspace", "workspace"),
    ("Fiverr Affiliates", "affiliates"),
    ("Fiverr Elevate", "elevate"),
    ("Fiverr Community", "community"),
    ("Fiverr Events", "events"),
    ("Fiverr Support", "support"),
    ("Fiverr Mobile App", "mobile-app"),
    ("Fiverr Seller Plus", "seller-plus"),
    ("Fiverr Briefs", "briefs"),
    ("Fiverr Certified", "certified"),
    ("Fiverr Guides", "guides"),
    ("Fiverr Blog", "blog"),
    ("Fiverr Help Center", "help-center"),
    ("Fiverr Resources", "resources")
]

BROWSE_CATEGORIES = [
    "Logo Design", "WordPress", "Voice Over", "Video Editing", "Business Cards", "SEO", "Translation",
    "Data Entry", "Resume Writing", "Social Media", "Animation", "Illustration", "Music Production",
    "Web Development", "App Development", "Copywriting", "Email Marketing", "Product Description",
    "Shopify", "Podcast Editing", "UI UX", "NFT Art", "Book Cover", "3D Modeling", "Virtual Assistant",
    "Transcription", "Proofreading", "Content Writing", "Brand Style Guide", "Flyer Design", "Presentation Design"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, notifications, or promotional banners) before proceeding.",
        "Do not attempt to purchase or submit payment; only view and interact with public content.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Fiverr", steps).model_dump()

def fiverr_search_gig(_: dict) -> dict:
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.fiverr.com'.",
        *_ui_hygiene(),
        "Locate the main search input box (with placeholder like 'What service are you looking for?').",
        f"Type '{term}' into the search box.",
        "Submit the search (press Enter or click the search icon).",
        "Wait for the results page to load.",
        f"Verify that at least one gig card is visible and that the search term '{term}' appears in the results page header or in the gig cards.",
        "Assert that the URL contains the search term (case-insensitive, spaces replaced by hyphens or encoded)."
    ]
    return {
        "task_type": "fiverr_search_gig",
        "search_term": term,
        "steps": steps,
        "assertions": [
            "At least one gig card is present.",
            "Search term is reflected in the page header or gig titles.",
            "URL reflects the search term."
        ]
    }

def fiverr_filter_category(_: dict) -> dict:
    cat = random.choice(CATEGORIES)
    steps = [
        "Go to url 'https://www.fiverr.com'.",
        *_ui_hygiene(),
        "Locate the 'Categories' menu or navigation bar.",
        f"Click on the '{cat}' category.",
        "Wait for the category page to load.",
        f"Verify that the category name '{cat}' appears in the page header or breadcrumb.",
        "Assert that at least one gig card is visible.",
        "Assert that the URL contains a slug or keyword matching the category."
    ]
    return {
        "task_type": "fiverr_filter_category",
        "category": cat,
        "steps": steps,
        "assertions": [
            "Category header or breadcrumb matches selected category.",
            "At least one gig card is present.",
            "URL contains the category slug."
        ]
    }

def fiverr_filter_price(_: dict) -> dict:
    min_price, max_price = random.choice(PRICE_RANGES)
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.fiverr.com'.",
        *_ui_hygiene(),
        f"Search for '{term}' in the main search box.",
        "Wait for the results page to load.",
        "Locate the price filter controls (slider or min/max input fields).",
        f"Set minimum price to ${min_price} and maximum price to ${max_price}.",
        "Apply the price filter.",
        "Wait for the filtered results to load.",
        f"Assert that all visible gig cards show a price within ${min_price} - ${max_price}.",
        "Assert that at least one gig card is present after filtering."
    ]
    return {
        "task_type": "fiverr_filter_price",
        "search_term": term,
        "min_price": min_price,
        "max_price": max_price,
        "steps": steps,
        "assertions": [
            "All visible gig cards are within the selected price range.",
            "At least one gig card is present."
        ]
    }

def fiverr_filter_delivery_time(_: dict) -> dict:
    delivery = random.choice(DELIVERY_TIMES)
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.fiverr.com'.",
        *_ui_hygiene(),
        f"Search for '{term}' in the main search box.",
        "Wait for the results page to load.",
        "Locate the 'Delivery Time' filter.",
        f"Select '{delivery}' as the delivery time filter.",
        "Apply the filter and wait for results to update.",
        f"Assert that all visible gig cards show a delivery time matching or faster than '{delivery}'.",
        "Assert that at least one gig card is present."
    ]
    return {
        "task_type": "fiverr_filter_delivery_time",
        "search_term": term,
        "delivery_time": delivery,
        "steps": steps,
        "assertions": [
            "All visible gig cards match or are faster than the selected delivery time.",
            "At least one gig card is present."
        ]
    }

def fiverr_filter_seller_level(_: dict) -> dict:
    level = random.choice(SELLER_LEVELS)
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.fiverr.com'.",
        *_ui_hygiene(),
        f"Search for '{term}' in the main search box.",
        "Wait for the results page to load.",
        "Locate the 'Seller Level' filter.",
        f"Select '{level}' as the seller level filter.",
        "Apply the filter and wait for results to update.",
        f"Assert that all visible gig cards display the seller level '{level}' or higher.",
        "Assert that at least one gig card is present."
    ]
    return {
        "task_type": "fiverr_filter_seller_level",
        "search_term": term,
        "seller_level": level,
        "steps": steps,
        "assertions": [
            "All visible gig cards display the selected seller level.",
            "At least one gig card is present."
        ]
    }

def fiverr_filter_language(_: dict) -> dict:
    lang = random.choice(LANGUAGES)
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.fiverr.com'.",
        *_ui_hygiene(),
        f"Search for '{term}' in the main search box.",
        "Wait for the results page to load.",
        "Locate the 'Seller Language' filter.",
        f"Select '{lang}' as the language filter.",
        "Apply the filter and wait for results to update.",
        f"Assert that all visible gig cards are from sellers who speak '{lang}'.",
        "Assert that at least one gig card is present."
    ]
    return {
        "task_type": "fiverr_filter_language",
        "search_term": term,
        "language": lang,
        "steps": steps,
        "assertions": [
            "All visible gig cards are from sellers who speak the selected language.",
            "At least one gig card is present."
        ]
    }

def fiverr_sort_results(_: dict) -> dict:
    sort = random.choice(SORT_OPTIONS)
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.fiverr.com'.",
        *_ui_hygiene(),
        f"Search for '{term}' in the main search box.",
        "Wait for the results page to load.",
        "Locate the sort dropdown or controls.",
        f"Select '{sort}' as the sort order.",
        "Wait for results to update.",
        f"Assert that the gig cards are sorted by '{sort}' (e.g., check first few cards for expected order).",
        "Assert that at least one gig card is present."
    ]
    return {
        "task_type": "fiverr_sort_results",
        "search_term": term,
        "sort_option": sort,
        "steps": steps,
        "assertions": [
            "Gig cards are sorted according to the selected sort option.",
            "At least one gig card is present."
        ]
    }

def fiverr_gig_detail_view(_: dict) -> dict:
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.fiverr.com'.",
        *_ui_hygiene(),
        f"Search for '{term}' in the main search box.",
        "Wait for the results page to load.",
        "Click on the first gig card to open its detail page.",
        "Wait for the gig detail page to load.",
        "Assert that the gig title, seller name, price, and description are visible.",
        "Assert that the URL contains '/gig/' or a gig slug."
    ]
    return {
        "task_type": "fiverr_gig_detail_view",
        "search_term": term,
        "steps": steps,
        "assertions": [
            "Gig title, seller name, price, and description are visible.",
            "URL contains '/gig/' or gig slug."
        ]
    }

def fiverr_help_center_topic(_: dict) -> dict:
    topic, slug = random.choice(HELP_TOPICS)
    steps = [
        "Go to url 'https://www.fiverr.com/support'.",
        *_ui_hygiene(),
        f"Locate and click on the help topic '{topic}'.",
        "Wait for the help topic page or section to load.",
        f"Assert that the topic header or breadcrumb matches '{topic}'.",
        "Assert that at least one FAQ or article is visible."
    ]
    return {
        "task_type": "fiverr_help_center_topic",
        "help_topic": topic,
        "steps": steps,
        "assertions": [
            "Topic header or breadcrumb matches selected topic.",
            "At least one FAQ or article is visible."
        ]
    }

def fiverr_signup_form_validation(_: dict) -> dict:
    # Use a variety of invalid and valid emails/usernames for edge/negative checks
    emails = [
        "testuser@example.com", "user123@gmail.com", "hello.world@domain.co", "invalid-email", "user@.com",
        "user@domain", "user@domain.c", "user@domain.comm", "user@@domain.com", "user@domain..com",
        "user@domain.com.", ".user@domain.com", "user@domain.com-", "user@-domain.com", "user@domain_com.com",
        "user@domain.com_", "user@domain.com!", "user@domain,com", "user@domain#com", "user@domain$com"
    ]
    email = random.choice(emails)
    steps = [
        "Go to url 'https://www.fiverr.com/join'.",
        *_ui_hygiene(),
        "Locate the signup form.",
        f"Enter '{email}' as the email address.",
        "Enter 'TestUser123' as the username.",
        "Enter 'TestPassword!23' as the password.",
        "Submit the signup form.",
        "If the email is invalid, assert that an error message is shown.",
        "If the email is valid, assert that a confirmation or next-step message is shown."
    ]
    return {
        "task_type": "fiverr_signup_form_validation",
        "email": email,
        "steps": steps,
        "assertions": [
            "Error message appears for invalid emails.",
            "Confirmation or next-step message appears for valid emails."
        ]
    }

def fiverr_login_form_validation(_: dict) -> dict:
    # Use a variety of invalid and valid emails for negative/edge checks
    emails = [
        "testuser@example.com", "user123@gmail.com", "hello.world@domain.co", "invalid-email", "user@.com",
        "user@domain", "user@domain.c", "user@domain.comm", "user@@domain.com", "user@domain..com",
        "user@domain.com.", ".user@domain.com", "user@domain.com-", "user@-domain.com", "user@domain_com.com",
        "user@domain.com_", "user@domain.com!", "user@domain,com", "user@domain#com", "user@domain$com"
    ]
    email = random.choice(emails)
    steps = [
        "Go to url 'https://www.fiverr.com/login'.",
        *_ui_hygiene(),
        "Locate the login form.",
        f"Enter '{email}' as the email address.",
        "Enter 'FakePassword123!' as the password.",
        "Submit the login form.",
        "Assert that an error message is shown for invalid credentials.",
        "Assert that no user dashboard is shown after failed login."
    ]
    return {
        "task_type": "fiverr_login_form_validation",
        "email": email,
        "steps": steps,
        "assertions": [
            "Error message appears for invalid credentials.",
            "No user dashboard is shown after failed login."
        ]
    }

def fiverr_browse_categories(_: dict) -> dict:
    cat = random.choice(BROWSE_CATEGORIES)
    steps = [
        "Go to url 'https://www.fiverr.com'.",
        *_ui_hygiene(),
        "Locate the 'Browse Categories' or main navigation area.",
        f"Click on '{cat}'.",
        "Wait for the category page to load.",
        f"Assert that the category name '{cat}' appears in the page header or breadcrumb.",
        "Assert that at least one gig card is visible.",
        "Assert that the URL contains a slug or keyword matching the category."
    ]
    return {
        "task_type": "fiverr_browse_categories",
        "category": cat,
        "steps": steps,
        "assertions": [
            "Category header or breadcrumb matches selected category.",
            "At least one gig card is present.",
            "URL contains the category slug."
        ]
    }

_TASK_GENERATORS: Dict[FIVERR_TASK_TYPES, Callable[[dict], dict]] = {
    "fiverr_search_gig": fiverr_search_gig,
    "fiverr_filter_category": fiverr_filter_category,
    "fiverr_filter_price": fiverr_filter_price,
    "fiverr_filter_delivery_time": fiverr_filter_delivery_time,
    "fiverr_filter_seller_level": fiverr_filter_seller_level,
    "fiverr_filter_language": fiverr_filter_language,
    "fiverr_sort_results": fiverr_sort_results,
    "fiverr_gig_detail_view": fiverr_gig_detail_view,
    "fiverr_help_center_topic": fiverr_help_center_topic,
    "fiverr_signup_form_validation": fiverr_signup_form_validation,
    "fiverr_login_form_validation": fiverr_login_form_validation,
    "fiverr_browse_categories": fiverr_browse_categories,
}

def generate_fiverr_task(task_type: FIVERR_TASK_TYPES, payload: dict) -> dict:
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
    items = list(FIVERR_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_fiverr_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)