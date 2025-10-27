import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

GOODHOUSEKEEPING_TASK_TYPES = Literal[
    "ghk_search_recipe",
    "ghk_search_home_advice",
    "ghk_browse_recipe_category",
    "ghk_browse_home_category",
    "ghk_view_article_from_search",
    "ghk_newsletter_signup_flow",
    "ghk_social_link_navigation",
    "ghk_footer_navigation",
    "ghk_privacy_dialog_interaction",
    "ghk_location_switcher",
    "ghk_play_home_video",
    "ghk_view_recipe_details",
    "ghk_view_product_review",
    "ghk_filter_recipe_by_tag",
    "ghk_filter_home_by_tag",
]

GHK_SAMPLING_CONFIG: Dict[GOODHOUSEKEEPING_TASK_TYPES, int] = {
    "ghk_search_recipe": 10,
    "ghk_search_home_advice": 10,
    "ghk_browse_recipe_category": 10,
    "ghk_browse_home_category": 10,
    "ghk_view_article_from_search": 10,
    "ghk_newsletter_signup_flow": 10,
    "ghk_social_link_navigation": 10,
    "ghk_footer_navigation": 10,
    "ghk_privacy_dialog_interaction": 10,
    "ghk_location_switcher": 10,
    "ghk_play_home_video": 10,
    "ghk_view_recipe_details": 10,
    "ghk_view_product_review": 10,
    "ghk_filter_recipe_by_tag": 10,
    "ghk_filter_home_by_tag": 10,
}

RECIPE_SEARCH_TERMS = [
    "chicken", "pasta", "chocolate", "salad", "cookies", "cake", "vegan", "gluten free", "breakfast", "dinner",
    "soup", "casserole", "brownies", "pancakes", "pizza", "grilled cheese", "smoothie", "shrimp", "quiche", "lasagna",
    "meatballs", "tacos", "muffins", "steak", "pumpkin", "apple", "banana bread", "sandwich", "potato", "rice", "turkey"
][:24]

HOME_ADVICE_SEARCH_TERMS = [
    "cleaning", "organizing", "laundry", "carpet stains", "pet hair", "declutter", "mold", "fridge", "vacuum", "dishwasher",
    "bathroom", "kitchen", "bedroom", "garage", "windows", "dust", "air purifier", "pest control", "fireplace", "paint",
    "furniture", "plants", "storage", "lighting", "curtains", "mattress", "allergies", "humidity", "home security", "energy saving"
][:24]

RECIPE_CATEGORIES = [
    "Healthy Recipes", "Party Recipes", "Cooking Tips", "Inside The Test Kitchen", "Desserts", "Quick Dinners", "Vegetarian",
    "Vegan", "Gluten-Free", "Appetizers", "Breakfast", "Lunch", "Snacks", "Holiday Recipes", "Slow Cooker", "Grilling",
    "Baking", "Soups & Stews", "Salads", "Pasta", "Chicken", "Seafood", "Beef", "Drinks"
][:24]

HOME_CATEGORIES = [
    "Cleaning Advice", "Decorating Ideas", "Home Improvement & Reno", "Gardening & Plants Advice", "Home Organizing Ideas",
    "Pest Control", "Home & Outdoor Products", "Kitchen & Dining Products", "Bathroom", "Bedroom", "Living Room",
    "Garage & Storage", "Laundry Room", "Entryway", "Home Office", "Lighting", "Paint & Wallpaper", "Windows & Curtains",
    "Flooring", "Fireplace", "Furniture", "Smart Home", "Home Security", "Energy Saving"
][:24]

