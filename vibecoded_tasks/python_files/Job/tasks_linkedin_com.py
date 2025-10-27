import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

LINKEDIN_TASK_TYPES = Literal[
    "linkedin_browse_topic",
    "linkedin_browse_category",
    "linkedin_explore_editors_pick",
    "linkedin_navigate_site_section",
    "linkedin_footer_legal_link",
    "linkedin_language_change",
    "linkedin_signup_email",
    "linkedin_signup_google",
    "linkedin_signup_form_validation",
    "linkedin_signin_navigation",
    "linkedin_app_promotion_open",
    "linkedin_app_promotion_dismiss",
    "linkedin_accessibility_skip",
    "linkedin_browse_people_directory",
    "linkedin_browse_learning",
    "linkedin_browse_jobs",
    "linkedin_browse_games",
    "linkedin_get_app_page",
]

LINKEDIN_SAMPLING_CONFIG: Dict[LINKEDIN_TASK_TYPES, int] = {
    "linkedin_browse_topic": 10,
    "linkedin_browse_category": 10,
    "linkedin_explore_editors_pick": 10,
    "linkedin_navigate_site_section": 10,
    "linkedin_footer_legal_link": 10,
    "linkedin_language_change": 10,
    "linkedin_signup_email": 10,
    "linkedin_signup_google": 10,
    "linkedin_signup_form_validation": 10,
    "linkedin_signin_navigation": 10,
    "linkedin_app_promotion_open": 10,
    "linkedin_app_promotion_dismiss": 10,
    "linkedin_accessibility_skip": 10,
    "linkedin_browse_people_directory": 10,
    "linkedin_browse_learning": 10,
    "linkedin_browse_jobs": 10,
    "linkedin_browse_games": 10,
    "linkedin_get_app_page": 10,
}

# 20+ topics, editors picks, categories, legal links, site sections, languages, etc.
TOPICS = [
    "Tips for Managing Stressors with Mental Toughness",
    "How to Navigate Difficult Conversations for Personal Growth",
    "Time Management Strategies for Busy Professionals",
    "Building a Personal Brand on LinkedIn",
    "Networking Remotely: Best Practices",
    "Effective Resume Writing",
    "Interview Preparation Tips",
    "Remote Work Productivity Hacks",
    "Emotional Intelligence at Work",
    "Career Change Guidance",
    "Negotiation Skills for Professionals",
    "Diversity and Inclusion in the Workplace",
    "Public Speaking Confidence",
    "Mentorship and Coaching",
    "Work-Life Balance Techniques",
    "Leadership Development",
    "Entrepreneurship Essentials",
    "Personal Finance for Employees",
    "Job Search Strategies",
    "Dealing with Burnout",
    "Managing Team Conflict",
    "Imposter Syndrome Solutions",
    "Digital Transformation Trends",
    "Sustainable Business Practices",
    "Women in Leadership",
]

EDITORS_PICKS = [
    "Career Advancement Tips",
    "Workday Management Tips",
    "AI Trends and Innovations",
    "Leadership in Uncertain Times",
    "Remote Team Collaboration",
    "Effective Feedback Techniques",
    "Building Resilience",
    "Inclusive Leadership",
    "Digital Marketing Essentials",
    "Emerging Tech Insights",
    "Personal Branding for Executives",
    "Workplace Wellness",
    "Productivity Tools",
    "Job Interview Q&A",
    "Salary Negotiation",
    "Global Business Trends",
    "Emotional Intelligence",
    "Diversity Hiring",
    "Hybrid Work Best Practices",
    "Professional Networking",
    "Upskilling in Tech",
    "Mentorship Success Stories",
    "Entrepreneurial Mindset",
    "Women in Tech",
    "Sustainability in Business",
]

CATEGORIES = [
    "Business Strategy",
    "Artificial Intelligence",
    "Career",
    "Marketing",
    "Technology",
    "Finance",
    "Sales",
    "Healthcare",
    "Education",
    "Operations",
    "Entrepreneurship",
    "Leadership",
    "Human Resources",
    "Product Management",
    "Customer Service",
    "Legal",
    "Project Management",
    "Design",
    "Data Science",
    "Supply Chain",
    "Real Estate",
    "Retail",
    "Energy",
    "Consulting",
    "Government",
]

LEGAL_LINKS = [
    "About",
    "Accessibility",
    "User Agreement",
    "Privacy Policy",
    "Your California Privacy Choices",
    "Cookie Policy",
    "Copyright Policy",
    "Brand Policy",
    "Guest Controls",
    "Community Guidelines",
    "Terms of Service",
    "Security",
    "Sitemap",
    "Ad Choices",
    "Help Center",
    "Careers",
    "Developers",
    "Press",
    "Contact Sales",
    "Mobile",
    "Business Services",
    "Marketing Solutions",
    "Advertising",
    "Talent Solutions",
]

SITE_SECTIONS = [
    "Top Content",
    "People",
    "Learning",
    "Jobs",
    "Games",
    "Get the app",
    "Join now",
    "Sign in",
    "Home",
    "My Network",
    "Messaging",
    "Notifications",
    "Work",
    "Post a job",
    "Groups",
    "Events",
    "Salary",
    "Interview Prep",
    "Insights",
    "Settings",
    "Help",
    "Company Pages",
    "News",
    "Products",
]

LANGUAGES = [
    "English",
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese",
    "Dutch",
    "Russian",
    "Chinese (Simplified)",
    "Chinese (Traditional)",
    "Japanese",
    "Korean",
    "Turkish",
    "Arabic",
    "Polish",
    "Swedish",
    "Danish",
    "Norwegian",
    "Finnish",
    "Czech",
    "Hungarian",
    "Greek",
    "Indonesian",
    "Thai",
    "Vietnamese",
]

EMAIL_DOMAINS = [
    "example.com", "mail.com", "testmail.com", "sample.org", "demo.net", "myemail.org", "fakemail.com", "userdomain.com", "mailinator.com", "tempmail.com",
    "test.org", "email.com", "mailbox.org", "webmail.com", "mailhub.com", "inbox.com", "protonmail.com", "fastmail.com", "outlook.com", "gmail.com",
    "yahoo.com", "icloud.com", "zoho.com", "gmx.com", "yandex.com"
]

PASSWORDS_VALID = [
    "Password123", "Linkedin2025", "Welcome2024", "CareerTips1", "WorkLife22", "StrongPass6", "MyPassw0rd", "TestAcc88", "SecurePwd7", "Qwertyui9",
    "Professional2", "GrowthMind3", "SkillSet44", "JobReady5", "NetWork6", "LearnFast7", "ChangeNow8", "PromoUser9", "SignUp2025", "UserTest10",
    "AlphaBeta1", "GammaDelta2", "SigmaTheta3", "OmegaZeta4", "BetaAlpha5"
]

PASSWORDS_INVALID = [
    "12345", "abc", "pass", "qwerty", "letmein", "test", "password", "111111", "abc123", "short", "pw", "12", "xy", "a", "b", "c", "d", "e", "f", "g",
    "h", "i", "j", "k", "l"
]

# Helper for instruction
def _instr(steps: list[str]) -> dict:
    return get_instruction("LinkedIn", steps).model_dump()

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, app promotion) if present.",
        "Do not sign in or submit any sensitive information unless instructed.",
    ]

def linkedin_browse_topic(_: dict) -> dict:
    topic = random.choice(TOPICS)
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        "Scroll to the section 'What topics do you want to explore?'.",
        f"Click the link labeled '{topic}'.",
        "Wait for the topic detail page to load.",
        f"Verify the page contains the topic title '{topic}'.",
    ]
    return {
        "task_type": "linkedin_browse_topic",
        "topic": topic,
        "steps": steps,
        "assertion": f"Topic page for '{topic}' is displayed and contains relevant content."
    }

def linkedin_browse_category(_: dict) -> dict:
    category = random.choice(CATEGORIES)
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        "Scroll to the 'Topic Categories' section.",
        f"Click the link labeled '{category}'.",
        "Wait for the category feed or page to load.",
        f"Verify that the feed or page contains posts or resources related to '{category}'.",
    ]
    return {
        "task_type": "linkedin_browse_category",
        "category": category,
        "steps": steps,
        "assertion": f"Category page for '{category}' is displayed with relevant posts."
    }

def linkedin_explore_editors_pick(_: dict) -> dict:
    pick = random.choice(EDITORS_PICKS)
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        "Scroll to the 'Editor’s Picks' section.",
        f"Click the link labeled '{pick}'.",
        "Wait for the editor's pick detail page to load.",
        f"Verify the page contains the pick title '{pick}'.",
    ]
    return {
        "task_type": "linkedin_explore_editors_pick",
        "editors_pick": pick,
        "steps": steps,
        "assertion": f"Editor's pick page for '{pick}' is displayed and contains relevant content."
    }