SOCIAL_LINKS = [
    ("tiktok", "https://www.tiktok.com/@goodhousekeeping"),
    ("youtube", "https://www.youtube.com/user/goodhousekeeping"),
    ("facebook", "https://www.facebook.com/goodhousekeeping"),
    ("instagram", "https://www.instagram.com/goodhousekeeping"),
    ("pinterest", "https://www.pinterest.com/goodhousemag/"),
    ("twitter", "https://twitter.com/goodhousemag"),
    ("linkedin", "https://www.linkedin.com/company/good-housekeeping"),
    ("snapchat", "https://www.snapchat.com/add/goodhousemag"),
    ("tumblr", "https://goodhousekeeping.tumblr.com/"),
    ("rss", "https://www.goodhousekeeping.com/rss/all.xml"),
    ("flipboard", "https://flipboard.com/@goodhousemag"),
    ("reddit", "https://www.reddit.com/r/goodhousekeeping"),
    ("whatsapp", "https://wa.me/?text=goodhousekeeping"),
    ("telegram", "https://t.me/goodhousekeeping"),
    ("weibo", "https://weibo.com/goodhousekeeping"),
    ("line", "https://line.me/R/ti/p/@goodhousekeeping"),
    ("vk", "https://vk.com/goodhousekeeping"),
    ("wechat", "https://www.wechat.com/goodhousekeeping"),
    ("quora", "https://www.quora.com/topic/Good-Housekeeping"),
    ("medium", "https://medium.com/@goodhousekeeping"),
    ("flickr", "https://www.flickr.com/photos/goodhousekeeping"),
    ("vimeo", "https://vimeo.com/goodhousekeeping"),
    ("dribbble", "https://dribbble.com/goodhousekeeping"),
    ("behance", "https://www.behance.net/goodhousekeeping"),
][:24]

FOOTER_LINKS = [
    ("About Us", "https://www.goodhousekeeping.com/about-us/"),
    ("Contact Us", "https://www.goodhousekeeping.com/contact-us/"),
    ("Work for Good Housekeeping", "https://www.goodhousekeeping.com/work-for-us/"),
    ("Media Kit", "https://www.goodhousekeeping.com/media-kit/"),
    ("Advertise Online", "https://www.goodhousekeeping.com/advertise/"),
    ("Manage Subscription", "https://w1.buysub.com/pubs/HG/GHK/ManageSubscription.jsp"),
    ("Site Map", "https://www.goodhousekeeping.com/sitemap/"),
    ("Terms of Use", "https://www.goodhousekeeping.com/terms-of-use/"),
    ("Privacy Notice", "https://www.goodhousekeeping.com/privacy-notice/"),
    ("CA Notice at Collection", "https://www.goodhousekeeping.com/ca-notice-at-collection/"),
    ("Your CA Privacy Rights/Shine the Light", "https://www.goodhousekeeping.com/your-ca-privacy-rights/"),
    ("DAA Industry Opt Out", "https://optout.aboutads.info/"),
    ("do-not-sell-link", "https://www.goodhousekeeping.com/do-not-sell-my-info/"),
    ("Newsletter Sign Up Newsletter", "https://www.goodhousekeeping.com/newsletter-signup/"),
    ("Other Hearst Subscriptions", "https://subscribe.hearstmags.com/subscribe/splits/goodhousekeeping/"),
    ("Cookie Preferences", "https://www.goodhousekeeping.com/cookie-preferences/"),
    ("Accessibility", "https://www.goodhousekeeping.com/accessibility/"),
    ("RSS", "https://www.goodhousekeeping.com/rss/"),
    ("Magazine", "https://www.goodhousekeeping.com/magazine/"),
    ("Press Room", "https://www.goodhousekeeping.com/press-room/"),
    ("Editorial Policies", "https://www.goodhousekeeping.com/editorial-policies/"),
    ("Brand Licensing", "https://www.goodhousekeeping.com/brand-licensing/"),
    ("Events", "https://www.goodhousekeeping.com/events/"),
    ("Shop", "https://shop.goodhousekeeping.com/"),
][:24]

RECIPE_TAGS = [
    "gluten free", "vegan", "vegetarian", "dairy free", "low carb", "keto", "paleo", "quick", "easy", "family friendly",
    "holiday", "summer", "winter", "spring", "fall", "comfort food", "healthy", "budget", "one pot", "slow cooker",
    "grilled", "baked", "no bake", "classic"
][:24]

HOME_TAGS = [
    "eco-friendly", "pet-friendly", "budget", "luxury", "DIY", "minimalist", "maximalist", "modern", "traditional",
    "boho", "farmhouse", "industrial", "mid-century", "rustic", "coastal", "urban", "suburban", "small space",
    "large space", "outdoor", "indoor", "kids", "teen", "senior"
][:24]

RECIPE_ARTICLES = [
    "Dirt Pudding Terrarium", "Vanilla Sheet Cake", "Classic Lasagna", "Best-Ever Chocolate Chip Cookies",
    "Easy Chicken Parmesan", "Vegetarian Chili", "Homemade Pizza Dough", "Quick Shrimp Scampi", "Healthy Green Smoothie",
    "Pumpkin Bread", "Apple Crisp", "Breakfast Burritos", "Grilled Cheese Deluxe", "Spaghetti Carbonara", "Lemon Bars",
    "Roast Turkey", "Banana Bread", "Muffin Tin Omelets", "Beef Stew", "Stuffed Peppers", "Chicken Noodle Soup",
    "Eggplant Parmesan", "Fish Tacos", "Berry Parfait"
][:24]

HOME_ARTICLES = [
    "How to Get Rid of Bed Bugs for Good", "50 Fireplace Decor Ideas to Warm Up Your Space",
    "The Best Couch Covers to Protect Your Investment", "How to Clean a Washing Machine",
    "Easy Ways to Declutter Your Home", "Top 10 Air Purifiers", "How to Remove Carpet Stains",
    "Best Vacuum Cleaners of 2025", "Organizing Your Pantry", "DIY Closet Makeover", "Pet Hair Removal Tips",
    "Best Mattresses for Back Pain", "How to Clean Windows", "Energy Saving Tips", "Smart Home Security Basics",
    "Best Indoor Plants", "Bathroom Cleaning Hacks", "Garage Organization Ideas", "How to Paint a Room",
    "Choosing the Right Lighting", "Eco-Friendly Cleaning Products", "Best Kitchen Gadgets", "Home Office Setup Guide",
    "Allergy-Proofing Your Home"
][:24]

PRODUCT_REVIEWS = [
    "The Best Couch Covers to Protect Your Investment", "Top 10 Air Purifiers", "Best Vacuum Cleaners of 2025",
    "Best Mattresses for Back Pain", "Best Kitchen Gadgets", "Best Indoor Plants", "Best Bathroom Cleaners",
    "Best Laundry Detergents", "Best Dishwashers", "Best Refrigerators", "Best Coffee Makers", "Best Blenders",
    "Best Food Processors", "Best Slow Cookers", "Best Grills", "Best Air Fryers", "Best Pressure Cookers",
    "Best Stand Mixers", "Best Toaster Ovens", "Best Cookware Sets", "Best Nonstick Pans", "Best Water Filters",
    "Best Robot Vacuums", "Best Steam Mops"
][:24]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., privacy, cookie, newsletter).",
        "Do not enter any personal or payment information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Good Housekeeping", steps).model_dump()

def ghk_search_recipe(_: dict) -> dict:
    term = random.choice(RECIPE_SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/food-recipes/'.",
        *_ui_hygiene(),
        "Locate the search textbox labeled 'Search'.",
        f"Type '{term}' into the search box.",
        "Click the 'Search' button.",
        "Wait for search results to load.",
        "Verify at least one recipe result is shown.",
        "Assert that the search term appears in the page heading or results.",
    ]
    return {
        "task_type": "ghk_search_recipe",
        "search_term": term,
        "steps": steps,
        "assertion": "At least one recipe result is visible and the search term is reflected in the results.",
        "instruction": _instr(steps),
    }