def linkedin_navigate_site_section(_: dict) -> dict:
    section = random.choice(SITE_SECTIONS)
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        f"Locate and click the navigation link labeled '{section}'.",
        f"Wait for the '{section}' section or page to load.",
        f"Verify the URL or page content reflects the '{section}' section.",
    ]
    return {
        "task_type": "linkedin_navigate_site_section",
        "section": section,
        "steps": steps,
        "assertion": f"Navigation to '{section}' is successful and page content matches."
    }

def linkedin_footer_legal_link(_: dict) -> dict:
    link = random.choice(LEGAL_LINKS)
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        "Scroll to the footer section.",
        f"Click the link labeled '{link}'.",
        f"Verify that the '{link}' page or modal opens and contains legal or informational content.",
    ]
    return {
        "task_type": "linkedin_footer_legal_link",
        "footer_link": link,
        "steps": steps,
        "assertion": f"'{link}' legal/informational page is displayed."
    }

def linkedin_language_change(_: dict) -> dict:
    lang = random.choice(LANGUAGES)
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        "Locate and click the 'Language' button in the footer.",
        f"In the language selection dialog, select '{lang}'.",
        "Wait for the page to reload or update to the selected language.",
        f"Verify that the page interface is now displayed in '{lang}'.",
    ]
    return {
        "task_type": "linkedin_language_change",
        "language": lang,
        "steps": steps,
        "assertion": f"Page interface is shown in '{lang}'."
    }

def linkedin_signup_email(_: dict) -> dict:
    email = f"user{random.randint(1000,9999)}@{random.choice(EMAIL_DOMAINS)}"
    password = random.choice(PASSWORDS_VALID)
    steps = [
        "Go to url 'https://www.linkedin.com/pub/dir/+/+?trk=guest_homepage-basic_guest_nav_menu_people'.",
        *_ui_hygiene(),
        "Locate the 'Email' textbox and enter the email address.",
        f"Type '{email}' in the 'Email' field.",
        "Locate the 'Password (6+ characters)' textbox and enter the password.",
        f"Type '{password}' in the 'Password' field.",
        "Click the 'Agree & Join' button.",
        "Wait for the next step or confirmation page to load.",
        "Verify that the account creation step proceeds (e.g., next registration step or welcome message).",
    ]
    return {
        "task_type": "linkedin_signup_email",
        "email": email,
        "password": password,
        "steps": steps,
        "assertion": "Sign-up proceeds to next step or confirmation page after valid input."
    }

def linkedin_signup_google(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.linkedin.com/pub/dir/+/+?trk=guest_homepage-basic_guest_nav_menu_people'.",
        *_ui_hygiene(),
        "Locate and click the 'Continue with google' button.",
        "Wait for the Google authentication window or dialog to appear.",
        "Verify that the Google sign-in interface is displayed (do not enter credentials).",
    ]
    return {
        "task_type": "linkedin_signup_google",
        "steps": steps,
        "assertion": "Google authentication dialog appears after clicking 'Continue with google'."
    }

def linkedin_signup_form_validation(_: dict) -> dict:
    email = f"user{random.randint(1000,9999)}@{random.choice(EMAIL_DOMAINS)}"
    password = random.choice(PASSWORDS_INVALID)
    steps = [
        "Go to url 'https://www.linkedin.com/pub/dir/+/+?trk=guest_homepage-basic_guest_nav_menu_people'.",
        *_ui_hygiene(),
        "Locate the 'Email' textbox and enter the email address.",
        f"Type '{email}' in the 'Email' field.",
        "Locate the 'Password (6+ characters)' textbox and enter an invalid password.",
        f"Type '{password}' in the 'Password' field.",
        "Click the 'Agree & Join' button.",
        "Verify that an error message appears indicating the password is too short or invalid.",
    ]
    return {
        "task_type": "linkedin_signup_form_validation",
        "email": email,
        "invalid_password": password,
        "steps": steps,
        "assertion": "Form displays a validation error for invalid password."
    }

def linkedin_signin_navigation(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.linkedin.com/pub/dir/+/+?trk=guest_homepage-basic_guest_nav_menu_people'.",
        *_ui_hygiene(),
        "Locate and click the 'Sign in' button.",
        "Wait for the sign-in form or page to load.",
        "Verify that the sign-in form is displayed with email and password fields.",
    ]
    return {
        "task_type": "linkedin_signin_navigation",
        "steps": steps,
        "assertion": "Sign-in form is displayed after clicking 'Sign in'."
    }