def ghk_search_home_advice(_: dict) -> dict:
    term = random.choice(HOME_ADVICE_SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/home/'.",
        *_ui_hygiene(),
        "Locate the search textbox labeled 'Search'.",
        f"Type '{term}' into the search box.",
        "Click the 'Search' button.",
        "Wait for search results to load.",
        "Verify at least one article or advice result is shown.",
        "Assert that the search term appears in the page heading or results.",
    ]
    return {
        "task_type": "ghk_search_home_advice",
        "search_term": term,
        "steps": steps,
        "assertion": "At least one home advice result is visible and the search term is reflected in the results.",
        "instruction": _instr(steps),
    }

def ghk_browse_recipe_category(_: dict) -> dict:
    category = random.choice(RECIPE_CATEGORIES)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/food-recipes/'.",
        *_ui_hygiene(),
        f"Locate and click the navigation link labeled '{category}'.",
        "Wait for the category page to load.",
        f"Verify that the page heading or breadcrumb includes '{category}'.",
        "Assert that at least one recipe/article is listed.",
    ]
    return {
        "task_type": "ghk_browse_recipe_category",
        "category": category,
        "steps": steps,
        "assertion": f"Page heading or breadcrumb includes '{category}' and at least one recipe/article is present.",
        "instruction": _instr(steps),
    }

def ghk_browse_home_category(_: dict) -> dict:
    category = random.choice(HOME_CATEGORIES)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/home/'.",
        *_ui_hygiene(),
        f"Locate and click the navigation link labeled '{category}'.",
        "Wait for the category page to load.",
        f"Verify that the page heading or breadcrumb includes '{category}'.",
        "Assert that at least one article or product is listed.",
    ]
    return {
        "task_type": "ghk_browse_home_category",
        "category": category,
        "steps": steps,
        "assertion": f"Page heading or breadcrumb includes '{category}' and at least one article/product is present.",
        "instruction": _instr(steps),
    }

def ghk_view_article_from_search(_: dict) -> dict:
    term = random.choice(RECIPE_SEARCH_TERMS + HOME_ADVICE_SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/'.",
        *_ui_hygiene(),
        "Locate the search textbox labeled 'Search'.",
        f"Type '{term}' into the search box.",
        "Click the 'Search' button.",
        "Wait for search results to load.",
        "Click the first article or recipe link in the results.",
        "Wait for the article/recipe page to load.",
        "Verify the article/recipe title is visible.",
        "Assert that the URL has changed and matches the expected article/recipe pattern.",
    ]
    return {
        "task_type": "ghk_view_article_from_search",
        "search_term": term,
        "steps": steps,
        "assertion": "Article/recipe title is visible and URL matches expected pattern.",
        "instruction": _instr(steps),
    }

def ghk_newsletter_signup_flow(_: dict) -> dict:
    email = f"testuser{random.randint(1000,9999)}@example.com"
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/'.",
        *_ui_hygiene(),
        "Locate and click the 'Newsletter Sign Up Newsletter' link (in header or footer).",
        "Wait for the newsletter signup page to load.",
        "Locate the email input field.",
        f"Enter '{email}' as the email address.",
        "Click the 'Sign Up' or 'Subscribe' button.",
        "Wait for confirmation message or success banner.",
        "Assert that a confirmation or thank you message is displayed.",
        "Negative: Try submitting with an invalid email (e.g., 'abc') and assert an error is shown.",
    ]
    return {
        "task_type": "ghk_newsletter_signup_flow",
        "email": email,
        "steps": steps,
        "assertion": "Confirmation message is displayed for valid email; error message for invalid email.",
        "instruction": _instr(steps),
    }

def ghk_social_link_navigation(_: dict) -> dict:
    label, url = random.choice(SOCIAL_LINKS)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/'.",
        *_ui_hygiene(),
        f"Locate and click the social media link labeled '{label}'.",
        "Switch to the newly opened tab or window.",
        f"Verify that the URL contains '{url.split('//')[1].split('/')[0]}'.",
        f"Assert that the social media page loads successfully (e.g., logo or profile is visible).",
    ]
    return {
        "task_type": "ghk_social_link_navigation",
        "social_label": label,
        "social_url": url,
        "steps": steps,
        "assertion": f"URL contains '{url.split('//')[1].split('/')[0]}' and social profile loads.",
        "instruction": _instr(steps),
    }

def ghk_footer_navigation(_: dict) -> dict:
    label, url = random.choice(FOOTER_LINKS)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/'.",
        *_ui_hygiene(),
        "Scroll to the bottom of the page to view the footer.",
        f"Locate and click the footer link labeled '{label}'.",
        "Wait for the destination page to load.",
        f"Verify that the URL matches or contains '{url}'.",
        f"Assert that the page heading or content matches '{label}'.",
    ]
    return {
        "task_type": "ghk_footer_navigation",
        "footer_label": label,
        "footer_url": url,
        "steps": steps,
        "assertion": f"URL contains '{url}' and page heading/content matches '{label}'.",
        "instruction": _instr(steps),
    }

def ghk_privacy_dialog_interaction(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/'.",
        "If a privacy or cookie dialog appears, verify the dialog is visible.",
        "Locate and click the 'Close' or 'Accept' button.",
        "Assert that the dialog disappears.",
        "Locate and click the 'Privacy Notice' link in the dialog (if present).",
        "Wait for the privacy notice page to load.",
        "Verify the page heading includes 'Privacy Notice'.",
        "Negative: Try to interact with the page while the dialog is open and verify interaction is blocked.",
    ]
    return {
        "task_type": "ghk_privacy_dialog_interaction",
        "steps": steps,
        "assertion": "Dialog can be closed, privacy notice page loads, and dialog blocks interaction when open.",
        "instruction": _instr(steps),
    }

def ghk_location_switcher(_: dict) -> dict:
    locations = [
        "US", "UK", "Canada", "Australia", "India", "Singapore", "South Africa", "New Zealand", "Ireland", "Philippines",
        "Malaysia", "Hong Kong", "UAE", "Germany", "France", "Italy", "Spain", "Mexico", "Brazil", "Japan", "South Korea", "Sweden", "Norway", "Denmark"
    ][:24]
    loc = random.choice(locations)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/'.",
        *_ui_hygiene(),
        "Locate the button labeled 'Current location: US. Click to change location.'",
        "Click the button to open the location selector.",
        f"Select '{loc}' from the list of available regions.",
        "Wait for the site to reload or update.",
        f"Assert that the site now reflects the '{loc}' region (e.g., banner, URL, or content changes).",
        "Negative: Try selecting the same region again and assert that no unnecessary reload occurs.",
    ]
    return {
        "task_type": "ghk_location_switcher",
        "target_location": loc,
        "steps": steps,
        "assertion": f"Site reflects '{loc}' region after selection; no reload on redundant selection.",
        "instruction": _instr(steps),
    }

def ghk_play_home_video(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/home/'.",
        *_ui_hygiene(),
        "Scroll to the 'Home Improvement & Reno' section.",
        "Locate the 'Play Video' button within this section.",
        "Click the 'Play Video' button.",
        "Verify that the embedded video begins playing (e.g., video controls appear, playback starts).",
        "Assert that the video is visible and playing.",
        "Negative: Pause the video and assert playback stops.",
    ]
    return {
        "task_type": "ghk_play_home_video",
        "steps": steps,
        "assertion": "Video plays on click and can be paused.",
        "instruction": _instr(steps),
    }