def linkedin_app_promotion_open(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.linkedin.com/pub/dir/+/+?trk=guest_homepage-basic_guest_nav_menu_people'.",
        *_ui_hygiene(),
        "If an app promotion notice is present, locate and click the 'Open the app' link.",
        "Wait for the app or download page to open (or for a prompt to appear).",
        "Verify that the app page or download prompt is displayed.",
    ]
    return {
        "task_type": "linkedin_app_promotion_open",
        "steps": steps,
        "assertion": "App page or download prompt is displayed after clicking 'Open the app'."
    }

def linkedin_app_promotion_dismiss(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.linkedin.com/pub/dir/+/+?trk=guest_homepage-basic_guest_nav_menu_people'.",
        *_ui_hygiene(),
        "If an app promotion notice is present, locate and click the 'Dismiss' button.",
        "Verify that the app promotion notice is no longer visible.",
    ]
    return {
        "task_type": "linkedin_app_promotion_dismiss",
        "steps": steps,
        "assertion": "App promotion notice is dismissed and not visible."
    }

def linkedin_accessibility_skip(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        "Locate and click the 'Skip to main content' link at the top of the page.",
        "Verify that keyboard focus moves directly to the main content area.",
    ]
    return {
        "task_type": "linkedin_accessibility_skip",
        "steps": steps,
        "assertion": "Focus is set to main content after using 'Skip to main content'."
    }

def linkedin_browse_people_directory(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        "Locate and click the 'People' navigation link.",
        "Wait for the people directory page to load.",
        "Verify that a directory or list of people is displayed.",
    ]
    return {
        "task_type": "linkedin_browse_people_directory",
        "steps": steps,
        "assertion": "People directory page is displayed with a list of people."
    }

def linkedin_browse_learning(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        "Locate and click the 'Learning' navigation link.",
        "Wait for the LinkedIn Learning page to load.",
        "Verify that learning resources or courses are displayed.",
    ]
    return {
        "task_type": "linkedin_browse_learning",
        "steps": steps,
        "assertion": "Learning resources or courses are visible on the Learning page."
    }

def linkedin_browse_jobs(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        "Locate and click the 'Jobs' navigation link.",
        "Wait for the Jobs page to load.",
        "Verify that job postings or search options are displayed.",
    ]
    return {
        "task_type": "linkedin_browse_jobs",
        "steps": steps,
        "assertion": "Jobs page is displayed with job postings or search options."
    }

def linkedin_browse_games(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        "Locate and click the 'Games' navigation link.",
        "Wait for the Games page to load.",
        "Verify that games or related content are displayed.",
    ]
    return {
        "task_type": "linkedin_browse_games",
        "steps": steps,
        "assertion": "Games page is displayed with games or related content."
    }

def linkedin_get_app_page(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.linkedin.com/top-content?trk=guest_homepage-basic_guest_nav_menu_topContent'.",
        *_ui_hygiene(),
        "Locate and click the 'Get the app' navigation link.",
        "Wait for the app download or information page to load.",
        "Verify that the app download or information page is displayed.",
    ]
    return {
        "task_type": "linkedin_get_app_page",
        "steps": steps,
        "assertion": "App download/information page is displayed after navigation."
    }

_TASK_GENERATORS: Dict[LINKEDIN_TASK_TYPES, Callable[[dict], dict]] = {
    "linkedin_browse_topic": linkedin_browse_topic,
    "linkedin_browse_category": linkedin_browse_category,
    "linkedin_explore_editors_pick": linkedin_explore_editors_pick,
    "linkedin_navigate_site_section": linkedin_navigate_site_section,
    "linkedin_footer_legal_link": linkedin_footer_legal_link,
    "linkedin_language_change": linkedin_language_change,
    "linkedin_signup_email": linkedin_signup_email,
    "linkedin_signup_google": linkedin_signup_google,
    "linkedin_signup_form_validation": linkedin_signup_form_validation,
    "linkedin_signin_navigation": linkedin_signin_navigation,
    "linkedin_app_promotion_open": linkedin_app_promotion_open,
    "linkedin_app_promotion_dismiss": linkedin_app_promotion_dismiss,
    "linkedin_accessibility_skip": linkedin_accessibility_skip,
    "linkedin_browse_people_directory": linkedin_browse_people_directory,
    "linkedin_browse_learning": linkedin_browse_learning,
    "linkedin_browse_jobs": linkedin_browse_jobs,
    "linkedin_browse_games": linkedin_browse_games,
    "linkedin_get_app_page": linkedin_get_app_page,
}

def generate_linkedin_task(task_type: LINKEDIN_TASK_TYPES, payload: dict) -> dict:
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
    items = list(LINKEDIN_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_linkedin_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)