def ghk_view_recipe_details(_: dict) -> dict:
    article = random.choice(RECIPE_ARTICLES)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/food-recipes/'.",
        *_ui_hygiene(),
        f"Locate and click the recipe/article link labeled '{article}'.",
        "Wait for the recipe detail page to load.",
        "Verify that the recipe title, ingredients, and instructions are visible.",
        "Assert that the page URL contains the article slug.",
    ]
    return {
        "task_type": "ghk_view_recipe_details",
        "article": article,
        "steps": steps,
        "assertion": "Recipe detail page loads with title, ingredients, and instructions.",
        "instruction": _instr(steps),
    }

def ghk_view_product_review(_: dict) -> dict:
    review = random.choice(PRODUCT_REVIEWS)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/home/'.",
        *_ui_hygiene(),
        f"Locate and click the product review link labeled '{review}'.",
        "Wait for the product review page to load.",
        "Verify that the review title and at least one product rating or verdict is visible.",
        "Assert that the URL contains the review slug.",
    ]
    return {
        "task_type": "ghk_view_product_review",
        "review": review,
        "steps": steps,
        "assertion": "Product review page loads with title and product rating/verdict.",
        "instruction": _instr(steps),
    }

def ghk_filter_recipe_by_tag(_: dict) -> dict:
    tag = random.choice(RECIPE_TAGS)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/food-recipes/'.",
        *_ui_hygiene(),
        f"Locate the filter or tag selector and select '{tag}'.",
        "Wait for filtered results to load.",
        f"Verify that the page heading or filter indicator shows '{tag}'.",
        "Assert that at least one recipe/article with the tag is listed.",
        "Negative: Deselect the tag and assert results reset.",
    ]
    return {
        "task_type": "ghk_filter_recipe_by_tag",
        "tag": tag,
        "steps": steps,
        "assertion": f"Filtered results show '{tag}' recipes; results reset when tag is deselected.",
        "instruction": _instr(steps),
    }

def ghk_filter_home_by_tag(_: dict) -> dict:
    tag = random.choice(HOME_TAGS)
    steps = [
        "Go to url 'https://www.goodhousekeeping.com/home/'.",
        *_ui_hygiene(),
        f"Locate the filter or tag selector and select '{tag}'.",
        "Wait for filtered results to load.",
        f"Verify that the page heading or filter indicator shows '{tag}'.",
        "Assert that at least one article/product with the tag is listed.",
        "Negative: Deselect the tag and assert results reset.",
    ]
    return {
        "task_type": "ghk_filter_home_by_tag",
        "tag": tag,
        "steps": steps,
        "assertion": f"Filtered results show '{tag}' articles/products; results reset when tag is deselected.",
        "instruction": _instr(steps),
    }

_TASK_GENERATORS: Dict[GOODHOUSEKEEPING_TASK_TYPES, Callable[[dict], dict]] = {
    "ghk_search_recipe": ghk_search_recipe,
    "ghk_search_home_advice": ghk_search_home_advice,
    "ghk_browse_recipe_category": ghk_browse_recipe_category,
    "ghk_browse_home_category": ghk_browse_home_category,
    "ghk_view_article_from_search": ghk_view_article_from_search,
    "ghk_newsletter_signup_flow": ghk_newsletter_signup_flow,
    "ghk_social_link_navigation": ghk_social_link_navigation,
    "ghk_footer_navigation": ghk_footer_navigation,
    "ghk_privacy_dialog_interaction": ghk_privacy_dialog_interaction,
    "ghk_location_switcher": ghk_location_switcher,
    "ghk_play_home_video": ghk_play_home_video,
    "ghk_view_recipe_details": ghk_view_recipe_details,
    "ghk_view_product_review": ghk_view_product_review,
    "ghk_filter_recipe_by_tag": ghk_filter_recipe_by_tag,
    "ghk_filter_home_by_tag": ghk_filter_home_by_tag,
}

def generate_ghk_task(task_type: GOODHOUSEKEEPING_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(GHK_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_ghk_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)